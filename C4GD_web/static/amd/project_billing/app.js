define([
  'm/bootstrap/tooltip'
  , 'jquery'
  , 'backbone'
  , 'project_billing/routers/main'], function(foo, $, Backbone, Router){
  return {
    initialize: function(){
      $.ajaxSetup(
        {
          dataFilter: function(data, type){
            if (type == 'json'){
              var obj = $.parseJSON(data)
              if (obj['status'] && (obj['status'] == 'error')){
                $('#error_message_modal .modal-body').html(obj['message']);
                $('#error_message_modal').modal();
                $('#error_message_modal').on('hidden', function () {
                  if (obj.code == 1){
                    window.location = '/logout/';
                  }
                })
              }
            }
          return data
        }
        });
    
      $(function(){
        new Router;
        Backbone.history.start();
      });
    }
  }
});