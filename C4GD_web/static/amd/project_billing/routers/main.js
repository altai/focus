define([
  'backbone'
  , 'project_billing/views/period'
  , 'project_billing/views/table'
  , 'project_billing/views/graph'
  , 'project_billing/collections/data'
], function(
  Backbone
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
    },
    routes: {
      '': 'month'
      , 'today*actions': 'today'
      , 'month*actions': 'month'
      , 'year*actions': 'year'
      , ':start_period/:end_period*actions': 'custom_period'
    }
    , today: function(actions){
      console.log(actions === '')
    }
    , month: function(actions){
      this.data.load()// default is month
    }
    , year: function(actions){
    }
    , custom_period: function(start_period, end_period, actions){
      console.log('custom period', start_period, end_period)
    }
  });
})