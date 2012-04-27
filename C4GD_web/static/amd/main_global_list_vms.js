define.amd.jQuery = true;
require.config({
  paths: {
    URI: 'm/uri'
    , ColumnsController: 'global_list_vms/views/columns'
    , DumpController: 'global_list_vms/views/dump'
    , SortingController: 'global_list_vms/views/sorting'
    , DraggingColumnsController: 'global_list_vms/views/dragging_columns'
    , Columns: 'global_list_vms/utils/columns_util'
    , GrouppingController: 'global_list_vms/views/groupping'
  }
});

require([
  'global_list_vms/main'
  , 'm/bootstrap/dropdown'
, 'm/bootstrap/collapse'
], function(App){
  App.initialize();
});