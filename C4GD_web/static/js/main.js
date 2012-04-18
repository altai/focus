require.config({
  paths: {
    jQuery: 'libs/jquery/jquery-raw',
    app: 'apps/main'
  }
});

require([
  'app'
  , 'order!libs/jquery/jquery-min'
  , 'order!libs/bootstrap/bootstrap.min'
], function(App){
  App.initialize();
});