define(
[
  'js!amd/jq.vanilla.js!order', 
  'js!vendors/twitter-bootstrap-aaabe2a/js/bootstrap-transition.js!order',
  'js!vendors/twitter-bootstrap-aaabe2a/js/bootstrap-collapse.js!order', 
  'js!vendors/twitter-bootstrap-aaabe2a/js/bootstrap-dropdown.js!order',
  'js!vendors/twitter-bootstrap-aaabe2a/js/bootstrap-modal.js!order',
  'js!vendors/twitter-bootstrap-aaabe2a/js/bootstrap-tab.js!order',
  'js!vendors/twitter-bootstrap-aaabe2a/js/bootstrap-alert.js!order'], function(){
  var g_data = {}
  g_data[Date.now()] = ''
  $.ajaxSetup(
    {
      dataFilter: function(data, type){
        if (type == 'json'){
          var obj = $.parseJSON(data);
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
      , data: g_data
    }
  );
  return $;
})
