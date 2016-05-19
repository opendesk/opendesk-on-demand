# -*- coding: utf-8 -*-

"""Given a folder containing:

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

import syslog
syslog.openlog('od-fusion')

import argparse
import copy
import fnmatch
import json
import os.path
import re
import syslog

from collections import defaultdict

AXIS = (
    u'x',
    u'y',
    u'z',
)
MATCH_EXPRESSIONS = {
    'vertex': re.compile('^vertex ', re.U),
}

# XXX Hardcoded for local dev.
EXAMPLES_DIR = os.path.expanduser(
    '~/Development/opendesk-on-demand/examples'
)

def log(*args, **kwargs):
    for arg in args:
        msg = u'{0}'.format(arg)
        syslog.syslog(syslog.LOG_ALERT, msg)
    for k, v in kwargs.items():
        msg = u'{0}: {1}'.format(k, v)
        syslog.syslog(syslog.LOG_ALERT, msg)

def gen_lines(obj_file):
    text = obj_file.read()
    text = text.replace(u'\\\n ', u'')
    for line in text.split(u'\n'):
        line = line.strip()
        if line:
            yield line

class Generator(object):
    """Parse all the data from the target dir. Call the parser.
      Coerce the return value.
    """

    def __init__(self, target_dir):
        self.target_dir = target_dir

    def __call__(self):
        param_files = {}
        target_dir = self.target_dir
        try:
            config_filepath = os.path.join(target_dir, 'config.json')
            source_filepath = os.path.join(target_dir, 'source.stl')
            with open(config_filepath, 'r') as config_file:
                config_json = json.loads(config_file.read())
            with open(source_filepath, 'r', encoding='latin-1') as source_file:
                for key in config_json['parameters']:
                    filename = '{0}.stl'.format(key)
                    param_filepath = os.path.join(target_dir, filename)
                    param_files[key] = open(param_filepath, 'r', encoding='latin-1')
                parser = Parser(source_file, param_files)
                gen_lines = parser(config_json)
                obj_json = {
                    'data': list(gen_lines)
                }
                return obj_json, config_json
        finally:
            for f in param_files.values():
                f.close()

class Parser(object):
    """Given a ``.obj`` file parse it into a flat abstract syntax tree.

      Yields an item generator.
    """

    def __init__(self, source_file, param_files, **kwargs):
        self.lines = gen_lines(source_file)
        self.params = {
            k: list(gen_lines(v)) for k, v in param_files.items()
        }
        self.expr = MATCH_EXPRESSIONS

    def __call__(self, config_data):
        for i, line in enumerate(self.lines):
            if self.expr['vertex'].match(line):
                item = self.parse_geometry(i, line, u'vertex')
                # for each parameter
                for key, alt_lines in self.params.items():
                    # Grab the difference between the default and the
                    # deliberately changed value.
                    c = config_data['parameters'][key]
                    diff_param = c['comparison_value'] - c['initial_value']
                    log('-')
                    log(diff_param=diff_param)
                    # Get the corresponding value.
                    alt_line = alt_lines[i]
                    alt_item = self.parse_geometry(i, alt_line, u'vertex')
                    # For each geometry value
                    for axis in AXIS:
                        geom_value = item['geometry'].get(axis)
                        alt_value = alt_item['geometry'].get(axis)
                        # If it's changed
                        if geom_value != alt_value:
                              if item.get('transformations') is None:
                                  item['transformations'] = {}
                              # Add transformation with `factor = diff_value / diff_param`
                              diff_value = geom_value*100.0 - alt_value*100.0
                              log(diff_value=diff_value)
                              factor = diff_value / diff_param
                              # factor = factor # / 2.0
                              log(factor=factor)

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
            else:
                item = self.pass_through(line)
            yield item

    def parse_geometry(self, i, line, type_):
        """When we encounter a line with geometry values, we want to
          record the type, layer and the x, y, x geometry values.
        """

        parts = line[6:].strip().split()
        return {
            'type': type_,
            'geometry': {
                'x': float(parts[0]),
                'y': float(parts[1]),
                'z': float(parts[2]),
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

def export(name, target_dir):
    """Fusion plugin entry point."""

    # Parse the target_dir to generate the data.
    generate = Generator(target_dir)
    obj_json, config_json = generate()

    # XXX here we would actually post to an endpoint, but for
    # now we write to `./examples/:name`.
    example_dir = os.path.join(EXAMPLES_DIR, name)
    os.system('mkdir "{}"'.format(example_dir))
    obj_filepath = os.path.join(example_dir, 'obj.json')
    config_filepath = os.path.join(example_dir, 'config.json')
    with open(obj_filepath, 'w') as f:
        f.write(json.dumps(obj_json, indent=2))
    with open(config_filepath, 'w') as f:
        f.write(json.dumps(config_json, indent=2))
    return True

def main():
    """Command line entry point."""

    parser = argparse.ArgumentParser()
    parser.add_argument('target_dir')
    args = parser.parse_args()
    generate = Generator(args.target_dir)
    obj_json, config_json = generate()
    return json.dumps([obj_json, config_json], indent=2)

if __name__ == '__main__':
    print(main())
