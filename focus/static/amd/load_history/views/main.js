define([
  'jq'
  , 'backbone'
  , 'underscore'
  , 'm/graphael'
  , 'text!amd/load_history/templates/main.html'
], function($, Backbone, _, gRaphael, main_tmpl){
  return Backbone.View.extend({
    host: null
    , period: null
    , template: _.template(main_tmpl)
    , data : []
    , initialize: function(){
      this.render()
    }
    , render: function(){
      var self = this;
      this.data = null;
      if (this.host == null & this.options.hosts.length){
        this.host = this.options.hosts[0]
      }
      if (this.period == null & this.options.periods.length){
        this.period = this.options.periods[0]
      }
      var url = this.options.url
        .replace('_host_', this.host)
        .replace('_period_', this.period)
        .replace('?parameters=param1,param2', '')
      if (this.host !== null & this.period !== null){
        $.ajax(url, {
          async: false
          , success: function(data){
            self.data = data;
          }
          , dataType: 'json'});
      }
      this.$el.html(this.template({
        host: this.host, 
        period: this.period, 
        hosts: this.options.hosts, 
        periods: this.options.periods,
        parameters: this.options.parameters,
        data: this.data
      }))
      // nice data to see nice pictures (we have arrays of nulls in data[2][0])
      var x = [], y = [], y2 = [], y3 = [];

      for (var i = 0; i < 1e6; i++) {
        x[i] = i * 10;
        y[i] = (y[i - 1] || 0) + (Math.random() * 7) - 3;
        y2[i] = (y2[i - 1] || 150) + (Math.random() * 7) - 3.5;
        y3[i] = (y3[i - 1] || 300) + (Math.random() * 7) - 4;
      }
      _.each(this.data[1], function(parameter, i){
        console.log()
        var r =  Raphael(self.$('.chart-' + parameter)[0])
        r.linechart(10, 10, 300, 220, x, [y.slice(0, 1e3), y2.slice(0, 1e3), y3.slice(0, 1e3)]).hoverColumn(function () {
          this.set = r.set(
            r.circle(this.x, this.y[0]),
            r.circle(this.x, this.y[1]),
            r.circle(this.x, this.y[2])
          );
        }, function () {
          this.set.remove();
        });
      })
    }
    , events: {
      'change select.hosts': function(){
        this.host = this.$('select.hosts').val()
        this.render()
      }
      , 'click a.foo': function(e){
        e.preventDefault()
        this.period = e.currentTarget.rel
        this.render()
      }
    }
  });
});
