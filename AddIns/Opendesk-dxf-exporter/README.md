# fusion360-dxf-export
> Generates an Opendesk dxf drawing from a Fusion360 model.

## How to use

NOTE: Current version only works on Mac.

Clone the "dxf-gen" branch of this repo to your local or download directly and navigate to the "/Addins/Opendesk-dxf-exporter".

Open the "Opendesk-dxf-exporter.py" file in a text editor and change the path of the variable "FILE_LOC" to somewhere appropriate for your machine and save. Make sure you keep the name of the dxf (e.g "/test.dxf") and the file path you choose exists in your finder.

Fire up Fusion360 and open the Scripts and Addins dialog box by pressing the "Addins" button in the "Model" ribbon. Toggle to the addins view and click the green "+" symbol. Navigate to:

{your location}/opendesk-on-demand-dxf-gen/Addins/Opendesk-dxf-exporter/Opendesk-dxf-exporter.py

and click open. The addin is now loaded.

Run the addin on any model that has only single root compent and any number of separate solid bodies.

Example model - http://a360.co/1sYVDbz