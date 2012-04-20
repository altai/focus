define(['Backbone', 'URI', 'jQuery'], function(Backbone, URI, $){
  return Backbone.View.extend({
    events: {
      'click a[data-groupping-value]': function (event){
        var $a = $(event.target);
        var groupping_value = $a.data('groupping-value');
        var uri = URI(window.location.toString())
          .removeSearch('groupby').removeSearch('page');
        if (groupping_value !== ""){
          uri = uri.addSearch('groupby', groupping_value);
        }
        window.location.assign(uri.toString());
      }
    }
  });
});