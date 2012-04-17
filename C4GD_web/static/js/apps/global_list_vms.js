define([
  'jQuery', 
  'ColumnsController',
  'DumpController'
], function($, ColumnsController, DumpController){
  return {initialize: function(){
    $(document).ready(function(){
      new ColumnsController({el: $('#columns-controller')});
      new DumpController({el: $('#dump-controller')});
    });
/*
    $(document).ready(function(){
    
  });*/
  }};
});