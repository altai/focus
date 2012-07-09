define([
  'jq', 
  'global_list_vms/views/columns', 
  'global_list_vms/views/dump', 
  'global_list_vms/views/sorting', 
  'global_list_vms/views/dragging_columns', 
  'global_list_vms/views/groupping'
], function($, ColumnsController, DumpController, SortingController, DraggingColumnsController, GrouppingController){
  return {
    'initialize': function(){
      $(function(){
        new ColumnsController({el: $('#columns-controller')});
        new DumpController({el: $('#dump-controller')});
        $('th.sorting-contoller').each(function(num, val){
          new SortingController({el: val});
        });
        new DraggingColumnsController({el: $('.dragging-controller')});
        $('.groupping-controller').each(function(){
          new GrouppingController({el: $(this)});
        });
      });
    }
  }
});
