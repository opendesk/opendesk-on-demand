
# XXX to organise etc.

model:
    initial_params
    current_params

class RenderedView extends Backbone.View
    render: ->
        # rebuild the shape objects using @choices model data
        # pass the shapes to the THREE.Mesh objects
        # etc.

class Controls extends Backbone.View
    render: ->
        # set the `length` etc values from the choice model

class Configurator extends Backbone.View
    initialize: ->
        @model.bind 'change', @render
        @params = @model.get 'params'
        @choice = new Backbone.Model @params.defaults()

class Configuration extends Backbone.Model
    constructor: (@dxf, @params) ->

class DXF extends Backbone.Model
    # ... vector data

class ExposedParameters extends Backbone.Model
    # options sub set
    defaults: ->
        # return the default choices

doit = ->
    el = $('#webgl')
    params = new ExposedParameters data
    dxf = new DXF data
    model = new Configuration dxf, params
    view = new Configurator model, el
