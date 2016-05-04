# Global function to define a namespace.
window.define = (name, constructor) ->
  target = window
  target = target[item] or= {} for item in name.split '.'
  constructor target, window
  return
