# -*- coding: utf-8 -*-

"""Given an ``obj_file`` and a ``config_file``, parse the ``obj_file``
  and mix in / denormalise the layer definitions from the ``config_file``
  to build a list-of-dicts and print it as a JSON string:

      $ python compile.py foo.obj config.json
      # ... writes json to stdout ...

  The output is a flat abstract syntax tree that we can share with the
  compiler client which applies geometry transformations and re-outputs
  as an ``obj_file``.
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

class Parser(object):
    """Given a ``.obj`` file parse it into a flat abstract syntax tree.

      Yields an item generator.
    """

    def __init__(self, obj_file, **kwargs):
        self.lines = gen_lines(obj_file)
        self.expr = MATCH_EXPRESSIONS

    def __call__(self):
        for line in self.lines:
            if self.expr['vertex'].match(line):
                item = self.parse_geometry(line, u'vertex')
            else:
                item = self.pass_through(line)
            yield item

    def parse_geometry(self, line, type_):
        """When we encounter a line with geometry values, we want to
          record the type, layer and the x, y, x geometry values.
        """

        parts = line.split(' ')
        return {
            'type': type_,
            'geometry': {
                'x': float(parts[1]),
                'y': float(parts[2]),
                'z': float(parts[3]),
            },
        }

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

def parse_args():
    """Parse the command line arguments."""

    parser = argparse.ArgumentParser()
    parser.add_argument('obj_file', type=file)
    parser.add_argument('config_file', type=file)
    return parser.parse_args()

def main():
    try:
        args = parse_args()
        parse = Parser(args.obj_file)
        denormalise = Denormaliser(args.config_file)
        gen_items = denormalise(parse())
        data = {
            'data': list(gen_items)
        }
    finally:
        args.obj_file.close()
        args.config_file.close()
    return json.dumps(data, indent=2)

if __name__ == '__main__':
    print main()
