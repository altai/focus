require.config({
  paths: {
    loader: 'libs/backbone/loader'
    , jQuery: 'libs/jquery/jquery'
    , URI: 'libs/URI/URI'
    , Backbone: 'libs/backbone/backbone'
    , Underscore: 'libs/underscore/underscore'
    , ColumnsController: 'controllers/columns'
    , DumpController: 'controllers/dump'
    , SortingController: 'controllers/sorting'
  }
});

require([
  'apps/global_list_vms'

  , 'order!libs/jquery/jquery-min'
  , 'order!libs/bootstrap/bootstrap.min'
  , 'order!libs/underscore/underscore-min'
  , 'order!libs/json2/json2-min'
  , 'order!libs/backbone/backbone-min'
  , 'order!libs/URI/URI.min'
], function(App){
  App.initialize();
});