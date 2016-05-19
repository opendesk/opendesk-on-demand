# -*- coding: utf-8 -*-

"""Fusion 360 Python3 plugin to export parameterised models."""

import syslog
syslog.openlog('od-fusion')

import adsk.core
import adsk.fusion

import json
import math
import os.path
import re
import tempfile
import traceback
import urllib.parse
import uuid
import webbrowser

# from .packages import requests
from .packages import opendesk
log = opendesk.log

HIGHLY_REFINED = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh

# Keep event handler instances in memory, i.e.: so they don't get
# garbage collected.
handlers = []

def slugify(s):
    return re.sub(r'[^0-9a-zA-Z]+', '-', s)

def convert_cm(value, units):
    """Convert the `value` from cm into the `units` provided."""

    if units == 'mm':
        return value * 10.0
    if units in ['in', 'inch', 'inches']:
        return value / 2.54
    raise NotImplementedError('Units not yet supported')

def is_number(s):
    try:
        n = float(s)
    except ValueError:
        return False
    return True

def as_number(s):
    try:
        a = int(s)
    except ValueError:
        pass
    else:
        if str(a) == s:
            return a
    # try:
    #     b = float(s)
    # except ValueError:
    #     pass
    # else:
    #     if str(b) == s:
    #         return b
    # return complex(s)
    return float(s)

def get_comparison_value(config_item):
    """Given a winnow option-value dict, figure out the value to set
      for the revised STL export.
    """

    initial_value = config_item['initial_value']
    value = config_item['value']
    if value.get('type') == 'numeric::range':
        min_ = value['min']
        max_ = value['max']
        if initial_value < max_:
            return max_
        return min_
    raise NotImplementedError

