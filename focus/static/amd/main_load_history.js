curl(curl_cfg, [
  'jq'
  , 'amd/load_history/views/main'
], function($, MainView){
  $(function(){
    var endpoints = {};
    $.ajax(window.ZABBIX_API, {
      async: false
      , success: function(data){
        endpoints = data.endpoints;
      }
      , dataType: "json"})

    var hosts = [];
    $.ajax(endpoints.hosts, {
      async: false
      , success: function(data){
        hosts = data
      }
      , dataType: "json"})
    
    var periods = [];
    $.ajax(endpoints.periods, {
      async: false
      , success: function(data){
        periods = data
      }
      , dataType: "json"})
    
    var parameters = [];
    $.ajax(endpoints.parameters, {
      async: false
      , success: function(data){
        parameters = data
      }
      , dataType: "json"})
    new MainView({
      el: $('.main-view')
      , hosts: hosts
      , periods: periods
      , parameters: parameters
      , url: endpoints.data
    });
  });
});
