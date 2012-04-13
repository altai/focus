require.config({
  paths: {
    jQuery: 'libs/jquery/jquery'
//    , bootstrap: 'libs/bootstrap/bootstrap'
  }
});

require([
  'app'
  , 'order!libs/jquery/jquery-1.7.2.min'
  , 'order!libs/bootstrap/bootstrap.min'
], function(App){
  App.initialize();
});