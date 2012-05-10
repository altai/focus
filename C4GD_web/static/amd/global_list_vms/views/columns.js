/* default_columns is global variable from the page */
define(['jquery', 'backbone', 'URI', 'Columns'], function($, Backbone, URI, Columns){
  return Backbone.View.extend({
    uri: URI(window.location.toString()),

    events: {
      'click li.selected-column > a': function(e){
        this.redirect(this.remove(e.currentTarget.attributes[0].nodeValue));
      },
      'click li.spare-column > a': function(e){
        this.redirect(this.add(e.currentTarget.attributes[0].nodeValue));
      },
      'click button.restore-columns': function(){
        this.redirect(this.uri.removeSearch('columns'));
      }
    },

    add: function(value){
      var columns = new Columns();
      return columns.add(value);
    },

    remove: function(value){
      var columns = new Columns();
      return columns.remove(value);
    },

    redirect: function(uri){
      window.location.assign(uri.toString());
    }
  });
});