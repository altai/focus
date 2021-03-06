define([
  'images/backbone',
  'images/underscore',
  'text!/static/amd/images/templates/upload.html',
  'text!/static/amd/images/templates/progress_bar.html',
  'text!/static/amd/images/templates/api_progress_bar.html'
], function(Backbone, _, template, progress_bar_template, api_progress_bar_template){
  return Backbone.View.extend({
    initialize: function(){
      this.options.kernel_list = window.kernel_list; // from global
      this.options.initrd_list = window.initrd_list; // from global
    },
    events: {
      'change input#id_upload_type': function(e){
        this.options.router.navigate(e.currentTarget.value, trigger=true)
      },
      'click button[type=submit]': function(e){
        e.preventDefault();
        if (this.formValid()){
          if (this.selected_upload_type == 'solid'){
            var uploaded_filename = this.$('#uploaded_filename').html();
            this.$el.append('<input type="hidden" name="uploaded_filename" value="' + uploaded_filename  + '">');
          } else {
            var uploaded_kernel_filename = this.$("#kernel_container #uploaded_filename").html();
            var uploaded_initrd_filename = this.$("#initrd_container #uploaded_filename").html();
            var uploaded_filesystem_filename = this.$("#filesystem_container #uploaded_filename").html();
            this.$el.append('<input type="hidden" name="uploaded_kernel" value="' + uploaded_kernel_filename  + '">');
            this.$el.append('<input type="hidden" name="uploaded_initrd" value="' + uploaded_initrd_filename  + '">');
            this.$el.append('<input type="hidden" name="uploaded_filesystem" value="' + uploaded_filesystem_filename  + '">');
          }
          var bkp_form_actions = this.$('.form-actions').html();
          this.$('.form-actions').html(
            '<div width="100%" height="100%" align="left"><img src="/static/img/ajax-loader.gif"></div>'
          );
          var $f = $('form.new-image');
          var self = this;

          // start transmitting uploaded images to Glance
          $.post($f.attr('action'), $f.serialize())
          // callbacks on transmission complete
          .success(function(){
              window.location = window.location.pathname.replace('new/', '');
          })
          .error(function(){
              self.$('.form-actions').html(bkp_form_actions);
              self.render();
          });

          // Here was commented code for showing progress bar on transmitting
          // images to Glance. If you need this code again - find it in earlier
          // versions of this file in repository.
      }
      },
      'click .cancel-upload': function(e){
          e.preventDefault();
          this.uploader.stop()
          this.progress_bar(this.$('#filelist'), {});
          $('#id_uploaded_file').val('');
      }
    },
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
      if (this.selected_upload_type == 'solid'){
        if (!window.is_file_uploaded){
          this.error_messages['uploader'] = 'No complete upload';
        }
      }else{
        if (!(window.is_kernel_uploaded || ($('#kernel_container option:selected' == 'Upload')))
            && !(window.is_initrd_uploaded  || ($('#initrd_container option:selected' == 'Upload')))
            && !window.is_filesystem_uploaded){
          this.error_messages['uploader'] = 'No complete upload';
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
    template: _.template(template),
    _progress_bar: _.template(progress_bar_template),
    progress_bar: function($el, context){
        $el.html(this._progress_bar(context));
        if (context.file_percent != undefined){
            $el.parent().find('a.cancel-upload').show()
        } else {
            $el.parent().find('a.cancel-upload').hide()
        }
    },
    api_progress_bar: _.template(api_progress_bar_template),
    render_with_respect_to_upload: function(){
      var name = this.$('#id_name').val();
      this.clean_error_messages();
      this.render();
      this.$('input#id_upload_type').removeAttr('checked');
      this.$('input#id_upload_type[value='+ this.selected_upload_type +']').attr('checked', 'checked');
      this.$('#id_name').val(name);
    },
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
      /* first time there is no uploader */
      if (this.selected_upload_type == 'solid'){
        if (this.uploader){
          this.uploader.stop();
        }
        var self = this;
        this.uploader = new plupload.Uploader({
          runtimes: 'html5,gears,flash,silverlight',
          multi_selection: this.selected_upload_type=='amazon_like',
          url : '/fast-upload/',
          flash_swf_url : '/static/vendors/plupload-1.5.4/js/plupload.flash.swf',
	  silverlight_xap_url : '/static/vendors/plupload-1.5.4/js/plupload.silverlight.xap',
          browse_button : 'id_uploaded_file_button',
          container : 'container',
        });

        this.uploader.bind('Init', function(up, params) {
          //self.$('#filelist').html(self.progress_bar());
        });
        this.uploader.init();
        this.uploader.bind('FilesAdded', function(up, files) {
          /*
            Remove previous content of the queue as we have
            1 item uploaded at the time.
          */
          window.is_file_uploaded = false;
          self.$('.form-actions button[type=submit]').attr('disabled', 'disabled');
          this.splice(0, this.files.length - 1);
          self.$('.uploader').removeClass('alert-error');
          self.$('.uploader p.help-block').remove();
          self.$('#filelist').removeClass('hide');
          $.each(files, function(i, file) {
            self.progress_bar(self.$('#filelist'), {
              file_id: file.id,
              file_name: file.name,
              file_size: plupload.formatSize(file.size),
              file_percent: file.percent
            })
          });
          up.refresh(); // Reposition Flash/Silverlight
          up.start()
          $('#autoupload_container').removeClass('hide');
        });

        this.uploader.bind('UploadProgress', function(up, file) {
          self.progress_bar(self.$('#filelist'), {
            file_id: file.id,
            file_name: file.name,
            file_size: plupload.formatSize(file.size),
            file_percent: file.percent,
            bytes_loaded: file.loaded,
            bytes_size: file.size
          })
        });

        this.uploader.bind('Error', function(up, err) {
            self.progress_bar(self.$('#filelist'), {
            'error': err
          })
          up.refresh(); // Reposition Flash/Silverlight
          $('#id_uploaded_file').val('Select file');
        });
        
        this.uploader.bind('FileUploaded', function(up, file, response) {
          $('#autoupload_container').addClass('hide');
          $('#' + file.id + " b").html("100%");
          $('#' + file.id).append('<div id="uploaded_filename" class=" hide">' + response.response + '</div>');
          window.is_file_uploaded = true;
          self.$('.form-actions button[type=submit]').removeAttr('disabled');
        	$('#id_uploaded_file').val(file.name);
	        $('#filelist').addClass('hide');
	        if ($('#autoupload').is(':checked')){
	          $('button[type=submit]').click();
	        }
        });
      } else {
        // amazon
        
        // kernel uploader start
          if (this.kernel_uploader){
            this.kernel_uploader.stop();
          }
          var self = this;
          this.kernel_uploader = new plupload.Uploader({
            runtimes: 'html5,gears,flash,silverlight',
            multi_selection: false,
            url : '/fast-upload/',
            flash_swf_url : '/static/vendors/plupload-1.5.4/js/plupload.flash.swf',
      silverlight_xap_url : '/static/vendors/plupload-1.5.4/js/plupload.silverlight.xap',
            browse_button : 'kernel_uploaded_file_button',
            container : 'kernel_container',
          });
          $('#id_kernel').change(function(){
            if ($("#id_kernel option:selected").val() == 'Upload new kernel'){
                $("#id_kernel").val("Select kernel");
                $("#kernel_uploaded_file_button").click();
            }
            $('#id_initrd').removeAttr('disabled');
          });
          this.kernel_uploader.init();
          this.kernel_uploader.bind('FilesAdded', function(up, files) {
            /*
              Remove previous content of the queue as we have
              1 item uploaded at the time.
            */
            window.is_kernel_uploaded = false;
            self.$('#kernel_container .form-actions button[type=submit]').attr('disabled', 'disabled');
            this.splice(0, this.files.length - 1);
            self.$('#kernel_container .uploader').removeClass('alert-error');
            self.$('#kernel_container .uploader p.help-block').remove();
            self.$('#kernel_container #filelist').removeClass('hide');
            $.each(files, function(i, file) {
                self.progress_bar(self.$('#kernel_container #filelist'), {
                file_id: file.id,
                file_name: file.name,
                file_size: plupload.formatSize(file.size),
                file_percent: file.percent
              })
            });
            up.refresh(); // Reposition Flash/Silverlight
            up.start();
          });

          this.kernel_uploader.bind('UploadProgress', function(up, file) {
              self.progress_bar(self.$('#kernel_container #filelist'), {
              file_id: file.id,
              file_name: file.name,
              file_size: plupload.formatSize(file.size),
              file_percent: file.percent,
              bytes_loaded: file.loaded,
              bytes_size: file.size
            })
          });

          this.kernel_uploader.bind('Error', function(up, err) {
              self.progress_bar(self.$('#kernel_container #filelist'), {
              'error': err
            })
            up.refresh(); // Reposition Flash/Silverlight
            $('#kernel_container #id_uploaded_file').val('Select file');
          });
          
          this.kernel_uploader.bind('FileUploaded', function(up, file, response) {
            $('#kernel_container #' + file.id + " b").html("100%");
            $('#kernel_container #' + file.id).append('<div id="uploaded_filename" class=" hide">' + response.response + '</div>');
            window.is_kernel_uploaded = true;
            if (window.is_filesystem_uploaded && (window.is_initrd_uploaded || $("#initrd_container option:selected") != 'Upload')){
              self.$('.form-actions button[type=submit]').removeAttr('disabled');
            }
            $('#kernel_container #filelist').removeClass('hide');
            $('#kernel_container select').prepend('<option value="'+ file.name +'" selected>'+ file.name +'</option>');
            if ($('#autoupload').is(':checked')){
              $('button[type=submit]').click();
            }
          });
        // kernel uploader end

        // initrd uploader start
          if (this.initrd_uploader){
            this.initrd_uploader.stop();
          }
          var self = this;
          this.initrd_uploader = new plupload.Uploader({
            runtimes: 'html5,gears,flash,silverlight',
            multi_selection: false,
            url : '/fast-upload/',
            flash_swf_url : '/static/vendors/plupload-1.5.4/js/plupload.flash.swf',
      silverlight_xap_url : '/static/vendors/plupload-1.5.4/js/plupload.silverlight.xap',
            browse_button : 'initrd_uploaded_file_button',
            container : 'initrd_container',
          });
          $('#id_initrd').change(function(){
            if ($("#id_initrd option:selected").val() == 'Upload new initrd'){
                $("#id_initrd").val("Select initrd");
                $("#initrd_uploaded_file_button").click();
            }
            $('#filesystem_uploaded_file_button').removeAttr('disabled');
          });
          this.initrd_uploader.init();
          this.initrd_uploader.bind('FilesAdded', function(up, files) {
            /*
              Remove previous content of the queue as we have
              1 item uploaded at the time.
            */
            window.is_initrd_uploaded = false;
            self.$('#initrd_container .form-actions button[type=submit]').attr('disabled', 'disabled');
            this.splice(0, this.files.length - 1);
            self.$('#initrd_container .uploader').removeClass('alert-error');
            self.$('#initrd_container .uploader p.help-block').remove();
            self.$('#initrd_container #filelist').removeClass('hide');
            $.each(files, function(i, file) {
                self.progress_bar(self.$('#initrd_container #filelist'), {
                file_id: file.id,
                file_name: file.name,
                file_size: plupload.formatSize(file.size),
                file_percent: file.percent
              })
            });
            up.refresh(); // Reposition Flash/Silverlight
            up.start()
          });

          this.initrd_uploader.bind('UploadProgress', function(up, file) {
              self.progress_bar(self.$('#initrd_container #filelist'), {
              file_id: file.id,
              file_name: file.name,
              file_size: plupload.formatSize(file.size),
              file_percent: file.percent,
              bytes_loaded: file.loaded,
              bytes_size: file.size
            })
          });

          this.initrd_uploader.bind('Error', function(up, err) {
              self.progress_bar(self.$('#initrd_container #filelist'), {
              'error': err
            })
            up.refresh(); // Reposition Flash/Silverlight
            $('#initrd_container #id_uploaded_file').val('Select file');
          });
          
          this.initrd_uploader.bind('FileUploaded', function(up, file, response) {
            $('#initrd_container #' + file.id + " b").html("100%");
            $('#initrd_container #' + file.id).append('<div id="uploaded_filename" class=" hide">' + response.response + '</div>');
            window.is_initrd_uploaded = true;
            if (window.is_filesystem_uploaded && (window.is_kernel_uploaded || $("#kernel_container option:selected") != 'Upload')){
              self.$('.form-actions button[type=submit]').removeAttr('disabled');
            }
            $('#initrd_container #filelist').removeClass('hide');
            $('#initrd_container select').prepend('<option value="'+ file.name +'" selected>'+ file.name +'</option>');
            if ($('#autoupload').is(':checked')){
              $('button[type=submit]').click();
            }
          });
        // initrd uploader end

        // filesystem uploader start
          if (this.filesystem_uploader){
            this.filesystem_uploader.stop();
          }
          var self = this;
          this.filesystem_uploader = new plupload.Uploader({
            runtimes: 'html5,gears,flash,silverlight',
            multi_selection: false,
            url : '/fast-upload/',
            flash_swf_url : '/static/vendors/plupload-1.5.4/js/plupload.flash.swf',
      silverlight_xap_url : '/static/vendors/plupload-1.5.4/js/plupload.silverlight.xap',
            browse_button : 'filesystem_uploaded_file_button',
            container : 'filesystem_container',
          });

          this.filesystem_uploader.init();
          this.filesystem_uploader.bind('FilesAdded', function(up, files) {
            /*
              Remove previous content of the queue as we have
              1 item uploaded at the time.
            */
            window.is_filesystem_uploaded = false;
            self.$('#filesystem_container .form-actions button[type=submit]').attr('disabled', 'disabled');
            this.splice(0, this.files.length - 1);
            self.$('#filesystem_container .uploader').removeClass('alert-error');
            self.$('#filesystem_container .uploader p.help-block').remove();
            self.$('#filesystem_container #filelist').removeClass('hide');
            $.each(files, function(i, file) {
                self.progress_bar(self.$('#filesystem_container #filelist'), {
                file_id: file.id,
                file_name: file.name,
                file_size: plupload.formatSize(file.size),
                file_percent: file.percent
              })
            });
            up.refresh(); // Reposition Flash/Silverlight
            up.start()
            $('#autoupload_container').removeClass('hide');
          });

          this.filesystem_uploader.bind('UploadProgress', function(up, file) {
              self.progress_bar(self.$('#filesystem_container #filelist'), {
              file_id: file.id,
              file_name: file.name,
              file_size: plupload.formatSize(file.size),
              file_percent: file.percent,
              bytes_loaded: file.loaded,
              bytes_size: file.size
            })
          });

          this.filesystem_uploader.bind('Error', function(up, err) {
              self.progress_bar(self.$('#filesystem_container #filelist'), {
                  'error': err
              })
            up.refresh(); // Reposition Flash/Silverlight
            $('#filesystem_container #id_uploaded_file').val('Select file');
          });
          
          this.filesystem_uploader.bind('FileUploaded', function(up, file, response) {
            $('#autoupload_container').addClass('hide');
            $('#filesystem_container #' + file.id + " b").html("100%");
            $('#filesystem_container #' + file.id).append('<div id="uploaded_filename" class=" hide">' + response.response + '</div>');
            window.is_filesystem_uploaded = true;
            if ((window.is_kernel_uploaded || $("#kerel_container option:selected") != 'Upload')
              && (window.is_initrd_uploaded || $("#initrd_container option:selected") != 'Upload')){
              self.$('.form-actions button[type=submit]').removeAttr('disabled');
            }
            $('#filesystem_container #filelist').removeClass('hide');
            $('#filesystem_container #filesystem_uploaded_file').val(file.name);
            if ($('#autoupload').is(':checked')){
              $('button[type=submit]').click();
            }
          });
        // filesystem uploader end

        // end amazon
      }
    }
  });
});
