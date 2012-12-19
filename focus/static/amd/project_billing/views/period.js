define(['jq', 'backbone', 'jqueryui/datepicker'], function ($, Backbone) {
    'use strict';
    return Backbone.View.extend({
        initialize : function () {
            this.$el.find('input.datepicker').datepicker({ dateFormat: "yy-mm-dd" });
        },

        showTooltip: function ($e, message) {
            $e.tooltip({
                trigger: 'manual'
            });
            $e.data('tooltip').options.title = message;
            $e.tooltip('show');
            return false;
        },

        hideTooltip: function ($e) {
            this.$el.find('input').tooltip('hide');
        },

        validThenPath: function (s, e) {
// passed values
            var s_val = s.val(),
                e_val = e.val(),
// Warning messages
                format_msg = 'Unknown date format, use yyyy-mm-dd.\n',
                confused_msg = 'The end happens earlier than the start.\n',
                future_msg = 'Start date is in future.\n',
                empty_msg = 'The field is required.\n',
// Validation tools
                reg = /\d{4}-\d{2}-\d{2}/,
                valid_format_start = reg.test(s_val),
                valid_format_end = reg.test(e_val),
                valid_order = new Date(s_val) <= new Date(e_val),
                valid_start = new Date(s_val) <= new Date(),
                exists_start = s_val !== '',
                exists_end = e_val !== '',
// Tooltip message blanks
                start_msg = '',
                end_msg = '';
// Validation process
            if (!valid_order) {end_msg = confused_msg; }
            if (!valid_start) {start_msg = future_msg; }
            if (!valid_format_start) {start_msg = format_msg; }
            if (!valid_format_end) {end_msg = format_msg; }
            if (!exists_start) {start_msg = empty_msg; }
            if (!exists_end) {end_msg = empty_msg; }
// Raising  tooltips
            if (start_msg.length > 0) {
                this.showTooltip(s, start_msg);
            }
            if (end_msg.length > 0) {
                this.showTooltip(e, end_msg);
            }
// Period values returning
            return start_msg.length === 0 && end_msg.length === 0 && s_val + '/' + e_val;
        },

        saveDate: function (event) {
            var path = this.validThenPath($('input.datepicker[name=start]'),
                $('input.datepicker[name=end]'));

            if (path) {
                this.options.router.navigate(path, {trigger: true});
                $("#choose_period").modal("hide");
            }

            return false;
        },

        events: {
            'click [data-action=apply]': 'saveDate',
            'hidden': 'hideTooltip'
        }
    });
});
