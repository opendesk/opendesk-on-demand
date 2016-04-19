window.opendesk_on_demand ?= {}

((exports) ->

  add = (model, value, param_name) ->
      initial = model.initial_params.get param_name
      current = model.current_params.get param_name
      value + current - initial

  exports.add = add

)(window.opendesk_on_demand)
