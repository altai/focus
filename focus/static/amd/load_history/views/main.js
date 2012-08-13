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
      }));
      
      this.draw_cpu();
      this.draw_memory();
      this.draw_disk();
      this.draw_swap();
      /*
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
      */
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
    , draw_cpu: function(){
      var r = Raphael('chart-cpu')
      txtattr = { font: "12px sans-serif" };
      r.text(160, 15, "Load Average").attr(txtattr);
      r.linechart(
        10, 10, 300, 200, 
        [this.data[0], this.data[0], this.data[0], this.data[0]], 
        [this.data[1]['avg1'], this.data[1]['avg5'], this.data[1]['avg15'], this.data[1]['iowait']],
        {
          axis: '0 0 1 1',
          nostroke: false,
          colors: ['red', 'green', 'blue', 'yellow']
        }
      );
      var base = 0;
      _.each([['avg1', '1 min', 'red'], 
              ['avg5', '5 min', 'green'], 
              ['avg15', '15 min', 'blue'],
              ['iowait', 'iowait', 'yellow'],], 
             function(x){
               r.rect(base + 40, 220, 10, 10).attr({fill: x[2]})
               r.text(base + 70, 227, x[1])
               base = base + 50
             })
        }
    , draw_memory: function(data){
      var r = Raphael('chart-memory')
      txtattr = { font: "12px sans-serif" };
      r.text(160, 15, "Memory").attr(txtattr);
      r.linechart(
        10, 10, 300, 200, 
        [this.data[0], this.data[0]], 
        [this.data[1]['freemem'], this.data[1]['usedmem']],
        {
          axis: '0 0 1 1',
          nostroke: false,
          colors: ['blue', 'red'],
          shadow: true
        }
      );
      var base = 0;
      _.each([['freemem', 'Free', 'blue'], 
              ['usedmem', 'Used', 'red']], 
             function(x){
               r.rect(base + 40, 220, 10, 10).attr({fill: x[2]})
               r.text(base + 70, 227, x[1])
               base = base + 50
             })
        }
    , draw_disk: function(data){
      var r = Raphael('chart-disk')
      txtattr = { font: "12px sans-serif" };
      r.text(160, 15, "Disk").attr(txtattr);
      r.linechart(
        10, 10, 300, 200, 
        [this.data[0]], 
        [this.data[1]['freespace']],
        {
          axis: '0 0 1 1',
          nostroke: false,
          colors: ['blue'],
          shadow: true
        }
      );
      var base = 0;
      _.each([['freespace', 'Free', 'blue']], 
             function(x){
               r.rect(base + 40, 220, 10, 10).attr({fill: x[2]})
               r.text(base + 70, 227, x[1])
               base = base + 50
             })
    }
    , draw_swap: function(data){
      var r = Raphael('chart-swap')
      txtattr = { font: "12px sans-serif" };
      r.text(160, 15, "Swap").attr(txtattr);
      r.linechart(
        10, 10, 300, 200, 
        [this.data[0]], 
        [this.data[1]['freeswap']],
        {
          axis: '0 0 1 1',
          nostroke: false,
          colors: ['blue'],
          shadow: true
        }
      );
      var base = 0;
      _.each([['freespace', 'Free', 'blue']], 
             function(x){
               r.rect(base + 40, 220, 10, 10).attr({fill: x[2]})
               r.text(base + 70, 227, x[1])
               base = base + 50
             })
    }
  });
});
