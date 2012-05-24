function formatDate(date_string){
  /*
    Return strung representing date in correct format:
    - yyyy/mm/dd HH:mm
    - all values zero-padded
    - null returns as-is
    */
  function zero_pad(value){
    return (value < 10 ? '0' : '') + value
  }
  if (date_string !== null){ 
    var d = new Date(date_string);
    new_date_string = d.getFullYear() +
      "/" + zero_pad(d.getMonth()) +
      "/" + zero_pad(d.getDate()) +
      " " + zero_pad(d.getHours()) +
      ":" + zero_pad(d.getMinutes())
    return new_date_string
  }else{
    return date_string
  }
}
define([
  'underscore', 
  'backbone', 
  'text!project_billing/templates/table.html'
], function(_, Backbone, table_tmpl){
  return Backbone.View.extend({
    initialize: function(){
      this.options.router.data.on('reset', this.render, this);
    }
    , render: function(){
      var data = this.options.router.data.models[0].attributes;
      /* filter can be introduced by othe parts of the app, like diagrams */
      var filter = this.options.router.filter;
      if (filter){
    	data = filter(data);
      } else {
        data.data.cost = _.reduce(
          data.data.resources,
          function(acc, n){
            return acc + n.cost
          },
          0
        )
      }
      this.$el.html(this.template(data));
    }
    , template: _.template(table_tmpl)
  });
});