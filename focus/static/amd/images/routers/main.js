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
    },

    upload_type_selection: function(upload_type){
      if (_.indexOf(['solid', 'amazon_like'], upload_type) != -1){
        this.view.selected_upload_type = upload_type;
        this.view.render_with_respect_to_upload();
      } else {
        this.navigate('solid', trigger=true)
      }
      $('input#id_upload_type').removeAttr('checked');
      $('input#id_upload_type[value='+ upload_type +']').attr('checked', 'checked');
    },
  });
});
