define(['jQuery'], function($){
  return {
    initialize: function(){
      $(document).ready(function(){
        $('form.login input#username').focus();
      });
    }
  }
});