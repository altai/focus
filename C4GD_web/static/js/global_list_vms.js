require.config({
  paths: {
    jQuery: 'libs/jquery/jquery'
    , URI: 'libs/URI/URI'
    , Backbone: 'libs/backbone/backbone'
    , Underscore: 'libs/underscore/underscore'
    , ColumnsController: 'controllers/columns'
    , DumpController: 'controllers/dump'
  }
});

require([
  'apps/global_list_vms'

  , 'order!libs/jquery/jquery-1.7.2.min'
  , 'order!libs/bootstrap/bootstrap.min'
  , 'order!libs/underscore/underscore-min'
  , 'order!libs/json2/json2-min'
  , 'order!libs/backbone/backbone-min'

], function(App){
  App.initialize();
});