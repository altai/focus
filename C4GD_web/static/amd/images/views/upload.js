define([
  'images/backbone',
  'images/underscore',
  'text!/static/amd/images/templates/upload.html',
  'text!/static/amd/images/templates/progress_bar.html'
], function(Backbone, _, template, progress_bar_template){
  return Backbone.View.extend({
    initialize: function(){
      this.options.kernel_list = window.kernel_list; // from global
      this.options.initrd_list = window.initrd_list; // from global
    },
    events: {
      'change select#id_upload_type': function(e){
        this.options.router.navigate(e.currentTarget.value, trigger=true)
      },
      'click button[type=submit]': function(e){
        if (!this.formValid()){
          e.preventDefault();
          this.render();
        } else {
          this.$el.append('<input type="hidden" name="uploaded_filename" value="' + this.$('#uploaded_filename').html()  + '">')
        }
      }
    },
    error_messages: {},
    formValid: function(){
      this.error_messages = {}
      if (!this.$('#id_name').val()){
        this.error_messages['name'] = 'Required field';
      }
      if (!this.$('#uploaded_filename').length){
        this.error_messages['uploader'] = 'No complete upload';
      }
      if (this.$('#id_upload_type').val() == 'rootfs'){
        if (!this.$('#id_kernel').val()){
          this.error_messages['kernel'] = 'No kernel image selected';
        }
        if (!this.$('#id_initrd').val()){
          this.error_messages['initrd'] = 'No initrd image selected';
        }
      }
      return _.isEmpty(this.error_messages);
    },
    selected_upload_type: 0,
    template: _.template(template),
    progress_bar: _.template(progress_bar_template),
    render: function(){
      context = {
        'selected_upload_type': this.selected_upload_type,
        'kernel_list': this.options.kernel_list,
        'initrd_list': this.options.initrd_list,
        'error_messages': this.error_messages
      };
      if (this.$('#id_name').val()){
        context['name'] = this.$('#id_name').val()
      };
      if (this.$('#uploaded_filename').length){
        context['uploaded_filename'] = this.$('#uploaded_filename').html()
      }
      this.$el.html(this.template(context));
      
      var self = this;
      var uploader = new plupload.Uploader({
        runtimes: 'html5,gears,flash,silverlight',
        multi_selection: false,
        url : 'upload/',
        flash_swf_url : '/static/vendors/plupload-1.5.4/js/plupload.flash.swf',
	silverlight_xap_url : '/static/vendors/plupload-1.5.4/js/plupload.silverlight.xap',
        browse_button : 'pickfiles',
        container : 'container',
      });
      
      uploader.bind('Init', function(up, params) {
        self.$('#filelist').html(self.progress_bar({
          'runtime': "Current runtime: " + params.runtime
        }))
      });
      
      this.$('#uploadfiles').click(function(e) {
        uploader.start();
        e.preventDefault();
      });
      
      uploader.init();
      
      uploader.bind('FilesAdded', function(up, files) {
        /*
          Remove previous content of the queue as we have 
          1 item uploaded at the time.
          */
        this.files = [_.last(this.files)];
        self.$('.uploader').removeClass('alert-error');
        self.$('.uploader p.help-block').remove();
        $.each(files, function(i, file) {
          self.$('#filelist').html(self.progress_bar({
            file_id: file.id,
            file_name: file.name,
            file_size: plupload.formatSize(file.size),
            file_percent: file.percent
          }))
        });
        up.refresh(); // Reposition Flash/Silverlight
      });
      
      uploader.bind('UploadProgress', function(up, file) {
          self.$('#filelist').html(self.progress_bar({
            file_id: file.id,
            file_name: file.name,
            file_size: plupload.formatSize(file.size),
            file_percent: file.percent
          }))
      });
      
      uploader.bind('Error', function(up, err) {
        self.$('#filelist').html(self.progress_bar({
          'error': err
        }));        
        up.refresh(); // Reposition Flash/Silverlight
      });
      
      uploader.bind('FileUploaded', function(up, file, response) {
        $('#' + file.id + " b").html("100%");
        $('#' + file.id).append('<div id="uploaded_filename" class=" hide">' + response.response + '</div>')
      });

    }
  });
});