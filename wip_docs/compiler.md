Python:

1. Parse the source DXF into an AST abstract representation
2. Transform that into a published AST that's in the right structure to generate the THREE stuff from

Steps:

- the first AST gets the DXF objects and layers
- the second AST has
  - any pre-processing of static values (e.g.: arc)
  - the DXF values augmented with the layer functions as per
    `'value_type': 'dynamic',` example below

The published AST has nodes with values that are either literal or dynamic where the dynamic values are pulled from the choice doc.

I.e.:

    nodes = [
      {
        'type': 'Shape',
        'nodes': [
          {
            'type': 'MoveTo',
            'value_type': 'literal',
            'value': {
              'x': 12.34,
              'y': 1.456
            ]
          }, {
            'type': 'MoveTo',
            'value_type': 'dynamic',
            'value': {
              'x': {
                'operation': 'od.add',
                'args': [
                  12.34,
                  '$length'
                ]
              },
              'y': '1.456'
            },
            'bind': { // references the choice doc model
              'length': '$ref:dimensions/length'
            }
          }, {
            'type': 'ARC',
            'value_type': 'dynamic',
            'value': {
              'x': {
                'operation': 'add',
                'args': [
                  12.34,
                  '$length'
                ]
              },
              'y': '1.456'
            },
            'bind': { // references the choice doc model
              'length': '$ref:dimensions/length'
            }
          }
        ]
      }
    ]

Javascript:

3. Have the new choice values through data binding etc.
4. Generate the THREE obj from the second AST + the choice values
