define 'opendesk.on_demand.client', (exports) ->

    String::startsWith = (s) -> @indexOf(s) is 0
    String::endsWith = (s) -> -1 isnt @indexOf s, @length - s.length
    String::contains = (s) -> @indexOf(s) > -1

    ###*
    # Get the value of a querystring
    # @param  {String} field The field to get the value of
    # @param  {String} url   The URL to get the value from (optional)
    # @return {String}       The field value
    ###
    window.getQueryString = (field, url) ->
        href = if url then url else window.location.href
        reg = new RegExp '[?&]' + field + '=([^&#]*)', 'i'
        string = reg.exec href
        if string then string[1] else null

    # We define a single `Model` class with a set of required attributes.
    class Model extends Backbone.Model
        defaults:
            parameters: null
            obj_as_ast: null
            # choice_doc
            # initial_choice_doc
            # obj_string

        validate: (attrs, options) ->
            for key of @defaults
                if not attrs[key]?
                    return "The model must have `#{ key }`."

    # The `ControlsView` renders a form with inputs for each parameter
    # and atomically updates the choice doc when the value of any of those
    # inputs change through user input.
    class ControlsView extends Backbone.View
        template: Handlebars.compile """
            <form class="form">
              {{#each parameters}}
                <div class="form-group">
                  <label for="{{@key}}">
                    {{@key}}:
                    {{#if (lookup ../choice_doc @key)}}
                      {{ lookup ../choice_doc @key }}
                    {{else}}
                      {{ this.initial_value }}
                    {{/if}}
                    {{#if this.units}}
                      {{ this.units }}
                    {{/if}}
                  </label>
                  <input type="range"
                      name="{{@key}}"
                      {{#if (lookup ../choice_doc @key)}}
                        value="{{ lookup ../choice_doc @key }}"
                      {{else}}
                        value="{{ this.initial_value }}"
                      {{/if}}
                      {{#if this.value.min}}
                        min="{{ this.value.min }}"
                      {{/if}}
                      {{#if this.value.max}}
                        max="{{ this.value.max }}"
                      {{/if}}
                  />
                </div>
              {{/each}}
            </form>
        """

        value_types:
            boolean: 'BOOLEAN'
            number: 'NUMBER'
            string: 'STRING'

        initialize: ->
            @listenToOnce @model, 'change:parameters', @render
            @listenTo @model, 'change:choice_doc', @render

        render: ->
            @$el.html @template @model.attributes
            @$form = @$el.find 'form'
            @$inputs = @$form.find 'input, select'
            @$inputs.on 'change', @set_choice_doc
            @set_choice_doc()

        get_input_value: (name) ->
            $input = @$inputs.filter "[name='#{ name }']"
            value = $input.val()
            type_ = $input.attr 'type'
            switch type_
                when 'number', 'range'
                    value = parseInt value
                else
                    throw "Handle input types: `#{ type_ }`."
            value

        ###
        get_value_type: (param) ->
            TYPES = @value_types
            value = param
            if _.isArray value
                value = value[0]
            type_ = typeof value
            if type_ of TYPES
                return TYPES[type_]
            throw "Unknown value type: `#{ type_ }`."
        ###

        set_choice_doc: (args...) =>
            choice_doc = _.clone @model.get 'choice_doc'
            choice_doc ?= {}
            for name, parameter of @model.get 'parameters'
                value = @get_input_value name
                # XXX dont need to deduce type here if we've rendered the
                # right inputs in the template.
                # type_ = @get_value_type parameter
                choice_doc[name] = value
            @model.set 'choice_doc', choice_doc

    # The `ChoiceDocView` view shows the current choice document that
    # would be merged into the product options.
    class ChoiceDocView extends Backbone.View
        template: Handlebars.compile """
            <pre><code class="json">{{ doc }}</code></pre>
        """

        initialize: ->
            @listenTo @model, 'change:choice_doc', @render

        format: (choices) ->
            type: 'choice_document'
            schema: 'https://opendesk.cc/schemata/options.json'
            options: choices

        render: ->
            choice_doc = @format @model.get 'choice_doc'
            tmpl_vars = doc: JSON.stringify choice_doc, null, 2
            @$el.html @template tmpl_vars
            $code = @$el.find 'pre code'
            window.hljs.highlightBlock $code.get 0

    # The `CodeGenerator` contains the core business logic to generate `.obj`
    # code from the `obj_as_ast` node list and the current parameter values.
    class CodeGenerator
        constructor: (@model) ->
            _.extend this, Backbone.Events
            @listenTo @model, 'change:choice_doc', @generate

        generate: ->
            ast = @model.get 'obj_as_ast'
            lines = _.map ast, @line
            obj_string = lines.join '\n'
            @model.set 'obj_string', obj_string

        line: (node, index, ast) =>
            params = @model.get 'parameters'
            choices = @model.get 'choice_doc'
            switch node.type
                when 'pass'
                    line = node.line
                when 'vertex'
                    geom = _.clone node.geometry
                    ts = node.transformations
                    _.each ts, (t) ->
                        _.each t, (sig, key) ->
                            geom_value = geom[key]
                            lib_func = opendesk.on_demand.lib[sig.use]
                            throw "No `geom.#{ geom[key] }`." if not geom_value?
                            throw "No `lib.#{ sig.use }`." if not lib_func?
                            args = _.map sig.args, (a) ->
                                switch
                                    when a is '@' then geom_value
                                    when a.startsWith '$' then a.slice 1
                                    else a
                            geom[key] = lib_func params, choices, args...
                    line = "v #{ geom.x } #{ geom.y } #{ geom.z }"
                else
                    throw "#{ node.type }"
            line

    # The `WebGLViewer` updates the in-browser view of the object whenever
    # the generated `obj_string` code changes.
    class WebGLViewer extends Backbone.View
        defaults: {}

        initialize: ->
            @options = _.defaults @options, @defaults
            # Setup renderer.
            renderer_opts =
                alpha: 1
                antialias: true
                clearColor: 0xffffff
            dims = @dims()
            @renderer = new THREE.WebGLRenderer renderer_opts
            @renderer.setSize dims.width, dims.height
            renderer_el = @renderer.domElement
            @$el.append renderer_el
            # Setup camera.
            camera_args = [
                dims.width / -2   # left
                dims.width / 2    # right
                dims.height / 2   # top
                dims.width / -2   # bottom
                -1000             # near
                1000              # far
            ]
            @camera = new THREE.OrthographicCamera camera_args...
            @camera.position.x = 2;
            @camera.position.y = 2;
            @camera.position.z = 2;
            @camera.fov = 1;
            # Setup controls.
            @controls = new THREE.OrbitControls @camera, renderer_el
            @controls.minPolarAngle = -Infinity;
            @controls.maxPolarAngle = Infinity;
            @controls.minAzimuthAngle = -Infinity;
            @controls.maxAzimuthAngle = Infinity;
            # Setup scene.
            axisHelper = new THREE.AxisHelper 50
            @scene = new THREE.Scene
            @scene.add axisHelper
            # And material.
            material_opts =
                color: 0x99CC99
                linewidth: 2
            @material = new THREE.LineBasicMaterial material_opts
            # Update when the object changes.
            @listenTo @model, 'change:obj_string', @render

        dims: ->
            width: @$el.width()
            height: $(window).height() * 0.8

        render: (model, obj_string) =>
            if @object?
                @scene.remove @object
            for child in @scene.children
                @scene.remove child
            loader = new THREE.OBJLoader
            @object = loader.parse obj_string
            @object.traverse (child) =>
                if child instanceof THREE.Mesh
                    child.material = @material
                    edges_helper = new THREE.EdgesHelper child, 0x000000
                    @scene.add edges_helper
            @scene.add @object

        animate: =>
            if @object?
                @controls.update()
                @renderer.render @scene, @camera
            window.requestAnimationFrame @animate

    # Create the model and components.
    factory = () ->
        model = new Model
        model.on 'invalid', (m, error) -> throw error
        generator = new CodeGenerator model
        controls = new ControlsView el: '#controls', model: model
        choices = new ChoiceDocView el: '#choices', model: model
        viewer = new WebGLViewer el: '#viewer', model: model
        viewer.animate()
        model

    # Bootstrap the initial model data.
    bootstrap = (model, options) ->
        data = {}
        num_performed = 0
        num_requests = 2
        $.getJSON options.config_path, (config) ->
            data.parameters = config.parameters
            num_performed += 1
            complete()
        $.getJSON options.obj_path, (obj) ->
            data.obj_as_ast = obj.data
            num_performed += 1
            complete()
        complete = () ->
            if num_performed is num_requests
                model.set data, validate: true

    # Entry point -- call `main` to setup the client application.
    main = (options) ->
        bootstrap factory(), options

    exports.main = main
