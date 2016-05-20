# -*- coding: utf-8 -*-

"""Fusion 360 plugin to export parameterised models."""

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

from .opendesk_on_demand import log
from .opendesk_on_demand import main
from .opendesk_on_demand import generate

FILE_FORMAT = 'stl'
MODEL_UNITS = 'cm'
MESH_REFINEMENT = adsk.fusion.MeshRefinementSettings.MeshRefinementLow

# Keep event handlers in memory, so they don't get garbage collected.
handlers = []

def slugify(s):
    return re.sub(r'[^0-9a-zA-Z]+', '-', s)

def convert_from_model_units(value, target_units):
    """Convert the `value` from the MODEL_UNITS into the `units` provided."""

    return generate.convert_units(value, MODEL_UNITS, target_units)

def convert_to_model_units(value, target_units):
    """Convert the `value` from the MODEL_UNITS into the `units` provided."""

    return generate.convert_units(value, target_units, MODEL_UNITS)

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
    return float(s)

def get_comparison_value(config_item):
    """Given a winnow option-value dict, figure out the value to set
      for the revised STL export.

      It's important to return a small enough difference to avoid
      triggering a different geometry layout, as this causes the
      lines of the exported files to diverge.

      However, it's also fairly important to return some kind of
      difference, as we don't want to get caught out by a lack
      of rounding precision.

      So, we shoot for +-2% of the initial value.
    """

    initial_value = config_item['initial_value']
    value = config_item['value']
    if value.get('type') == 'numeric::range':
        two_percent_less = initial_value * 0.98
        two_percent_more = initial_value * 1.02
        min_ = value['min']
        max_ = value['max']
        if two_percent_more < max_:
            return two_percent_more
        if two_percent_less > min_:
            return two_percent_less
        if initial_value < max_:
            return max_
        return min_
    raise NotImplementedError

class HandleExport(adsk.core.CommandEventHandler):
    """Write the model as an `.stl` file + params data to the filesystem and
      then post them to a web API endpoint.
    """

    def set_param(self, target, name, value):
        for param in target.allParameters:
            if param.name == name:
                param.value = value

    def export(self, design, name, tmp_dir):
        """Unpack the design. Grab the params and format as winnow data.
          Write out ``config.json``. Export an initial ``source.stl`` file.
          For each parameter, export a ``{{ param }}.stl`` file. Call the
          ``opendesk.write_to_filesystem`` entry point with the folder.
        """

        # Unpack the design.
        component = design.rootComponent
        export_manager = design.exportManager
        units_manager = design.unitsManager
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
                param['initial_value'] = convert_from_model_units(item.value, item.unit)
            else:
                param['units'] = MODEL_UNITS
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
        source_opts.meshRefinement = MESH_REFINEMENT
        export_manager.execute(source_opts)

        # For each parameter, export a `{{ param }}.stl` file.
        for item in user_params:
            key = slugify(item.name)
            config_item = params.get(key)
            if not config_item:
                continue
            units = config_item['units']
            raw_initial_value = config_item['initial_value']
            raw_comparison_value = config_item['comparison_value']
            initial_value = convert_to_model_units(raw_initial_value, units)
            comparison_value = convert_to_model_units(raw_comparison_value, units)
            log.warn('units', units)
            log.warn('raw_initial_value', raw_initial_value)
            log.warn('raw_comparison_value', raw_comparison_value)
            log.warn('initial_value', initial_value)
            log.warn('comparison_value', comparison_value)
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
                opts.meshRefinement = MESH_REFINEMENT
                export_manager.execute(opts)
            finally:
                self.set_param(design, item.name, initial_value)

        # Call the opendesk.write_to_filesystem entry point with the folder
        return main.write_to_filesystem(name, tmp_dir, MODEL_UNITS,
                units_manager.defaultLengthUnits, FILE_FORMAT)

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
                    output_dir = self.export(design, name, tmp_dir)
                    log.info(output_dir)
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
                log.warn('ERROR', traceback.format_exc())
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
                log.warn('ERROR', traceback.format_exc())
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def run(context):
    """Add an Opendesk button to the solid and surface panels."""

    ui = None
    try:
        log.info('Running...')
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
            log.warn('ERROR', traceback.format_exc())
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
            log.warn('ERROR', traceback.format_exc())
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
