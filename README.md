
# Opendesk On Demand

This repository contains code and experiments relating to parameterised
configuration and in-browser customisation of Opendesk products.

You can view the published demos at https://opendesk-on-demand.firebaseapp.com/

## Demo

Clone the repo, `cd` into the folder, run e.g.: `python -m SimpleHTTPServer` and open your browser at [localhost:8000/demo.html](http://localhost:8000/demo.html). Play with the controls to see the model adapt. When ready, save and check the console output.

## How it Works

Opendesk products are described using the [winnow][] data format. We use winnow:

1. to describe the "world of possibilities" of a product family and its potential configuration options
2. to describe the specific choices and individual product configurations that customers and makers choose and manufacture (as per [this specification pipeline][])

In-browser customisation must therefore:

* present configuration options that are based on, or at least compatible with, a product's winnow options
* generate choice documents in the winnow format

The way we're proposing to do this is as follows:

1. ensure that any customisable parameters are added to / present in the [product options][]
2. publish dynamic product configurations ([see example][]) that:
   - have a 3D model exported as a `.obj` file that:
     - groups objects by `layers` [#][]
     - can be [loaded in browser][] by [three.js][]
   - have a `config.json` file (see example) that:
     - exposes a subset of the product options as `parameters`
     - specifies the parameter aware [transformation functions][] to apply to object geometry values by `layers` (i.e.: objects on different layers will have different transformation functions applied)
3. write a [cross-language compiler][] that:
   - in `Python`:
     - parses the `.obj` and `config.json#layers` data
     - transforms it into a denormalised abstract-syntax-tree where each object node carries a copy of the transformations that should be applied to it (derived from the layers that the object is on)
   - in `Javascript`:
     - generates new `.obj` code by walking the AST and calculating actual object geometry values for a given configuration by applying the chosen parameter values to the transformation functions carried by any dynamic nodes
     - render the revised `.obj` string using `THREE.OBJLoader.parse`
4. control this using a [controller UI][] built from the `config.json#parameters`

N.b.: in future, we can also consider writing the transformation functions in Python and transpiling to Javascript from Python, in order to support an an alternative 'no-webgl' Python server-side code-generation step that uses [Blender][] to render images.

[winnow]: http://opendesk.github.io/winnow/
[this specification pipeline]: https://github.com/opendesk/winnow/raw/master/docs/product_pipeline_operator.pdf
[product options]: https://github.com/opendesk/winnow/blob/master/docs/product.md
[loaded in browser]: http://threejs.org/examples/webgl_loader_obj.html
[three.js]: http://threejs.org/
[#]: http://docs.mcneel.com/rhino/5/help/en-us/fileio/wavefront_obj_import_export.htm
[see example]: examples/box_height
[transformation functions]: src/lib.coffee
[blender]: https://www.blender.org/manual/
[controller UI]: src/client.coffee
[cross-language compiler]: https://github.com/thejameskyle/the-super-tiny-compiler/blob/master/super-tiny-compiler.js
