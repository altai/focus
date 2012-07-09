function get_obj_by_id(arr, id){
  for (var i = arr.length - 1; i >= 0; --i) {
    if (arr[i].id == id) {
	return arr[i];
    }
  }
  return null;
}

function update_info(eventObject){
    var data = eventObject.data;
    var name = data.name;
    var obj = get_obj_by_id(data.array, $("#" + name + " option:selected").first().val());
    if (obj == null)
	return;
    $("." + name + "_properties").html(_.template(data.template, {obj: obj}));
}

curl(curl_cfg, ['jq'], function($) {
	$(document).ready(function() {
		var change_data = [{
			template: "<p>ID: <%= obj.id %></p>" +
			"<p>Name: <%= obj.name %></p>" +
			"<p>Status: <%= obj.status %></p>" +
			"<p>Container Format: <%= obj.container_format %></p>" +
			"<p>Disk Format: <%= obj.disk_format %></p>" +
			"<p>Size: <%= obj.size %></p>",
			name: "image",
			array: images
		    }, {
			template: "<p>ID: <%= obj.id %></p>" +
			"<p>Name: <%= obj.name %></p>" +
			"<p>VCPUs: <%= obj.vcpus %></p>" +
			"<p>RAM: <%= obj.ram %> MiB</p>" +
			"<p>Disk: <%= obj.disk %> GiB</p>",
			name: "flavor",
			array: flavors
		    }];
		for (var i = 0; i < change_data.length; ++i) {
		    $("#" + change_data[i].name).change(change_data[i], update_info);
		    $("#" + change_data[i].name).change();
		}
	    });
    });
