# fusion360-dxf-export
> Generates an Opendesk dxf drawing from a Fusion360 model.

## How to use

NOTE: Current version only works on Mac.

Clone the "dxf-gen" branch of this repo to your local or download directly by going to this [link](https://github.com/opendesk/opendesk-on-demand/tree/dxf-gen) and clicking the green clone/download button.

Open the downloaded file and navigate to the "{download location}/opendesk-on-demand/Addins/Opendesk-dxf-exporter" directory.

Open the "Opendesk-dxf-exporter.py" file in a text editor and change the path of the variable "FILE_LOC" at the top of the file to somewhere appropriate for your machine and save. This is the location where all the generated files will be saved so make sure you keep the name of the dxf (e.g "/test.dxf") and the file path you choose exists in your finder.

Fire up Fusion360 and open the Scripts and Addins dialog box by pressing the "Addins" button in the "Model" ribbon. Toggle to the addins view and click the green "+" symbol. Navigate to:

{your location}/opendesk-on-demand-dxf-gen/Addins/Opendesk-dxf-exporter/Opendesk-dxf-exporter.py

and click open. The addin is now loaded.

Run the addin on any model that has only single component and any number of separate solid bodies laid out flat on the XY plane. An example of a model ready for export can be foun [here](http://a360.co/1sYVDbz)
