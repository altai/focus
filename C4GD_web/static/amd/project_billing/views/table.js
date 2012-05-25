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
  'jq'
  , 'underscore' 
  , 'backbone'
  , 'text!project_billing/templates/table.html'
  , 'm/bootstrap/popover'
], function($, _, Backbone, table_tmpl){
  return Backbone.View.extend({
    initialize: function(){
      this.options.router.data.on('reset', this.render, this);
    }
    , render: function(){
      var data = this.options.router.data.models[0].attributes;
      /* filters can be introduced by othe parts of the app, like diagrams */
      var filters = this.options.router.filter;
      if (filters.length > 0){
        for (var i=0; i<filters.length;i++){
          filter = filters[i];
          data = filters[i](data);
        }
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
      // required to activate popovers after rendered template
      // was installed into HTML page 
      $(".detailed-cost-info").popover();
    }
    , template: _.template(table_tmpl)
  });
});
