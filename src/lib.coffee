define 'opendesk.on_demand.lib', (exports) ->

  # XXX an initial geometry function.
  add = (params, choices, initial_geometry_value, param_name, factor) ->

    # If the value is 0, that means the point is on the origin,
    # which means we don't want to move it.
    if initial_geometry_value is 0
        return 0

    # Get the difference in the parameter value.
    initial = params[param_name].initial_value
    current = choices[param_name]
    diff = (current - initial) * factor

    # Either add it to a positive value or subtract it from
    # a negative one.
    if initial_geometry_value < 0
        diff = 0 - diff
    initial_geometry_value + diff

  exports.add = add
