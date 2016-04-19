(function (exports) {
  var add = function (model, value, param_name) {
    var current_value, initial_value;
    initial_value = model.initial_params.get(param_name);
    current_value = model.current_params.get(param_name);
    return value + current_value - initial_value;
  };
  exports.add = add;
})(window); // namespace me
