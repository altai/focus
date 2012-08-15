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
      url = url + '?width=780&height=240&t=' + Date.now() + '&parameters='
      this.$el.html(this.template({
        host: this.host, 
        period: this.period, 
        hosts: this.options.hosts, 
        periods: this.options.periods,
        parameters: this.options.parameters,
        cpu_url: url + 'avg1,avg5,avg15,iowait&title=CPU%20Usage',
        memory_url: url + 'freemem,usedmem&title=Memory%20Usage',
        disk_url: url + 'freespace&title=Disk%20Usage',
        swap_url: url + 'freeswap&title=Swap%20Usage',
      }));
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
