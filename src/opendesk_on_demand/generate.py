# -*- coding: utf-8 -*-

"""Given an ``obj_file`` and a ``config_file``, parse the ``obj_file``
  and mix in / denormalise the layer definitions from the ``config_file``
  to build a list-of-dicts and print it as a JSON string:

      $ python compile.py foo.obj config.json
      # ... writes json to stdout ...

  The output is a flat abstract syntax tree that we can share with the
  compiler client which applies geometry transformations and re-outputs
  as an ``obj_file``.

  ===

  Given a folder containing:

  a. source.stl
  b. config.json (with one top level `parameters` key)
  c. one $param.stl for each `parameter` named in the config

  So, for example if `config.json` has one parameter called `height`
  then the folder should contain:

  - `source.stl`
  - `height.stl`
  - `config.json`

  Then generate an ``obj.json`` AST / nodelist with transformation functions
  mixed into the nodes and return along with the ``config.json``.
"""

import argparse
import collections
import copy
import fnmatch
import json
import os.path
import re

from . import log

AXIS = (
    u'x',
    u'y',
    u'z',
)
FILE_FORMATS = {
    'stl': {
        'match': {
            'vertex': re.compile('^vertex ', re.U),
        }
    },
    'obj': {
        'match': {
            'vertex': re.compile('^v ', re.U),
        }
    },
}
UNIT_CONVERSIONS = (
    ('mm', 'cm', 0.1),
    ('mm', 'in', 0.0393701),
    ('cm', 'mm', 10.0),
    ('cm', 'in', 0.393701),
    ('in', 'cm', 2.54),
    ('in', 'mm', 25.4),
)
VERSION = '0.0.1'

def convert_units(value, from_units, to_units):
    """Generic unit conversion between cm, mm and inches."""

    if from_units == to_units:
        return value
    normalise_inches = lambda x: 'in' if x.startswith('in') else x
    pair = (normalise_inches(from_units), normalise_inches(to_units))
    for item in UNIT_CONVERSIONS:
        if item[:2] == pair:
            return value * item[2]
    raise NotImplementedError('Units not yet supported')

class Generator(object):
    """Parse all the data from the target dir. Call the parser.
      Coerce the return value.
    """

    def __init__(self, target_dir, model_units, geometry_units, extension=None):
        self.target_dir = target_dir
        self.model_units = model_units
        self.geometry_units = geometry_units
        self.extension = self.determine_extension(extension)
        self.file_format = FILE_FORMATS[self.extension]

    def __call__(self):
        param_files = {}
        target_dir = self.target_dir
        try:
            config_name = 'config.json'
            source_name = 'source.{0}'.format(self.extension)
            config_filepath = os.path.join(target_dir, config_name)
            source_filepath = os.path.join(target_dir, source_name)
            with open(config_filepath, 'r') as config_file:
                config_data = json.loads(config_file.read())
            with open(source_filepath, 'r', encoding='latin-1') as source_file:
                for key in config_data['parameters']:
                    filename = '{0}.{1}'.format(key, self.extension)
                    param_filepath = os.path.join(target_dir, filename)
                    if not os.path.exists(param_filepath):
                        continue
                    param_files[key] = open(param_filepath, 'r', encoding='latin-1')
                parser = Parser(config_data, source_file, param_files,
                        self.file_format, self.model_units, self.geometry_units)
                gen_items = parser()
                obj_data = {
                    'data': list(gen_items),
                    'meta': {
                        'format': self.extension,
                        'version': VERSION,
                    }
                }
                return obj_data, config_data
        finally:
            for f in param_files.values():
                f.close()

    def determine_extension(self, extension):
        valid_formats = [extension] if extension else FILE_FORMATS.keys()
        for k in FILE_FORMATS:
            if k not in valid_formats:
                continue
            filename = 'source.{0}'.format(k)
            path = os.path.join(self.target_dir, filename)
            if os.path.exists(path):
                return k
        msg = u'No file matching `source.$ext` where `$ext` is in `{0}`.'
        raise IOError(msg.format(valid_formats))

