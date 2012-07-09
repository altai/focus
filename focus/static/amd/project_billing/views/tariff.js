define([
	'backbone'
	, 'underscore'
	, 'jq'
],
function(Backbone, Underscore, $) {
	 return Backbone.View.extend({
	   initialize: function() {
	     }
	     , events: {
	       'click a.toggle_tariff': 'toggle_tariff',
		 }
	     , toggle_tariff: function(e) {
	       var $a = this.$("a.toggle_tariff");
	       if ($a.hasClass('hided')) {
		 $a.html('hide');
		 this.$('.toggleable').show();
		 $a.removeClass('hided');
	       } else {
		 $a.html('show tariffs');
		 this.$('.toggleable').hide();
		 $a.addClass('hided');
	       }
	       e.preventDefault();
	     }
	   });
       });
