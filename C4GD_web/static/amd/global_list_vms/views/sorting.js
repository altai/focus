define(['jquery', 'underscore', 'backbone', 'URI'], function($, _, Backbone, URI){
  return Backbone.View.extend({
    events: {
      'click ul > li > a': function(e){
        this.redirect(this.add_order($(e.currentTarget)));
      }
    },

    add_order: function(a){      
      var attr = this.$el.attr('data-attr-name');
      var uri = URI(window.location.toString())
        .removeSearch("asc", attr)
        .removeSearch("desc", attr);
      var direction = a.attr('data-direction');
      if (direction !== undefined){
        uri = uri.addSearch(direction, attr);
      }
      return uri;
    },

    redirect: function(uri){
      window.location.assign(uri.removeSearch('page').toString());
    }

  });
});
