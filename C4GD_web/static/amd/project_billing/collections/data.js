define(['backbone', 'project_billing/models/datum'], function(Backbone, Datum){
  return Backbone.Collection.extend({
    model: Datum
    , url: window.location.pathname
    , load: function(opts){
      /* 
         Define parameters to pass through fetch as {data: {page: 3}},
         assign caption, calculate and assign total after fetch is done but before rest.
         */
      this.fetch({
        success: function(collection, response){
          console.log(response);
        }
      });
    }
  });
})