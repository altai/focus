define([
  'jQuery'
], function($){
  var initialize = function(){
    // required for login, too small for separate app
    $(document).ready(function(){
      $('input#username').focus();
    });
  };
  return {initialize: initialize};
});