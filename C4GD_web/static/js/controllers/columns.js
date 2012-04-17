/* default_columns is global variable from the page */
define(['jQuery', 'Backbone', 'URI'], function($, Backbone, URI){
  return Backbone.View.extend({
    uri: URI(window.location.toString()),

    events: {
      'click li.selected-column > a': function(e){
        this.redirect(this.remove(e.currentTarget.attributes[0].nodeValue));
      },
      'click li.spare-column > a': function(e){
        this.redirect(this.add(e.currentTarget.attributes[0].nodeValue));
      }
    },

    normalize: function(){
      if (!this.uri.search().hasOwnProperty('columns')){
        return this.uri.addSearch({ columns: default_columns })
      } else {
        return this.uri;
      }
    },

    add: function(value){
      return this.normalize().addSearch('columns', value);
    },

    remove: function(value){
      return this.normalize().removeSearch('columns', value);
    },

    redirect: function(uri){
      window.location.assign(uri.toString());
    }
  });
});