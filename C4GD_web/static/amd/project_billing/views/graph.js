define([ 'backbone', 'underscore', 'm/graphael' ],

function(Backbone, Underscore, gRaphael) {
	return Backbone.View.extend({
		initialize : function() {
			this.options.router.data.on('reset', this.render, this);
		},
		render : function() {
			function drawPie(elemId, title, values, legends, onClick) {
				var displayedLegends = [];
				for ( var i = 0; i < legends.length; ++i) {
					displayedLegends.push(legends[i] + " ($"
							+ formatCost(values[i]) + ")");
				}
				var delta = 0;
				for ( var i = values.length - 1; i >= 0; --i)
					delta += values[i];
				delta = delta < 1e-6 ? 1.0 : delta * 0.1 / (values.length + 1);
				for ( var i = values.length - 1; i >= 0; --i)
					values[i] += delta;

				$("#" + elemId).children().remove();
				var r = Raphael(elemId, 460, 380);
				var pie = r.piechart(320, 240, 100, values, {
					legend : displayedLegends,
					legendpos : "west",
				});
				r.text(320, 100, title).attr({
					font : "20px sans-serif"
				});
				pie.click(function() {
					onClick(legends, this.value.order);
				});
				pie.hover(function() {
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
				}, function() {
					this.sector.animate({
						transform : 's1 1 ' + this.cx + ' ' + this.cy
					}, 500, "bounce");
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
				if (res.depth > 0)
					continue;
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
			function filterResources(resources, condition) {
				var resLen = resources.length;
				var filtered = [];
				var addIt = true;
				var cost = 0.0;
				for ( var i = 0; i < resLen; ++i) {
					var res = resources[i];
					if (res.depth == 0) {
						addIt = condition(res);
						if (addIt)
							cost += res.cost;
					}
					if (addIt)
						filtered.push(res);
				}
				return {
					resources : filtered,
					cost : cost
				};
			}

			function filter_type(legends, id) {
				var rtype = legends[id];
				if (rtype == "Others") {
					router.filter = undefined;
				} else {
					router.filter = function(data) {
						return {
							data : filterResources(data.data.resources,
									function(res) {
										return res.rtype == rtype;
									}),
							caption : "Resources of " + rtype + " type",
						};
					}
				}
				router.table_view.render();
			}

			function filter_presence(legends, id) {
				var showDestroyed = id;
				router.filter = function(data) {
					return {
						data : filterResources(data.data.resources, function(
								res) {
							return (res.destroyed_at == null) ^ showDestroyed;
						}),
						caption : (showDestroyed ? "Destroyed resources"
								: "Present resources"),
					};
				}
				router.table_view.render();
			}
			drawPie("chart_by_type", "Bill by type", costs, legends,
					filter_type);
			drawPie("chart_by_existence", "Bill by existence", byExistence, [
					"Present", "Destroyed" ], filter_presence);

		}
	});
});
