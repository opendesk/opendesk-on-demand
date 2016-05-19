
... header image ...

# Opendesk at Autodesk

> this article explores how we can integrate our configuration and distributed manufacturing systems with Autodesk's collaborative, cloud-based design tools

S:

We're big fans of Autodesk. We use [AutoCAD][] as a primary design tool and [Inventor][] to master finished [designs as parameterised applications][]. However, our current workflow isn't particuarly suitable for external designers to adopt: requiring rigorous adherence to a set of rather fragile mastering conventions.

[AutoCAD]: http://www.autodesk.co.uk/products/autocad/overview
[Inventor]: http://www.autodesk.co.uk/products/inventor/overview
[designs as parameterised applications]: http://thruflo.com/post/82192044143/the-shift-to-post-purchase-manufacture

So we were pretty excited to be invited by Autodesk to their [cloud accelerator programme](http://autodeskcloudaccelerator.com/) in Barcelona this week to explore how we could use their cloud-based [Fusion 360][] platform to build a workflow that would be much more accessible and designed from the ground up to support designer collaboration.

[Fusion 360]: http://www.autodesk.com/products/fusion-360/overview

... fusion grab ...

> Fusion 360TM is the first 3D CAD, CAM, and CAE tool of its kind. It connects your entire product development process in a single cloud-based platform that works on both Mac and PC.

We were pretty confident that Fusion 360 would work as a design and mastering tool. Plus we could see that, just like Inventor, it came with a scriptable environment that we should be able to export files and data from. The key questions for us were whether we could automate the export of:

1. model data and parameterised rules to drive our in-browser customisation engine
2. cutting files for makers to manufacture dynamically configured products

... diagramme ...

We felt that if we could crack these two technical issues, product designers all over the world could master designs in Fusion 360 and then export them for local manufacturing through our [global maker network](https://www.opendesk.cc/open-making/makers).

## 1. Driving In-browser Customisation

### The challenge -- automatically generating compatible data

As you can see from [previous posts](https://www.opendesk.cc/blog/opendesk-on-demand) we've been looking into exposing our Inventor parameterised models for online configuration. Over the weeks leading up to the Autodesk accelerator, we'd developed a working prototype of an export-for-in-browser-customisation system. You can see a demo on [opendesk-on-demand.firebaseapp.com](https://opendesk-on-demand.firebaseapp.com/demo/index.html?example=desk_length) and a [technical note on the implementation approach here](https://github.com/opendesk/opendesk-on-demand/blob/44d708d626ea5e4a733dfa75406c8fa190d1735d/README.md).

To very quickly summarise, this prototype system worked with:

* a 3D model exported from Inventor in `.obj` format
* a manually written `config.json` file that specified the parameters to expose and the geometric transformations to apply to the model when the parameter values changed

Our challenge was thus simple: could we get data out of Fusion 360 that we could coerce into the same format?

### The solution -- more elegant than we could imagine

The first difference we needed to overcome was a format problem: Fusion 360 can't generate `.obj` files directly. However, it can generate ascii `.stl` files, which we could use in just the same way. So we started by porting our existing code from `.obj` to `.stl`, which turned out to be pretty straightforward.

That gave us the model data, which was the first half of the problem. The second half was to access the parameterisation data -- the [logical rules](http://www.autodesk.com/products/fusion-360/blog/user-parameters-patterns-in-fusion-360/) authored in Fusion 360 that control how the model geometry adapts to configurable variables like length, height etc -- and coerce it to the right format. Now, using the Fusion 360 API we could access the rule data. However, once you've exported the geometry out in `.stl` format, you lose the mapping between the rules and the geometric components. I.e.: you know that rule X should be applied to component Y but there's no obvious way of identifying component Y within the `.stl` file -- without resorting to some kind of "are the coordinate values the same" hackery.

We were toying with the idea of writing our own exporter, which would thus be able to know which components were affected by which parameters. However, Adam, one of the Autodesk developers supporting us, came up with a much more elegant solution.

We could manipulate the parameter values inside Fusion 360 and export multiple `.stl` files. A control file with the model's default parameter values and a revised file per-parameter, generated after the value for that parameter had been changed. We could then compare the resulting files and determine which geometry values had changed: literally by comparing the two files line by line.

As it turned out, this technique worked perfectly, allowing us to automate the generation of parameterisation data in the same format that we'd previously been writing manually in our `config.json` file.

The resulting system, which you can play with on [opendesk-on-demand-fusion-360.firebaseapp.com](https://opendesk-on-demand-fusion-360.firebaseapp.com/demo/index.html?example=...) works identically to our initial prototype but, crucially, automates the export of generic Fusion 360 models -- without requiring designers to adhere to any fragile mastering conventions.

## 2. Cutting files for Makers

... context about manual steps using current Inventor plugin ...

... summary of approach to automate DXF output ...

... links to code and example DXF output ...

***

So, in summary, we were able to crack the two key technical issues that would allow us to adopt Fusion 360 and fully automate both the export for in-browser customisation and DXF cutting file generation. The next steps for us are to bring this online, probably first as a authoring tool for up-coming design challenges and then as an ongoing part of our design mastering and publishing workflow.

You can find the source code and examples in the `spike/fusion` branch of [our opendesk-on-demand repo](https://github.com/opendesk/opendesk-on-demand/tree/spike/fusion).
