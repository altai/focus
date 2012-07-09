curl(curl_cfg, ['jq'], function($){
  $(document).ready(function(){
    $('form.login input#username').focus();
  });
});