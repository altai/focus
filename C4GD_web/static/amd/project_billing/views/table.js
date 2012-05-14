define(['backbone', 'underscore', 'text!project_billing/templates/table.html'], function(Backbone, _, table_tmpl){
  function formatDate(date_string){
    if (date_string !== null){ 
      var d = new Date(date_string);
      new_date_string = d.getFullYear()+
        "/"+d.getMonth()+
        "/"+d.getDate()+
        " "+d.getHours()+
        ":"+d.getMinutes()
      return new_date_string
    }else{
      return date_string
    }
  }
  return Backbone.View.extend({
    initialize: function(){
      this.options.router.data.on('reset', this.render, this);
    }
    , dateMap: function(data){
      _.map(data.data.resources, function(x){
        x.created_at = formatDate(x.created_at)
        x.destroyed_at = formatDate(x.destroyed_at)
        return x;
      });
      return data;
    }
    , render: function(){
      var data = this.options.router.data.models[0].attributes;
      
      var filter = this.options.router.filter;
      if (filter)
    	  data = filter(data);
      data = this.dateMap(data)
      this.$el.html(this.template(data));
    }
    , template: _.template(table_tmpl)
  });
});