class HandleExport(adsk.core.CommandEventHandler):
    """Write the model as an `.obj` file + params data to the filesystem and
      then post them to a web API endpoint.
    """

    def set_param(self, target, name, value):
        for param in target.allParameters:
            if param.name == name:
                param.value += 2
                # param.value += 200

    def export(self, design, name, tmp_dir):
        """Unpack the design. Grab the params and format as winnow data.
          Write out ``config.json``. Export an initial ``source.stl`` file.
          For each parameter, export a ``{{ param }}.stl`` file. Call the
          ``opendesk.export`` entry point with the folder.
        """

        # Unpack the design.
        component = design.rootComponent
        export_manager = design.exportManager
        user_params = design.userParameters

        # Grab the params and format as winnow data.
        params = {}
        for item in user_params:
            if not item.comment:
                continue
            qs = dict(urllib.parse.parse_qsl(item.comment))
            export_type = qs.pop('export', None)
            if not export_type:
                continue
            key = slugify(item.name)
            value = qs
            for k, v in value.items():
                if is_number(v):
                    value[k] = as_number(v)
            value['type'] = 'numeric::{0}'.format(export_type)
            param = {
                'name': item.name,
                'value': value,
            }
            if item.unit:
                param['units'] = item.unit
                param['initial_value'] = convert_cm(item.value, item.unit)
            else:
                param['initial_value'] = item.value
            param['comparison_value'] = get_comparison_value(param)
            params[key] = param
        config = {
            'parameters': params,
        }

        # Write out ``config.json``.
        config_json = json.dumps(config, indent=2)
        config_filepath = os.path.join(tmp_dir, 'config.json')
        with open(config_filepath, 'w') as f:
            f.write(config_json)

        # Export an initial `source.stl` file.
        source_stl = os.path.join(tmp_dir, 'source.stl')
        source_opts = export_manager.createSTLExportOptions(component,
                source_stl)
        source_opts.isBinaryFormat = False
        source_opts.meshRefinement = HIGHLY_REFINED
        export_manager.execute(source_opts)

        # For each parameter, export a `{{ param }}.stl` file.
        for item in user_params:
            key = slugify(item.name)
            config_item = params.get(key)
            if not config_item:
                continue
            initial_value = config_item['initial_value']
            comparison_value = config_item['comparison_value']
            try:
                # Cascade the new parameter value to the design and all it's
                # sub components (and their sub components, and ...).
                self.set_param(design, item.name, comparison_value)
                # Export the new geometry as a $param.stl file. This allows
                # us to compare the difference in geometry values and thus
                # infer the linear transformation to apply to points affected
                # by this parameter.
                stl = os.path.join(tmp_dir, '{0}.stl'.format(key))
                opts = export_manager.createSTLExportOptions(component, stl)
                opts.isBinaryFormat = False
                opts.meshRefinement = HIGHLY_REFINED
                export_manager.execute(opts)
            finally:
                pass
                # self.set_param(design, item.name, initial_value)

        # Call the opendesk.export entry point with the folder
        return opendesk.export(name, tmp_dir)

    def notify(self, args):
        ui = None
        try:
            app = adsk.core.Application.get()
            ui = app.userInterface
            product = app.activeProduct
            design = adsk.fusion.Design.cast(product)
            name = slugify(app.activeDocument.name)
            with tempfile.TemporaryDirectory() as tmp_dir:
                try:
                    self.export(design, name, tmp_dir)
                except Exception:
                    raise
                finally:
                    import os
                    os.system(
                        'cp -r "{0}" /Users/thruflo/Desktop/tmp_dir'.format(
                            tmp_dir
                        ),
                    )
            ui.messageBox(u'Export successful!')
        except Exception:
            if ui:
                log('ERROR', traceback.format_exc())
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class HandleCreated(adsk.core.CommandCreatedEventHandler):
    """Jump through hoops to make the button clickable."""

    def notify(self, args):
        ui = None
        try:
            handle_export = HandleExport()
            cmd = args.command
            cmd.commandCategoryName = 'Opendesk'
            cmd.isExecutedWhenPreEmpted = False
            cmd.okButtonText = 'Do eeettt!!'
            cmd.execute.add(handle_export)
            handlers.append(handle_export)
        except Exception:
            if ui:
                log('ERROR', traceback.format_exc())
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def run(context):
    """Add an Opendesk button to the solid and surface panels."""

    ui = None
    try:
        # Unpack.
        app = adsk.core.Application.get()
        ui  = app.userInterface
        defns = ui.commandDefinitions
        panels = ui.allToolbarPanels
        # Clear.
        if defns.itemById('opendesk-btn'):
            defns.itemById('opendesk-btn').deleteMe()
        # Define the command button.
        tooltip = u"""
            <h4>Opendesk</h4>
            <p>La la some message...</p>
        """
        btn = defns.addButtonDefinition('opendesk-btn', u'Do it!', tooltip,
                './/Resources//Opendesk')
        # Wire it up.
        handle_created = HandleCreated()
        btn.commandCreated.add(handle_created)
        # Make sure the handler isn't garbage collected.
        handlers.append(handle_created)
        # Add the button to the toolbar panels.
        solid_panel = panels.itemById('SolidMakePanel')
        surface_panel = panels.itemById('SurfaceMakePanel')
        _ = solid_panel.controls.addCommand(btn, '', False)
        _ = surface_panel.controls.addCommand(btn, '', False)
    except Exception:
        if ui:
            log('ERROR', traceback.format_exc())
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def stop(context):
    ui = None
    try:
        # Unpack.
        app = adsk.core.Application.get()
        ui = app.userInterface
        defns = ui.commandDefinitions
        panels = ui.allToolbarPanels
        # Clear btn.
        btn = defns.itemById('opendesk-btn')
        if btn:
            btn.deleteMe()
        # Find the controls in the solid and surface panels and delete them.
        solid_panel = panels.itemById('SolidMakePanel')
        cntrl = solid_panel.controls.itemById('opendesk-btn')
        if cntrl:
            cntrl.deleteMe()
        surface_panel = panels.itemById('SurfaceMakePanel')
        cntrl = surface_panel.controls.itemById('opendesk-btn')
        if cntrl:
            cntrl.deleteMe()
        # Let the event handlers be garbage collected.
        for item in handlers:
            del item
    except Exception:
        if ui:
            log('ERROR', traceback.format_exc())
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
