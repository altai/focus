define(['jquery', 'underscore', 'ColumnsController', 'DumpController', 'SortingController', 'DraggingColumnsController', 'GrouppingController'], function($, _, ColumnsController, DumpController, SortingController, DraggingColumnsController, GrouppingController){
  return {initialize: function(){
    $(document).ready(function(){
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
  }};
});
