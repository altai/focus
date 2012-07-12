define(['jquery', 'backbone', 'project_billing/models/datum'], function($, Backbone, Datum){
  return Backbone.Collection.extend({
    model: Datum
    , url: window.location.pathname
    , load: function(opts){
      /* 
         Define parameters to pass through fetch as {data: {page: 3}},
         assign caption, calculate and assign total after fetch is done but before rest.
         */
      $('div.graph-view').html('<div width="100%" height="100%" align="center"><img src="/static/img/ajax-loader.gif"></div>');
      $('div.table-view').html('');
      this.fetch({
    	data: opts,
        success: function(collection, response){
          if (response['data']['resources'].length == 0) {
            $('div.graph-view').html('<div class="alert alert-warning">No items to show</div>');
            $('div.table-view').html('');
          } else {
            this.response = response;
          }
        }
      });
    }
  });
})
