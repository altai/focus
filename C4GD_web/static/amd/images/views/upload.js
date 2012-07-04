define([
  'images/backbone',
  'images/underscore',
  'text!/static/amd/images/templates/upload.html',
  'text!/static/amd/images/templates/progress_bar.html',
  'text!/static/amd/images/templates/rootfs_partial.html'
], function(Backbone, _, template, progress_bar_template, rootfs_partial_template){
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
        } else {
          this.$el.append('<input type="hidden" name="uploaded_filename" value="' + this.$('#uploaded_filename').html()  + '">');
          // and form is submitted -- make AJAX instead
        }
      },
      'click .cancel-upload': function(e){
        e.preventDefault();
        this.uploader.stop()
        this.uploader.splice();
        this.$('#filelist').html(this.progress_bar());
      }
    },
    is_file_uploaded: false,
    error_messages: {},
    clean_error_messages: function(){
      var self = this;
      _.each(this.error_messages, function(value, key){
        var $el = self.$('[data-error-key="' + key + '"]');
        $el.addClass('alert-error');
        $el.find('.controls').append('<p class="help-block error-message">' + value  + '</p>')
      });
    },
    formValid: function(){
      /*
        Validate form.

        Mark erroneus fields as side effect.
        No form rendering happens here.
        Return boolean true if no errors otherwise return false.

        */

      /* build list of error messages */
      this.error_messages = {}
      if (!this.$('#id_name').val()){
        this.error_messages['name'] = 'Required field';
      }
      if (!this.is_file_uploaded){
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

      /* remove alert error css classes and error messages from containers
         marked with alert error classes*/
      this.$('.alert-error').each(function(){
        $(this).removeClass('alert-error');
        $(this).find('.help-block.error-message').remove();
      });

      /* for each error add alert error class and error message */
      this.clean_error_messages();
      return _.isEmpty(this.error_messages);
    },
    selected_upload_type: 0,
    rootfs_partial: _.template(rootfs_partial_template),
    template: _.template(template),
    progress_bar: _.template(progress_bar_template),
    render_with_respect_to_upload: function(){
      var name = this.$('#id_name').val();
      if (this.is_file_uploaded){
        this.clean_error_messages();
        this.$('.rootfs-partial').remove();
        if (this.selected_upload_type == 'rootfs'){
          this.$('.control-group.upload-type').after(
            this.rootfs_partial({
              kernel_list: this.options.kernel_list, 
              initrd_list: this.options.initrd_list,
              selected_upload_type: this.selected_upload_type}));
        }
      } else {
        this.render();
        this.$('#id_name').val(name);
      }
    },
    render: function(){
      context = {
        'rootfs_partial': this.rootfs_partial,
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
      /* first time there is no uploader */
      if (this.uploader){
        this.uploader.stop();
      }
      var self = this;
      this.uploader = new plupload.Uploader({
        runtimes: 'html5,gears,flash,silverlight',
        multi_selection: false,
        url : 'upload/',
        flash_swf_url : '/static/vendors/plupload-1.5.4/js/plupload.flash.swf',
	silverlight_xap_url : '/static/vendors/plupload-1.5.4/js/plupload.silverlight.xap',
        browse_button : 'pickfiles',
        container : 'container',
      });
      
      this.uploader.bind('Init', function(up, params) {
        self.$('#filelist').html(self.progress_bar());
      });
      
      this.uploader.init();
      
      this.uploader.bind('FilesAdded', function(up, files) {
        /*
          Remove previous content of the queue as we have 
          1 item uploaded at the time.
          */
        self.is_file_uploaded = false;
        this.splice(0, this.files.length - 1);
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
        up.start()
      });
      
      this.uploader.bind('UploadProgress', function(up, file) {
          self.$('#filelist').html(self.progress_bar({
            file_id: file.id,
            file_name: file.name,
            file_size: plupload.formatSize(file.size),
            file_percent: file.percent,
            bytes_loaded: file.loaded,
            bytes_size: file.size
          }))
      });
      
      this.uploader.bind('Error', function(up, err) {
        self.$('#filelist').html(self.progress_bar({
          'error': err
        }));        
        up.refresh(); // Reposition Flash/Silverlight
        $('#pickfiles').html('Select file');
      });
      
      this.uploader.bind('FileUploaded', function(up, file, response) {
        $('#' + file.id + " b").html("100%");
        $('#' + file.id).append('<div id="uploaded_filename" class=" hide">' + response.response + '</div>');
        self.is_file_uploaded = true;
        $('#pickfiles').html('Select another file');
      });

    }
  });
});
