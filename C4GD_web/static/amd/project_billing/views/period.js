define(['backbone', 'jqueryui/datepicker'], function(Backbone){
  return Backbone.View.extend({
    initialize: function(){
      this.$el.find('input.datepicker').datepicker({ dateFormat: "yy-mm-dd" });
    },
    events: {
      'click .btn-primary': function(event){
        
        var sin = false;
        var oy = function($e, message){
          $e.data('tooltip', false); // reset needed
          $e.tooltip({
              title: message,
              trigger: 'manual'
          });
          $e.tooltip('show');
          sin = true;
          event.preventDefault();
        }
        function validateField($v){
          if (!$v.val().match(/\d{4}-\d{2}-\d{2}/)){
            oy($v, 'Unknown date format, use yyyy-mm-dd');
          }
        }
        var $start = $('input.datepicker[name=start]');
        var $end = $('input.datepicker[name=end]');
        validateField($start);
        validateField($end);
        if (!sin){
          if ($start.val() > $end.val()){
            oy($end, 'The end happens earlier than the start');
          }
        }

        if (!sin){
          /* actually change dates */
          var path = $start.val() + '/' + $end.val();
          this.options.router.navigate(path, {trigger: true});
          $("#choose_period").modal("hide");
          //return false to stop further processing of the event
          return false;
        }
      }
      , 'focus input.datepicker': function(event){
        $(event.target).tooltip('hide');
      }
    }
  });
});