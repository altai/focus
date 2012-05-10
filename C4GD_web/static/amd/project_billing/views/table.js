define(['backbone', 'underscore', 'text!project_billing/templates/table.html'], function(Backbone, _, table_tmpl){
  return Backbone.View.extend({
    initialize: function(){
      this.options.router.data.on('reset', this.render, this);
    }
    , render: function(){
      var data = this.options.router.data.models[0].attributes;
      var filter = this.options.router.filter;
      if (filter)
    	  data = filter(data);
      this.$el.html(this.template(data));
    }
    , template: _.template(table_tmpl)
  });
});