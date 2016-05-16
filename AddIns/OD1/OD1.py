# -*- coding: utf-8 -*-

"""Attempt to get some stuff out of Fusion 360."""

import adsk.core, adsk.fusion, traceback

# def run(context):
#     ui = None
#     try:
#         app = adsk.core.Application.get()
#         ui  = app.userInterface
#         ui.messageBox('Hello addin')

#     except:
#         if ui:
#             ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

# def stop(context):
#     ui = None
#     try:
#         app = adsk.core.Application.get()
#         ui  = app.userInterface
#         ui.messageBox('Stop addin')

#     except:
#         if ui:
#             ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))












#Author-100kGarages
#Description-Request a fabber quote from 100KGarages.

import adsk.core, traceback
#import shutil
#import os
#import sys

handlers = []

# Define the event handler for 100kGarages command is executed (the "Create RFQ" button is clicked on the dialog).
class Fusion100kGaragesExecutedEventHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        import adsk.fusion
        import tempfile
        import uuid
        import json
        import webbrowser
        from .Packages import requests
        ui = []
        try:
            app = adsk.core.Application.get()
            ui  = app.userInterface

            # Get the inputs.
            inputs = args.command.commandInputs

            fileTypeInput = inputs.itemById('fileType')
            fileType = fileTypeInput.selectedItem.name

            stlRefinementInput = inputs.itemById('stlRefinement')
            stlRefinement = stlRefinementInput.selectedItem.name

            selection = inputs.itemById('selection').selection(0).entity
            if selection.objectType == adsk.fusion.Occurrence.classType():
                selection = selection.component

            # Get the ExportManager from the active design.
            design = app.activeProduct
            exportMgr = design.exportManager

            # Create a temporary directory.
            tempDir = tempfile.mkdtemp()

            # Export the file.
            resultFilename = tempDir + '//' + str(uuid.uuid1())
            if fileType == 'STL File':
                resultFilename = resultFilename + '.stl'
                stlOptions = exportMgr.createSTLExportOptions(selection, resultFilename)
                if stlRefinement == 'Low':
                    stlOptions.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementLow
                elif stlRefinement == 'Medium':
                    stlOptions.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementMedium
                elif stlRefinement == 'High':
                    stlOptions.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh

                exportMgr.execute(stlOptions)
            elif fileType == 'IGES File':
                resultFilename = resultFilename + '.igs'
                igesOptions = exportMgr.createIGESExportOptions(resultFilename, selection)
                exportMgr.execute(igesOptions)
            elif fileType == 'STEP File':
                resultFilename = resultFilename + '.step'
                stepOptions = exportMgr.createSTEPExportOptions(resultFilename, selection)
                exportMgr.execute(stepOptions)

            # Open the exported file.
            files = {'file': open(resultFilename, 'rb')}

            # Post the file to the 100kGarages site.
            try:
                r = requests.post('http://www.100kgarages.com/fusion/upload/index.php', files = files, verify = False )
            except requests.exceptions.ConnectTimeout as e:
                if ui:
                    ui.messageBox('Connection timed out.')
                return
            except requests.exceptions.ConnectionError as e:
                if ui:
                    ui.messageBox('Error connecting to 100kGarages site.')
                return

            if r.status_code != 200:
                if ui:
                    ui.messageBox('Error posting file to 100kGarages site. (Error ' + str(r.status_code) + ')')
                return

            try:
                postResults = json.loads(r.text)
            except:
                if ui:
                    ui.messageBox('Unable to read token from 100kGarages.')
                return

            # Open the webpage.
            try:
                token = postResults.get('token')
            except:
                if ui:
                    ui.messageBox('Unable to extract token from 100kGarages.')
                return

            #if ui:
                    #ui.messageBox(resultFilename)

            url = 'http://www.100kgarages.com/job_post.php?fusion_token=' + token
            webbrowser.open_new(url)
        except:
            # Delete the temp directory and file, if it exists.
            #if os.path.exists(tempDir):
            #    shutil.rmtree(tempDir)

            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


# Define the event handler for when any input changes.
class Fusion100kGaragesInputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        ui = []
        try:
            app = adsk.core.Application.get()
            ui  = app.userInterface

            input = args.input

            # Check to see if the file type has changed and clear the selection
            # re-populate the selection filter.
            if input.id == 'fileType':
                selInput = input.commandInputs.itemById('selection')
                selInput.clearSelectionFilter()

                refinementDropDown = input.commandInputs.itemById('stlRefinement')

                if input.selectedItem.name == 'STL File':
                    selInput.addSelectionFilter('Occurrences')
                    selInput.addSelectionFilter('RootComponents')
                    #selInput.addSelectionFilter('SolidBodies')
                    refinementDropDown.isVisible = True
                else:
                    selInput.addSelectionFilter('Occurrences')
                    selInput.addSelectionFilter('RootComponents')
                    refinementDropDown.isVisible = False
#            elif input.id == 'policyButton':
#                webbrowser.open_new('http://www.100kgarages.com')
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


# Define the event handler for when the command is activated.
class Fusion100kGaragesCommandActivatedHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        ui = []
        try:
            app = adsk.core.Application.get()
            ui  = app.userInterface

            refinementDropDown = args.command.commandInputs.itemById('stlRefinement')
            refinementDropDown.isVisible = False
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


