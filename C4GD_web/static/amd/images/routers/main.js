define([
  'images/jq',
  'images/backbone',
  'images/views/upload'
], function($, Backbone, UploadView){
  return Backbone.Router.extend({
    initialize: function(){
      this.view = new UploadView({
        el: $('.upload-view'),
        router: this
      })
    },

    routes: {
      ':upload_type': 'upload_type_selection',
      '.*': 'go_combined'
    },

    upload_type_selection: function(upload_type){
      if (_.indexOf(['combined', 'kernel', 'rootfs', 'initrd'], upload_type) != -1){
        this.view.selected_upload_type = upload_type;
        this.view.render();
      } else {
        this.navigate('', trigger=true)
      }
    },

    go_combined: function(){
      this.navigate('combined', trigger=true);
    },

  });
});