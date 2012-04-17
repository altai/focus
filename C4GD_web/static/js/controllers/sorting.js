define(['Backbone'], function(Backbone){
  return Backbone.View.extend({
    events: {
      'click ul > li > a': function(e){
        console.log(el)
      }
    },

    is_asc: function(){
      return this.$el.hasClass('asc');
    },

    is_desc: function(){
      return this.$el.hasClass('desc');
    },

    is_none: function(){
      return !(this.is_asc() || this.is_desc());
    }

  });
});
