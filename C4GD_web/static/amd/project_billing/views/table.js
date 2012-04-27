define(['backbone', 'underscore', 'text!project_billing/templates/table.html'], function(Backbone, _, table_tmpl){
  return Backbone.View.extend({
    initialize: function(){
      this.options.router.data.on('reset', this.render, this);
    }
    , render: function(){
      this.$el.html(this.template({data: this.options.router.data}))
    }
    , template: _.template(table_tmpl)
  });
});