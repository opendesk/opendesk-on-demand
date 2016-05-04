define 'opendesk.on_demand.client', (exports) ->

    String::startsWith = (s) -> @indexOf(s) is 0
    String::endsWith = (s) -> -1 isnt @indexOf s, @length - s.length
    String::contains = (s) -> @indexOf(s) > -1

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

    # The `Controls` view renders a form with inputs for each parameter
    # and atomically updates the choice doc when the value of any of those
    # inputs change through user input.
    class ControlsView extends Backbone.View
        template: Handlebars.compile """
            <div class="panel">
              <ul>
                {{#each parameters}}
                  <li>
                    {{ @key }}: {{ this }}
                  </li>
                {{/each}}
              </ul>
            </div>
        """

        value_types:
            boolean: 'BOOLEAN'
            number: 'NUMBER'
            string: 'STRING'

        initialize: ->
            @listenToOnce @model, 'change:parameters', @render

        render: ->
            @$el.html @template @model.attributes
            @$form = @$el.find 'form'
            @$inputs = @$form.find 'input, select'
            @$inputs.on 'change', @set_choice_doc

        get_input_value: (name) ->
            $input = @$inputs.filter "[attribute='#{ name }']"
            $input.val()

        get_value_type: (param) ->
            TYPES = @value_types
            ###
            if _.isObject param and if 'type' of param
                type_ = param.type_.replace('set::', '')
                if type_.startsWith 'numeric'
                    return TYPES.number
                if type_.contains 'string'
                    return TYPES.string
                if type_.contains 'boolean'
                    return TYPES.boolean
                throw "Unknown object type: `#{ type_ }`."
            ###

            value = param
            if _.isArray value
                value = value[0]
            type_ = typeof value
            if type_ of TYPES
                return TYPES[type_]
            throw "Unknown value type: `#{ type_ }`."

        set_choice_doc: (args...) ->
            choice_doc = _.copy @model.get 'choice_doc'
            for name, parameter of @model.get 'parameters'
                value = @get_input_value name
                # XXX dont need to deduce type *here* if we've rendered the
                # right inputs in the template?
                # type_ = @get_value_type parameter
                choice_doc[name] = value
            @model.set 'choice_doc', choice_doc

    # The `CodeGenerator` contains the core business logic to generate `.obj`
    # code from the `obj_as_ast` node list and the current parameter values.
    class CodeGenerator
        constructor: (@model) ->
            _.extend this, Backbone.Events
            @listenTo @model, 'change:choice_doc', @generate

        generate: ->
            obj_as_ast = @model.get 'obj_as_ast'
            choice_doc = @model.get 'choice_doc'

            # obj_string = ...
            throw 'NotImplemented: do actual code generation.'

            @model.set 'obj_string', obj_string

    # Create the model and components.
    factory = () ->
        model = new Model
        model.on 'invalid', (m, error) -> throw error
        generator = new CodeGenerator model
        controls = new ControlsView el: '#controls', model: model
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
