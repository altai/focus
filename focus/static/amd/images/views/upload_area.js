define([
  'images/backbone',
  'images/underscore',
  'text!/static/amd/images/templates/upload_area.html'
], function(Backbone, _, template){
  return Backbone.View.extend({
    template: _.template(template),
    render: function(){
      var self = this;
      var context = this.options;
      context['cid'] = this.cid;
      this.$el.html(this.template(context));
      // setup uploader
      var uploader = new plupload.Uploader({
        header: this.options.name,
        runtimes: 'html5,gears,flash,silverlight',
        multi_selection: false,
        chunk_size : '1mb',
        url : '',
        flash_swf_url : '/static/vendors/plupload-1.5.4/js/plupload.flash.swf',
	silverlight_xap_url : '/static/vendors/plupload-1.5.4/js/plupload.silverlight.xap',
        browse_button : 'pickfiles-' + this.cid,
        container : 'container-' + this.cid,
      });

      uploader.bind('Init', function(up, params) {
        self.$('#filelist-' + self.cid).html(
          "<div>Current runtime: " + params.runtime + ". That's nice!</div>");
      });
      
      this.$('#uploadfiles-' + this.cid).click(function(e) {
        uploader.start();
        e.preventDefault();
      });
      
      uploader.init();

      uploader.bind('FilesAdded', function(up, files) {
        $.each(files, function(i, file) {
            self.$('#filelist-' + self.cid).append(
                '<div id="' + file.id + '">' +
                file.name + ' (' + plupload.formatSize(file.size) + ') <b></b>' + '</div>');
        });
        up.refresh(); // Reposition Flash/Silverlight
      });

      uploader.bind('UploadProgress', function(up, file) {
        self.$('#' + file.id + " b").html(file.percent + "%");
      });

      uploader.bind('Error', function(up, err) {
        self.$('#filelist-' + self.cid).html(
          "<div>Error: " + err.code +
            ", Message: " + err.message +
            (err.file ? ", File: " + err.file.name : "") +
            "</div>"
        );
        
        up.refresh(); // Reposition Flash/Silverlight
      });

      uploader.bind('FileUploaded', function(up, file) {
        $('#' + file.id + " b").html("100%");
      });

    }
  });
});