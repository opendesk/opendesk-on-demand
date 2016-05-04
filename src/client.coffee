define 'opendesk.on_demand.client', (exports) ->

    String::startsWith = (s) -> @indexOf(s) is 0
    String::endsWith = (s) -> -1 isnt @indexOf s, @length - s.length
    String::contains = (s) -> @indexOf(s) > -1

    # We define a single `Model` class with a set of required attributes.
    class Model extends Backbone.Model
        defaults:
            parameters: null
            initial_choice_doc: null
            choice_doc: null
            obj_as_ast: null
            obj_string: null

        validate: (attrs, options) ->
            for key of @defaults
                if not attrs[key]?
                    return "The model must have `#{ key }`."

    # Hipster views have mustache templates.
    class HipsterView extends Backbone.View
        template: Mustache.to_html

    # The `Controls` view renders a form with inputs for each parameter
    # and atomically updates the choice doc when the value of any of those
    # inputs change through user input.
    class ControlsView extends HipsterView
        tmpl: """
            <div class="panel">
              <ul>
                {{ #parameters }}
                  <li>
                    {{ @key }}: {{ this }}
                  </li>
                {{ /parameters }}
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
            @$el.html @template @tmpl, @model.attributes
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

    # Entry point -- call `main` with initial model, config and parameter
    # `data` to setup the client application.
    main = (data) ->
        model = new Model
        model.on 'invalid', (m, error) -> throw error
        generator = new CodeGenerator model
        controls = new ControlsView el: 'controls', model: model
        model.set data, validate: true

    exports.main = main
