# -*- coding: utf-8 -*-

"""Given a folder containing:

  a. source.stl
  b. config.json (with one top level `parameters` key)
  c. one $param.stl for each `parameter` named in the config

  So, for example if `config.json` has one parameter called `height`
  then the folder should contain `source.stl`, `height.stl` and
  `config.json`.

  Then generate an ``obj.json`` AST / nodelist with transformation functions
  mixed into the nodes and return along with the ``config.json``.
"""

import argparse
import copy
import fnmatch
import json
import re

from collections import defaultdict

AXIS = (
    u'x',
    u'y',
    u'z',
)

MATCH_EXPRESSIONS = {
    'vertex': re.compile('^v ', re.U),
}

def gen_lines(obj_file):
    text = obj_file.read().replace('\\\n ', '')
    for line in text.split('\n'):
        line = line.strip()
        if line:
            yield line

class Generator(object):
    # Parse all the data from the target dir.
    # Call the parser
    # Coerce the return value.

class Parser(object):
    """Given a ``.obj`` file parse it into a flat abstract syntax tree.

      Yields an item generator.
    """

    def __init__(self, source_file, param_files, **kwargs):
        self.lines = gen_lines(source_file)
        self.params = {
            k: gen_lines(v) for k, v in param_files.items()
        }
        self.expr = MATCH_EXPRESSIONS

    def __call__(self):
        for i, line in enumerate(self.lines):
            if self.expr['vertex'].match(line):
                item = self.parse_geometry(i, line, u'vertex')
            else:
                item = self.pass_through(line)
            yield item

    def parse_geometry(self, i, line, type_):
        """When we encounter a line with geometry values, we want to
          record the type, layer and the x, y, x geometry values.
        """

        parts = line.split(' ')
        node = {
            'type': type_,
            'geometry': {
                'x': float(parts[1]),
                'y': float(parts[2]),
                'z': float(parts[3]),
            },
        }
        # For each parameter
            # For each geometry value
                # If it's changed
                    # add transformation with
                    # `factor = diff_value / diff_param`
        raise NotImplementedError

    def pass_through(self, line):
        """When we encounter a line we don't want to amend, we just pass
          it through.
        """

        return {
            'type': u'pass',
            'line': line,
        }

class Denormaliser(object):
    """Given an items generator and a config file, mixes the layer
      definitions in the config file into the relevant items.

      Yields a new item generator.
    """

    def __init__(self, config_file):
        self.config = json.loads(config_file.read())

    def __call__(self, gen_items):
        transformations = self.config.get('transformations', {})
        for item in gen_items:
            if item.has_key('geometry'):
                applicable = defaultdict(dict)
                for key, transformation in transformations.iteritems():
                    match = transformation.get('match', {})
                    bounds = match.get('bounds', {})
                    layers = match.get('layers', [])
                    if layers and item.has_key('layer'):
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
                            if bounds.has_key(axis):
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
                    for property_, instruction in properties.iteritems():
                        applicable[key][property_] = copy.deepcopy(instruction)
                if applicable:
                    item['transformations'] = applicable
            yield item

# data = {
#     'data': list(gen_items)
# }

# finally:
#     args.obj_file.close()
#    args.config_file.close()

def export(self, name, target_dir):
    """Fusion plugin entry point."""

    # Parse the target_dir to generate the data.
    generate = Generator(args.target_dir)
    obj_json, config_json = generate()

    # XXX here we would actually post to an endpoint, but for
    # now we write to `./examples/:name`.
    raise NotImplementedError

def main():
    """Command line entry point."""

    parser = argparse.ArgumentParser()
    parser.add_argument('target_dir')
    args = parser.parse_args()
    generate = Generator(args.target_dir)
    obj_json, config_json = generate()
    return json.dumps([obj_json, config_json], indent=2)

if __name__ == '__main__':
    print main()
