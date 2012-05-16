define([
  'jq'
  , 'backbone'
  , 'project_billing/routers/main'
  , 'm/bootstrap/tooltip'
], function($, Backbone, Router){
  return {
    initialize: function(){
      $(function(){
        $('.change-tenant').change(function(){
          var tenant_id = $('.change-tenant option:selected').val();
          window.location = '/g/billing/' + tenant_id  + '/';
        })

        new Router;
        Backbone.history.start();
      });
    }
  }
});