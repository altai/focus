curl(curl_cfg, ['jq'], function($){
  $(document).ready(function(){
    $email = $('form.login input#email');
    $email.focus();
    $('form.login a').click(function(e){
      $a = $(this);
      $a.attr('href', $a.attr('href') + '?email=' + $email.val());
    });
  });
});
