# -*- coding: utf-8 -*-

"""Attempt to get some stuff out of Fusion 360."""

import adsk.core
import adsk.fusion

import json
import tempfile
import traceback
import uuid
import webbrowser

# from .packages import requests
from .packages import opendesk

# Keep event handler instances in memory, i.e.: so they don't get
# garbage collected.
handlers = []

class HandleExport(adsk.core.CommandEventHandler):
    """Write the model as an `.obj` file + params data to the filesystem and
      then post them to a web API endpoint.
    """

    def export(self, app, ui):
        design = app.activeProduct
        export_manager = design.exportManager

        # with a temp folder ...

        # Grab the params and write out in winnow format to ``config.json``.
        # Export an initial `source.stl` file.

        # resultFilename = tmp_dir + '//' + str(uuid.uuid1())
        # if fileType == 'STL File':
        #     resultFilename = resultFilename + '.stl'
        #     stlOptions = export_manager.createSTLExportOptions(selection, resultFilename)
        #     if stlRefinement == 'Low':
        #         stlOptions.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementLow
        #     elif stlRefinement == 'Medium':
        #         stlOptions.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementMedium
        #     elif stlRefinement == 'High':
        #         stlOptions.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh

        # # Open the exported file.
        # files = {'file': open(resultFilename, 'rb')}


        # For each parameter ...
            # Export a `{{ param }}.stl` file.

        # call the opendesk.export() entry point with the folder

        # and for now pop up a message box saying done!
        raise NotImplementedError

    def notify(self, args):
        ui = None
        try:
            app = adsk.core.Application.get()
            ui = app.userInterface
            with tempfile.TemporaryDirectory() as tmp_dir:
                self.export(app, ui)
        except:
            if ui:
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
        except:
            if ui:
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

        ui.messageBox('Running ...')

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

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def stop(context):
    ui = None
    try:

        # Unpack.
        app = adsk.core.Application.get()
        ui = app.userInterface
        defns = ui.commandDefinitions
        panels = ui.allToolbarPanels

        ui.messageBox('Stopping ...')

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
        del handlers

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
