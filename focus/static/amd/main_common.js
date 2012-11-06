curl(curl_cfg, [
  'jq',
], function(){
    $(document).on('submit', 'form', function() {
        $(this).find('.disable-on-submit').attr('disabled', 'disabled');
    })
});
