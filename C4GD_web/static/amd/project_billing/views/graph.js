define([
  'backbone'
  , 'underscore'
  , 'jq'
  , 'text!project_billing/templates/graph.html' 
  , 'project_billing/views/chart'
  , 'project_billing/events/collection_ready'
],

function(Backbone, Underscore, $, tmpl_name, ChartView, dispatcher) {
	return Backbone.View.extend({
    initialize: function(){
      this.options.router.data.on('reset', this.render, this);
    }
    , events: {
      'click a.toggle_diagram': 'toggle_diagram',
    }
      , fireDataReload: function(context){
          filterResources = function(resources, condition) {
              var resLen = resources.length;
              var filtered = [];
              var addIt = true;
              var cost = 0.0;
              for ( var i = 0; i < resLen; ++i) {
                  var res = resources[i];
                addIt = condition(res);
                      if (addIt)
                          cost += res.cost;
                  if (addIt)
                      filtered.push(res);
              }
              return {
                  resources : filtered,
                  cost : cost
              };
          } 
          if (context){
              // BY TYPE
            if (context.type == 'type'){
              var rtype = context.legends[context.order];
              if (rtype == "Others") {
                this.options.router.filter = undefined;
              } else {
                this.filters_state['type'] = function(data) {
                  if (context.order != '-1'){
                    return {
                      data : filterResources(data.data.resources,
                        function(res) {
                          return res.rtype == rtype;
                        }),
                      caption : "Resources of " + rtype + " type",
                    };
                  }else{
                    return {
                      data : filterResources(data.data.resources,
                          function(res) {return res})
                    };
                  }
                }
              }
            }
            // BY EXISTENCE
            if (context.type == 'existence'){
              var showDestroyed = context.order;
              this.filters_state['existence'] = function(data) {
                if (context.order != '-1'){
                  return {
                    data : filterResources(data.data.resources, function(res) {
                      var resourceIsAlive = res.destroyed_at == null;
                      if (byExistenceWasReversed){ 
                        return resourceIsAlive ^ !showDestroyed;
                      } else {
                        return resourceIsAlive ^ showDestroyed;
                      }
                    }),
                    caption : (showDestroyed ? "Destroyed resources"
                      : "Present resources"),
                  };
                }else{
                  return {
                    data : filterResources(data.data.resources, function(res) {
                      return res;
                    })
                  }
                }
              }
            }

            if (this.filters_state['type']){
              this.options.router.filter.push(this.filters_state['type']);
            }
            if (this.filters_state['existence']){
              this.options.router.filter.push(this.filters_state['existence']);
            }
            
            this.options.router.table_view.render();
            this.options.router.filter = [];
          }
    }
    , toggle_diagram: function(e){
      var $a = this.$("a.toggle_diagram");
      if ($a.hasClass('hided')){
        $a.html('hide');
        this.$('.toggleable').show();
        $a.removeClass('hided');
      }else{
        $a.html('show diagrams');
        this.$('.toggleable').hide();
        $a.addClass('hided');
      }
      e.preventDefault();
    }
        , render : function() {
          this.filters_state = {'type': undefined, 'existence': undefined};
          var router = this.options.router;
          var models = router.data.models;
          if (models.length < 1) {
            return;
            }
          var resources = models[0].attributes.data.resources;
          var rtypeCost = {};
          var byExistence = [ 0, 0 ];
          for ( var i = resources.length - 1; i >= 0; --i) {
            var res = resources[i];
            var sumCost = rtypeCost[res["rtype"]];
            var cost = parseFloat(res["cost"]);
            byExistence[res["destroyed_at"] == null ? 0 : 1] += cost;
            rtypeCost[res["rtype"]] = cost
              + (sumCost ? parseFloat(sumCost) : 0.0);
          }
          var costs = [], legends = [];
          for ( var rtype in rtypeCost) {
            costs.push(rtypeCost[rtype]);
            legends.push(rtype);
          }          
          
          this.options.el.html(_.template(tmpl_name));
          
          this.byTypeWasreversed = false;
          var chart_by_type = new ChartView({ 
            el: $("#chart_by_type")
            , title: "Bill by type*"
            , values: costs
            , legends: legends
            , type: 'type'
          });

          byExistenceWasReversed = false
          byExistenceLegends = ["Present", "Destroyed"]
          if (byExistence[0] < byExistence[1]){
            byExistence = byExistence.reverse();
            byExistenceLegends = byExistenceLegends.reverse();
            byExistenceWasReversed = true;
          }
          var chart_by_existence = new ChartView({ 
            el: $("#chart_by_existence")
                , title: "Bill by existence*"
            , values: byExistence
            , legends: byExistenceLegends
            , type: 'existence'
          });

          dispatcher.on("dataReload", this.fireDataReload, this)
	  }
	});
});
