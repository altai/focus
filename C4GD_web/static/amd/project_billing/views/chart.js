define([
  'backbone'
  , 'underscore'
  , 'm/graphael'
  , 'jq' 
  , 'project_billing/events/collection_ready'
  , 'text!project_billing/templates/chart.html'
],

function(Backbone, Underscore, gRaphael, $, dispatcher, tmpl_name) {
	return Backbone.View.extend({
		initialize: function() {
            this.render();
		}
        , events: {
            "change select": "callDataReloader",
        }
        , callDataReloader: function(){
            var order = parseInt(this.$el.find("option:selected").attr('value'));
            dispatcher.trigger("dataReload", {
                'legends': this.options.legends
                , 'order': order
                , 'type': this.options.type
                }
            );
            this.$(this.$el.find("svg tspan")).attr('style', 'font-weight : 400;');
            this.$(this.$el.find("svg tspan")[order]).attr('style', 'font-weight : 800;');
            this.piePopup(this.last_selected, order);
            this.last_selected = order;
        }
        , fadeSector: function(index){
            this.pie.series[index].animate({
			    transform : 's1 1 ' + this.cx + ' ' + this.cy
		    }, 100, ">");
        }
        , piePopup: function(last_selected, new_order){
            if(last_selected == new_order){
                /* 
                    When SAME sector was clicked previously and is already active now 
                    Have to fade it down.
                */
                this.fadeSector(new_order);
            }else{
                /* 
                    When ANOTHER sector was clicked previously and is already active now 
                    Have to fade it down.
                */
                if (last_selected != -1){
                    /*
                    There was some selecetd sector. Now another has been clicked.
                    Have to fade previously clicked
                    */
                    for (var i=0;i<this.pie.series.length;i++){
                        if (this.pie.series[i].value && this.pie.series[i].value.order == last_selected){
                            this.fadeSector(i);
                        }                            
                    }                        
                }
            }
        }
		, render: function() {
            var self = this;
            legends = this.options.legends;
            values = this.options.values;
            this.last_selected = -1;
 
            var displayedLegends = [];
			for (var i = 0; i < legends.length; ++i) {
				displayedLegends.push(legends[i] + " ($"
						+ formatCost(values[i]) + ")");
			}
            this.options.el.html(_.template(tmpl_name));
            
			var r = Raphael(this.$('.chart')[0], 460, 380);
			this.pie = r.piechart(320, 240, 100, values, {
				legend : displayedLegends,
				legendpos : "west",
			});
			r.text(320, 100, this.options.title).attr({
				font : "20px sans-serif"
			});
			this.pie.click(function(event) {
                var val = parseInt(self.$el.find("option:selected").attr('value'));
                self.$el.find('option').removeAttr('selected');
                if(val == this.value.order){
                    self.$el.find('option[value="-1"]').attr("selected", "selected");
                }else{
                    self.$el.find('option[value="'+this.value.order+'"]').attr("selected", "selected");
                }
                self.$el.find('option[value="'+this.value.order+'"]').change();
			});
            this.pie.hover(function() {
                if (this.value.order != self.last_selected){
                    this.sector.stop();
                    this.sector.scale(1.1, 1.1, this.cx, this.cy);
                    if (this.label) {
                            this.label[0].stop();
                            this.label[0].attr({
                                    r : 7.5
                            });
                            this.label[1].attr({
                                    "font-weight" : 800
                            });
                    }
                }
            }, function() {
                if (this.value.order != self.last_selected){
                    this.sector.animate({
                            transform : 's1 1 ' + this.cx + ' ' + this.cy
                    }, 500, "bounce");
                }
                if (this.label) {
                        this.label[0].animate({
                                r : 5
                        }, 500, "bounce");
                        this.label[1].attr({
                                "font-weight" : 400
                        });
                }
            });
	    }
	});
});
