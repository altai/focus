define([
  'jQuery', 
  'ColumnsController'
], function($, ColumnsController){
  return {initialize: function(){
    $(document).ready(function(){
      new ColumnsController({el: $('#columns-controller')});
    });
/*
    $(document).ready(function(){
    
    $('button.restore-columns').click(function(){
      window.location.assign(uri.removeSearch('columns'));
    });
    $('.export-json').click(function(e){
      e.preventDefault();
      uri.search['export'] = 'json'
      window.location.assign(uri.toString());
    })
    $('.export-csv').click(function(e){
      e.preventDefault();
      uri.search['export'] = 'csv'
      window.location.assign(uri.toString());
    })
    $('.export-xml').click(function(e){
      e.preventDefault();
      uri.search['export'] = 'xml'
      window.location.assign(uri.toString());
    })
  });*/
  }};
});