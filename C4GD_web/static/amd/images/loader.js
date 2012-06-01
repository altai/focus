define([
  'js!amd/jq.vanilla.js!order', 
  'js!vendors/twitter-bootstrap-aaabe2a/js/bootstrap-transition.js!order', 
  'js!vendors/twitter-bootstrap-aaabe2a/js/bootstrap-collapse.js!order', 
  'js!vendors/twitter-bootstrap-aaabe2a/js/bootstrap-dropdown.js!order',
  'js!vendors/twitter-bootstrap-aaabe2a/js/bootstrap-modal.js!order',
  // 'js!http://bp.yahooapis.com/2.4.21/browserplus-min.js!order',
  'js!/static/vendors/plupload-1.5.4/js/plupload.full.js!order', 
  'js!/static/vendors/plupload-1.5.4/js/jquery.plupload.queue/jquery.plupload.queue.js!order', 
  'js!vendors/underscore-1.3.3/underscore.js!order',
  'js!vendors/backbone-0.9.2/backbone.js!order'
], function(){
  return {
    Backbone: Backbone,
    _: _,
    jQuery: jQuery
  }
})