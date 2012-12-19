function formatCost(cost) {
    'use strict';
    return typeof cost === 'number' ? cost.toFixed(2) : cost.value.toFixed(2);
}

define([
    'jq',
    'backbone',
    'm/bootstrap/tab',
    'project_billing/views/period',
    'project_billing/views/table',
    'project_billing/views/graph',
    'project_billing/collections/data',
    'project_billing/views/tariff'
], function (
    $,
    Backbone,
    BootstrapTab,
    PeriodView,
    TableView,
    GraphView,
    DataCollection,
    TariffView
) {
    'use strict';
    return Backbone.Router.extend({
        initialize: function () {
            this.data = new DataCollection();
            this.data.reset();
            // Layout
            this.period_view = new PeriodView({el: $('#choose_period'), router: this});
            this.table_view = new TableView({el: $('.table-view'), router: this});
            this.graph_view = new GraphView({el: $('.graph-view'), router: this});
            this.tariff_view = new TariffView({el: $('.tariff-view'), router: this});
            this.filter = [];
        },
// Actions (aka ":period_start/:period_end*actions") was killed
        routes: {
            ':period': 'designate_period',
            ':period_start/:period_end': 'custom_period'
        },
        designate_period: function (p, s, e) {
            var today = new Date(),
                period = p === 'today' || p === 'year' || p === 'custom_period' ? p : 'month',
                start,
                end,
                num_days,
                load_dict;
            if (period === 'year') {
                start = new Date(today.getFullYear(), 0, 1);
                end = new Date(today.getFullYear(), 12, 1);
            } else if (period === 'today') {
                start = new Date();
                end = new Date();
                start.setHours(0, 0, 0, 0);
                end.setHours(23, 59, 59, 999);
            } else if (period === 'month') {
                num_days = new Date(today.getFullYear(), today.getMonth() + 1, 0).getDate();
                start = new Date();
                end = new Date();
                start.setDate(1);
                start.setHours(0, 0, 0, 0);
                end.setDate(num_days);
                end.setHours(23, 59, 59, 999);
            } else if (period === 'custom_period') {
                start = new Date(s);
                end = new Date(e);
                start.setHours(0, 0, 0, 0);
                end.setHours(23, 59, 59, 999);
            }
            this.data.load({
                'period_start': this.formatDateToISO(start.toUTCString()),
                'period_end': this.formatDateToISO(end.toUTCString())
            });
            $('.period-view a[href="#' + period + '"]').tab('show');
            $('.custom-period-indicator').empty();
        },
        custom_period: function (period_start, period_end) {
            return this.designate_period('custom_period', period_start, period_end);
        },
        formatDateToISO: function (date) {
            var new_date = new Date(date.replace(/-/g, '/'));
            return new_date.toISOString();
        }
    });
});
