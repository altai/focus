define(['jQuery', 'Underscore', 'Backbone', 'URI', 'Columns'], function($, _, Backbone, URI, Columns){
/*  function overlaps(a, b){
    function getBox($x){
      var pos = $x.offset();
      var width = $x.width();
      var height = $x.height();
      var $p;
      $x.parents().each(function(num, p){
        $p = $(p);
        var p_pos = $p.offset();
        pos.left = pos.left + p_pos.left;
        pos.top = pos.top + p_pos.top;
      });
      return [{x: pos.left, y: pos.top}, {x: pos.left + width, y: pos.top + height}];
    }
    ra = getBox(a);
    rb = getBox(b);
    console.log(ra)
    console.log(rb)
    return ra[0].x < rb[1].x && ra[1].x > rb[0].x && ra[0].y < rb[1].y && ra[1].y > rb[0].y
  }
  */
  return Backbone.View.extend({
    initialize: function(){
      var self = this;
      this.$el.find('a.dragging-handle').draggable();
      this.$el.find('th').droppable();
      //this.can_be_dropped = false;
    }
    , events: {
      'dragstop': function(event, ui){
        $(event.target).css('left', '0');
      },
      'drag': function(event, ui){
        ui.position.top = 0;
        // console.log(
        //   _.any(
        //     this.$el.find('th'),
        //     function(x){overlaps($(x), $(event.target))}
        //   )
        // );
      },
      'drop th': function(event, ui){
        var from = ui.draggable.parents('[data-attr-name]').attr('data-attr-name');
        var to = $(event.target).attr('data-attr-name');
        if (from != to){
          console.log('from ' + from + ' to ' + to)
          columns = new Columns();
          window.location.assign(columns.flip_columns(from, to));
        }
        // if (this.can_be_dropped){
          
        // }
      },
      // 'mouseenter th': function(event){
      //   this.can_be_dropped = true;
      // },
      // 'mouseleave th': function(event){
      //   this.can_be_dropped = false;
      // }
    },

    
  });
});