curl(curl_cfg, ['jq', 'select2'], function ($) {
    $(document).ready(function() {
        var params = { 'width': '99%' };
        $("#groups").select2(params);
        $("#users").select2(params);
    });
})
