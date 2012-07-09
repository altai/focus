curl(curl_cfg, [
  'jq'
  , 'm/bootstrap/modal'
], function($){
  $(function(){
    $('a[data-toggle=modal]').click(function(){$(this).modal();$('#' + $(this).attr('data-target')).show()});
  });
});