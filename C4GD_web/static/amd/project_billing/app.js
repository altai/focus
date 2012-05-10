define([
  'm/bootstrap/tooltip'
  , 'jquery'
  , 'backbone'
  , 'project_billing/routers/main'], function(foo, $, Backbone, Router){
  return {
    initialize: function(){
      $(function(){
        new Router;
        Backbone.history.start();
      });
    }
  }
});