/* default_columns is global variable from the page */
define(['underscore', 'backbone', 'URI'], function(_, Backbone, URI){
  return Backbone.View.extend({
    uri: URI(window.location.toString()),

    export: function(e, format){
      e.preventDefault();
      window.location.assign(this.uri.search({'export': format}).toString());
    },

    events: {
      'click .export-json': function(e){return this.export(e, 'json')},
      'click .export-csv': function(e){return this.export(e, 'csv')},
      'click .export-xml': function(e){return this.export(e, 'xml')}
    },


  });
});