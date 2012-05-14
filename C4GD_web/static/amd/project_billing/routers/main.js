function formatCost(cost) {
	return cost.toFixed(2);
}

define([
  'backbone'
  , 'm/bootstrap/tab'
  , 'project_billing/views/period'
  , 'project_billing/views/table'
  , 'project_billing/views/graph'
  , 'project_billing/collections/data'
], function(
  Backbone
  , BootstrapTab
  , PeriodView
  , TableView
  , GraphView
  , DataCollection
){
  function formatDateToISO(date){
    new_date = new Date(date.replace(/-/g, '/'));
    return new_date.toISOString();
  }
  return Backbone.Router.extend({
    initialize: function(){
      this.data = new DataCollection();
      this.data.reset();
      this.period_view = new PeriodView({el: $('.period-view'), router: this});
      this.table_view = new TableView({el: $('.table-view'), router: this});
      this.graph_view = new GraphView({el: $('.graph-view'), router: this});
      this.filter = undefined;
    },
    routes: {
      '': 'month'
      , 'today*actions': 'today'
      , 'month*actions': 'month'
      , 'year*actions': 'year'
      , ':period_start/:period_end*actions': 'custom_period'
    }
    , today: function(actions){
      $('.period-view a[href="#today"]').tab('show');
      today = new Date();
      today.setHours(0);
      today.setMinutes(0);
      today.setSeconds(0);
      tomorrow = new Date();
      tomorrow.setHours(24);
      tomorrow.setMinutes(0);
      tomorrow.setSeconds(0);
      this.data.load({
        "period_start": today.toISOString(),
        "period_end": tomorrow.toISOString()
      });
      $('.custom-period-indicator').html('&nbsp;');
    }
    , month: function(actions){
      $('.period-view a[href="#month"]').tab('show');
      this.data.load({"kind": "month"});      
      $('.custom-period-indicator').html('&nbsp;');
    }
    , year: function(actions){
      $('.period-view a[href="#year"]').tab('show');
      this.data.load({"kind": "year"});
      $('.custom-period-indicator').html('&nbsp;');
    }
    , custom_period: function(period_start, period_end, actions){
      $('.period-view a[href="#custom_period"]').tab('show');
      $('.custom-period-indicator').html(period_start+' / '+period_end);
      this.data.load({
        "period_start": formatDateToISO(period_start),
        "period_end": formatDateToISO(period_end)
      })
    }
  });
})