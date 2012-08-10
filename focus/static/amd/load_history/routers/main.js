define([
  'backbone'
  , 'amd/load_history/views/main'
  , 'underscore'
], function(Backbone, View, _){
  return Backbone.Router.extend({
    initialize: function(){
      this.main = View({el: $('.main-view'), router: this})
      alert('inited')
    },
    routes: {
      ':host/:period': 'show_graphs',
      '*path': 'index'
    },
    index: function(path){
      this.view.host = null
      this.view.period =  null
      this.view.render()
    },
    show_graphs: function(host, period){
      this.view.host = null
      this.view.period =  null
      this.view.render()
    }
  });
})
