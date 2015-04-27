function graphiteDataToDygraph(result) {
  var graphiteData = new Object();
  var graphLabels = ["DateTime"];

  $.each(result, function(i, item){
    //"Headers for native format(Array) must be specified via the labels option.
    //There's no other way to set them. -http://dygraphs.com/data.html#array"
    target=item.target.split('.');
    graphLabels.push(target[2]);

    //fill out the array with the metrics
    $.each(item["datapoints"], function(key, val) {
      tempDate = val[1];

      if (!(tempDate in graphiteData)) {
        graphiteData[tempDate] = [];
      }

      //I've chosen to 0 out any null values, otherwise additional data series
      //could be inserted into previous data series array
      if (val[0] === null) { val[0] = 0; }

      graphiteData[tempDate].push([val[0]]);
    });
  });

  //need to flatten the hash to an array for Dygraph
  var dygraphData = [];

  for (var key in graphiteData) {
    if (graphiteData.hasOwnProperty(key)) {
      tempArray = [];
      tempArray.push(new Date(key * 1000));

      dataSeries = graphiteData[key];

      for (var key in dataSeries) {
        if (dataSeries.hasOwnProperty(key)) {
          tempArray.push(dataSeries[key]);
        }
      }
      dygraphData.push(tempArray);
    }
  }

  return {
    dygraphData: dygraphData,
    graphLabels: graphLabels
  };
}

function createDygraph(params){
  //params should be like that :
  //
  // params = {
  //  url: 'http://graphite.example.com/render/?lineMode=connected&from=10:20_20150416&until=10:20_20150423&target=host1.service1.name',
  //  graphName: 'my service',
  //  targetDiv: 'mydiv',
  // }
  //

  url = params.url + '&format=json&jsonp=?';

  //Get JSON data from Graphite
  $.getJSON(url, function(result){

    returns = graphiteDataToDygraph(result);
    dygraphData = returns.dygraphData;
    graphLabels = returns.graphLabels;

    //You have the data Array now, so construct the graph:
    g = new Dygraph(
      document.getElementById(params.targetDiv),
      dygraphData,
      {
        fillGraph: true,
        labelsKMB: true,
        animatedZooms: true,
        title: params.graphName,
        titleHeight: 22,
        drawPoints: true,
        showRoller: true,
        // Force to display the 0
        includeZero: true,
        labels: graphLabels,
        xlabel: params.graphName,
        labelsDivStyles: {
                'text-align': 'right',
                'background': 'none'
        },
      }
    );
    g.other_urls = params.other_urls;
    // Register globaly
    dygraph_graphs.push(g);
  });
}

function updateDygraph(dygraph, new_url){

  url = dygraph.other_urls[new_url] + '&format=json&jsonp=?';

  $.getJSON(url, function(result){
    returns = graphiteDataToDygraph(result);
    dygraph.updateOptions({
      file: returns.dygraphData,
    });
  });
}
