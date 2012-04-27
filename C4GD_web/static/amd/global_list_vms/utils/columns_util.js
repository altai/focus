define(['underscore', 'URI'], function (_, URI){
  return function (){
    var uri = URI(window.location.toString());
    // default columns come from page in global context
    var parsed_uri = uri.search(true);
    if (_.has(parsed_uri, 'columns')){
      var columns = parsed_uri.columns.split(',');
    } else {
      var columns = default_columns;
    }
    function join(){
      return uri.removeSearch('columns').addSearch('columns', columns.join()).toString(); 
    }
    this.flip_columns = function(a, b){
      a_i = _.indexOf(columns, a);
      b_i = _.indexOf(columns, b);
      columns[a_i] = b;
      columns[b_i] = a;
      return join();
    }
    this.add = function(v){
      if (columns.indexOf(v) === -1){
        columns.push(v);
      }
      return join();
    }
    this.remove = function(v){
      columns = _.reject(columns, function(x){return x == v});
      return join();
    }
  }
});