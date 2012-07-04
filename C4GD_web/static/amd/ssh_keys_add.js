curl(curl_cfg, ['jq'], function($) {
	$(document).ready(function() {
    var re = /^\S+\s+\S+\s+(\S*)$/;
    var name_was_edited_by_user = false;
    $('#name').keyup(function(e){
      name_was_edited_by_user = true;
    });
		$('#public_key').keyup(function(e){
      var val = $(this).val();
      var matched = val.match(re);
      if(matched && (!name_was_edited_by_user || $('#name').val().length==0)){ 
        $('#name').val(matched[1].replace(/[^-A-Za-z0-9_]/g, '_')); 
        name_was_edited_by_user = false;
      };
    });
  });
});
