function print_image(data){
}

function print_flavor(data){
}

function get_image(){
  val = $("#image option:selected").first().val()
  alert("/images/" + val)
  $.get("/images/" + val, "", function(data) {
    alert(data)
  })
}

function get_flavor(data){
  val = $("#flavor option:selected").first().val()
  alert("/flavors/detail/" + val)
  $.get("/flavors/detail/" + val, "", function(data) {
    alert(data)
  })
}

curl(curl_cfg, ['jq'], function($){
  $(document).ready(function(){
    $("#image").change(get_image)
    $("#flavor").change(get_flavor)
  });
});

