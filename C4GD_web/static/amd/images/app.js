define([
  'images/jq',
  'images/backbone',
  'images/routers/main'
], function($, Backbone, Router){
  return {
    initialize: function(){
      $(function(){
        new Router;
        Backbone.history.start();
      });
    }
  };
});