class Parser(object):
    """Given a ``.obj`` file parse it into a flat abstract syntax tree.

      Yields an item generator.
    """

    def __init__(self, config, source_file, param_files, file_format,
            model_units, geometry_units):
        self.config = config
        self.transformations = config.get('transformations', {})
        self.source_file = source_file
        self.params = {
            k: list(self.gen_lines(v)) for k, v in param_files.items()
        }
        if self.params:
            self.transform = self.apply_dynamic_transformations
        else:
            self.transform = self.apply_manual_transformations
        self.file_format = file_format
        self.model_units = model_units
        self.geometry_units = geometry_units

    def __call__(self):
        gen_lines = self.gen_lines(self.source_file)
        gen_items = self.parse(gen_lines)
        return self.transform(gen_items)

    def gen_lines(self, obj_file):
        """Like ``obj_file.readlines()`` but capable of handling long lines
          that are indented.
        """

        text = obj_file.read().replace(u'\\\n ', u'')
        for line in text.split(u'\n'):
            line = line.strip()
            if line:
                yield line

    def parse(self, gen_lines):
        match_expressions = self.file_format['match'].items()
        for line in gen_lines:
            has_matched = False
            for type_, expr in match_expressions:
                if expr.match(line):
                    item = self.parse_geometry(line, type_)
                    has_matched = True
                    break
            if not has_matched:
                item = self.parse_through(line)
            yield item

    def parse_through(self, line):
        """When we encounter a line we don't want to amend, we just pass
          it through.
        """

        return {
            'type': u'pass',
            'line': line,
        }

    def parse_geometry(self, line, type_):
        """When we encounter a line with geometry values, we want to
          record the type, layer and the x, y, x geometry values.
        """

        # Build the basic geometry item.
        parts = line.strip().split()[1:]
        return {
            'type': type_,
            'geometry': {
                'x': float(parts[0]),
                'y': float(parts[1]),
                'z': float(parts[2]),
            },
        }

    def get_in_geom_units(self, config_item, key):
        value = config_item.get(key)
        units = config_item.get('units', None)
        if units:
            value = convert_units(value, units, self.geometry_units)
        return value

    def apply_dynamic_transformations(self, gen_items):
        """For each dynamic parameter, check the source item against the
          corresponding item in the comparison file. If any of the
          geometry values have changed, then apply the corresponding
          transformation rule.

          In this way we *derive* transformation rules from the exported
          data, rather than having to define them ourselves.
        """

        for i, item in enumerate(gen_items):
            if 'geometry' in item:
                for key, alt_lines in self.params.items():
                    # Grab the difference between the default and the
                    # deliberately changed value.
                    c = self.config['parameters'][key]
                    comp_value = self.get_in_geom_units(c, 'comparison_value')
                    init_value = self.get_in_geom_units(c, 'initial_value')
                    diff_param = comp_value - init_value
                    # Get the corresponding value.
                    alt_line = alt_lines[i]
                    alt_item = self.parse_geometry(alt_line, item['type'])
                    # For each geometry value
                    for axis in AXIS:
                        geom_value = item['geometry'].get(axis)
                        alt_value = alt_item['geometry'].get(axis)
                        # If it's changed
                        if geom_value != alt_value:
                              if item.get('transformations') is None:
                                  item['transformations'] = {}
                              # Add transformation with `factor = diff_value / diff_param`
                              diff_value = alt_value - geom_value
                              factor = diff_value / diff_param
                              if geom_value < 0:
                                  factor = 0 - factor
                              transformation_key = '{0}_by_{1}'.format(axis, key)
                              item['transformations'][transformation_key] = {
                                  axis: {
                                      'use': 'add',
                                      'args': [
                                          '@',
                                          '${0}'.format(key),
                                          factor,
                                      ]
                                  }
                              }
            yield item

    def apply_manual_transformations(self, gen_items):
        """Apply any transformation rules in the ``config.json``."""

        for item in gen_items:
            if 'geometry' in item:
                applicable = collections.defaultdict(dict)
                for key, transformation in self.transformations.items():
                    match = transformation.get('match', {})
                    bounds = match.get('bounds', {})
                    layers = match.get('layers', [])
                    if layers and 'layer' in item:
                        layer = item.get('layer')
                        matches = False
                        for pattern in layers:
                            matches = fnmatch.fnmatchcase(layer, pattern)
                        if not matches:
                            continue
                    if bounds:
                        matches_bounds = True
                        geometry = item.get('geometry')
                        for axis in AXIS:
                            if axis in bounds:
                                min_, max_ = bounds.get(axis)
                                geom_value = geometry.get(axis)
                                if geom_value < min_:
                                    matches_bounds = False
                                if geom_value > max_:
                                    matches_bounds = False
                                if not matches_bounds:
                                    break
                        if not matches_bounds:
                            continue
                    properties = transformation['properties']
                    for property_, instruction in properties.items():
                        applicable[key][property_] = copy.deepcopy(instruction)
                if applicable:
                    item['transformations'] = applicable
            yield item