# Define the event handler for when the 100kGarages command is run by the user.
class Fusion100kGaragesCreatedEventHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        ui = []
        try:
            app = adsk.core.Application.get()
            ui  = app.userInterface

            # Connect to the command executed event.
            cmd = args.command
            cmd.isExecutedWhenPreEmpted = False
            onExecute = Fusion100kGaragesExecutedEventHandler()
            cmd.execute.add(onExecute)
            handlers.append(onExecute)

            onInputChanged = Fusion100kGaragesInputChangedHandler()
            cmd.inputChanged.add(onInputChanged)
            handlers.append(onInputChanged)

            # Connect to the command activated event.
            onActivate = Fusion100kGaragesCommandActivatedHandler()
            cmd.activate.add(onActivate)
            handlers.append(onActivate)

            # Define the inputs.
            inputs = cmd.commandInputs

            inputs.addImageCommandInput('image1', '', './/Resources//100KLogo.png')
            #inputs.addTextBoxCommandInput('labelText1', '', '<a href="http://www.100kgarages.com">www.100kGarages.com</a></span>', 1, True)
            inputs.addTextBoxCommandInput('labelText2', '', '<a href="http://www.100kgarages.com">www.100kGarages.com</a></span> is a place for people who have designs, or just ideas for things they want to make, to connect with digital fabricators ("Fabbers") who can help make these ideas become real.', 4, True)


            inputs.addTextBoxCommandInput('labelText3', '', 'Choose the file type and selection to send to 100kGarages for quotes.', 2, True)

            dropDown = inputs.addDropDownCommandInput('fileType', 'File type', adsk.core.DropDownStyles.TextListDropDownStyle)
            dropDown.listItems.add('STEP File', True)
            dropDown.listItems.add('IGES File', False)
            dropDown.listItems.add('STL File', False)

            stldropDown = inputs.addDropDownCommandInput('stlRefinement', 'STL refinement', adsk.core.DropDownStyles.LabeledIconDropDownStyle)
            stldropDown.listItems.add('Low', False)
            stldropDown.listItems.add('Medium', True)
            stldropDown.listItems.add('High', False)

            selection = inputs.addSelectionInput('selection', 'Selection', 'Select the body or component to quote' )
            selection.addSelectionFilter('Occurrences')
            selection.addSelectionFilter('RootComponents')
            #selection.addSelectionFilter('SolidBodies')

            inputs.addTextBoxCommandInput('labelText3', '', '<br />Any information you provide to 100kGarages is subject to <a href="http://www.100kgarages.com/fairPlay.php">100kGarages’s privacy policy and terms</a>, which may differ from those of Fusion 360.', 7, True)
            #inputs.addBoolValueInput('policyButton', 'Privacy policy and terms', False, 'Resources//PolicyButton')

            cmd.commandCategoryName = '100kGaragesQuote2'
            cmd.setDialogInitialSize(500, 300)
            cmd.setDialogMinimumSize(500, 300)

            cmd.okButtonText = 'Get Quotes'

        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


def run(context):
    ui = None

    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface

        if ui.commandDefinitions.itemById('100kGaragesButtonID'):
            ui.commandDefinitions.itemById('100kGaragesButtonID').deleteMe()

        # Get the CommandDefinitions collection.
        cmdDefs = ui.commandDefinitions

        # Create a button command definition for the comamnd button.  This
        # is also used to display the disclaimer dialog.
        tooltip = '<div style=\'font-family:"Calibri";color:#B33D19; padding-top:-20px;\'><span style=\'font-size:20px;\'><b>100kGarages.com</b></span></div>The 100kGarages service enables you to request a quote for manufacturing your part, compare quotes against other fabbers, and get your product made with a seamless process.'
        Fusion100kGaragesButtonDef = cmdDefs.addButtonDefinition('100kGaragesButtonID', 'Get Quotes From 100kGarages.com', tooltip, './/Resources//100kGarages')
        on100kGaragesCreated = Fusion100kGaragesCreatedEventHandler()
        Fusion100kGaragesButtonDef.commandCreated.add(on100kGaragesCreated)
        handlers.append(on100kGaragesCreated)

        # Find the "ADD-INS" panel for the solid and the surface workspaces.
        solidPanel = ui.allToolbarPanels.itemById('SolidMakePanel')
        surfacePanel = ui.allToolbarPanels.itemById('SurfaceMakePanel')

        # Add a button for the "Request Quotes" command into both panels.
        buttonControl = solidPanel.controls.addCommand(Fusion100kGaragesButtonDef, '', False)
        buttonControl = surfacePanel.controls.addCommand(Fusion100kGaragesButtonDef, '', False)
    except:
        pass
        #if ui:
        #    ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def stop(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface

        if ui.commandDefinitions.itemById('100kGaragesButtonID'):
            ui.commandDefinitions.itemById('100kGaragesButtonID').deleteMe()

        # Find the controls in the solid and surface panels and delete them.
        solidPanel = ui.allToolbarPanels.itemById('SolidMakePanel')
        cntrl = solidPanel.controls.itemById('100kGaragesButtonID')
        if cntrl:
            cntrl.deleteMe()

        surfacePanel = ui.allToolbarPanels.itemById('SurfaceMakePanel')
        cntrl = surfacePanel.controls.itemById('100kGaragesButtonID')
        if cntrl:
            cntrl.deleteMe()

    except:
        pass
        #if ui:
        #    ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
