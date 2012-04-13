require.config({
  paths: {
    jQuery: 'libs/jquery/jquery'
    , URI: 'libs/URI/URI'
  }
});

require([
  'jQuery'
  , 'URI'
  , 'order!libs/jquery/jquery-1.7.2.min'
  , 'order!libs/bootstrap/bootstrap.min'
], function($, URI){
  $(document).ready(function(){
    var uri = URI(window.location.toString());
    $('.columns-selection  > li.selected-column > a').click(function(){
      if (!uri.search().hasOwnProperty('columns')){
        uri.addSearch({ columns: default_columns })// global var from page
      }
      uri.removeSearch('columns', $(this).attr("rel"));
      window.location.assign(uri.toString());
    });
    $('.columns-selection  > li.spare-column > a').click(function(){
      if (!uri.search().hasOwnProperty('columns')){
        uri.addSearch({ columns: default_columns })// global var from page
      }
      uri.addSearch('columns', $(this).attr("rel"));
      window.location.assign(uri.toString());
    });
    $('button.restore-columns').click(function(){
      window.location.assign(uri.removeSearch('columns'));
    });
    $('.export-json').click(function(){
      window.location.assign(uri.addSearch('export', 'json'));
    })
    $('.export-csv').click(function(){
      window.location.assign(uri.addSearch('export', 'csv'));
    })
    $('.export-xml').click(function(){
      window.location.assign(uri.addSearch('export', 'xml'));
    })
  });
});