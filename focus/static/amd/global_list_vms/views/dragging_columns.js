define([
  'jq', 
  'backbone', 
  'm/uri', 
  'global_list_vms/utils/columns_util', 
  'jqueryui/draggable', 
  'jqueryui/droppable'
], function($, Backbone, URI, Columns){
  return Backbone.View.extend({
    initialize: function(){
      var self = this;
      this.$el.find('a.dragging-handle').draggable();
      this.$el.find('th').droppable();
    }
    , events: {
      'dragstop': function(event, ui){
        $(event.target).css('left', '0');
      },
      'drag': function(event, ui){
        ui.position.top = 0;
      },
      'drop th': function(event, ui){
        var from = ui.draggable.parents('[data-attr-name]').attr('data-attr-name');
        var to = $(event.target).attr('data-attr-name');
        if (from != to){
          columns = new Columns();
          window.location.assign(columns.flip_columns(from, to));
        }
      },
    },
  });
});