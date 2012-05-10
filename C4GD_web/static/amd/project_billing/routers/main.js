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
      this.data.load({"kind": "today"});
    }
    , month: function(actions){
      $('.period-view a[href="#month"]').tab('show');
      this.data.load({"kind": "month"});      
    }
    , year: function(actions){
      $('.period-view a[href="#year"]').tab('show');
      this.data.load({"kind": "year"});
    }
    , custom_period: function(period_start, period_end, actions){
      $('.period-view a[href="#custom_period"]').tab('show');      
      this.data.load({"period_start": period_start, "period_end": period_end});
    }
  });
})