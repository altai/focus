define([
  'jQuery',
  'Underscore',
  'ColumnsController',
  'DumpController',
  'SortingController',
  'DraggingColumnsController'
], function($, _, ColumnsController, DumpController, SortingController, DraggingColumnsController){
  return {initialize: function(){
    $(document).ready(function(){
      new ColumnsController({el: $('#columns-controller')});
      new DumpController({el: $('#dump-controller')});
      $('th.sorting-contoller').each(function(num, val){
        new SortingController({el: val});
      });
      new DraggingColumnsController({el: $('.dragging-controller')});
    });
  }};
});