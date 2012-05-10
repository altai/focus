define(['backbone', 'underscore'], function(Backbone, _){
  var object = {};
  _.extend(object, Backbone.Events);
  return object;
})