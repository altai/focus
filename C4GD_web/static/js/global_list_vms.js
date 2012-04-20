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
    , DraggingColumnsController: 'controllers/dragging_columns'
    , jQueryUI: 'libs/jquery-ui/jquery-ui.js'
    , Columns: 'controllers/columns_util'
    , GrouppingController: 'controllers/groupping'
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
  , 'order!libs/jquery-ui/jquery-ui-1.8.19.custom.min'
], function(App){
  App.initialize();
});