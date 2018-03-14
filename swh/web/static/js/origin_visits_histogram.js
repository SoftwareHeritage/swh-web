// Creation of a stacked histogram with D3.js for SWH origin visits history
// Parameters description:
//  - container: selector for the div that will contain the histogram
//  - visits_data: raw swh origin visits data
//  - current_year: the visits year to display by default
//  - year_click_callback: callback when the user selects a year through the histogram

function create_visits_histogram(container, visits_data, current_year, year_click_callback) {

    // remove previously created hisogram and tooltip if any
    d3.select(container).select('svg').remove();
    d3.select('div.d3-tooltip').remove();

    // histogram size and margins
    var width = 1000, height = 300,
        margin = {top: 20, right: 80, bottom: 30, left: 50};

    // create responsive svg
    var svg = d3.select(container)
                .attr("style",
                      "padding-bottom: " + Math.ceil(height * 100 / width) + "%")
                .append("svg")
                .attr("viewBox", "0 0 " + width + " " + height);

    // create tooltip div
    var tooltip = d3.select("body")
                    .append("div")
                    .attr("class", "d3-tooltip")
                    .style("opacity", 0);

    // update width and height without margins
    width = width - margin.left - margin.right,
    height = height - margin.top - margin.bottom;

    // create main svg group element
    var g = svg.append("g").attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    // create x scale
    var x = d3.scaleTime().rangeRound([0, width]);

    // create y scale
    var y = d3.scaleLinear().range([height, 0]);

    // create oridinal colorscale mapping visit status
    var colors = d3.scaleOrdinal()
                   .domain(["full", "partial", "failed", "ongoing"])
                   .range(["#008000", "#edc344", "#ff0000", "#0000ff"]);

    // first SWH crawls were made in 2015
    var startYear = 2015;
    // set latest display year as the current one
    var now = new Date();
    var endYear = now.getUTCFullYear()+1;
    var monthExtent = [new Date(Date.UTC(startYear, 0, 1)), new Date(Date.UTC(endYear, 0, 1))];

    var currentYear = current_year;

    // create months bins based on setup extent
    var monthBins = d3.timeMonths(d3.timeMonth.offset(monthExtent[0], -1), monthExtent[1]);
    // create years bins based on setup extent
    var yearBins = d3.timeYears(monthExtent[0], monthExtent[1]);

    // set x scale domain
    x.domain(d3.extent(monthBins));

    // use D3 histogram layout to create a function that will bin the visits by month
    var binByMonth = d3.histogram()
                       .value(function(d) {
                           return d.date;
                       })
                       .domain(x.domain())
                       .thresholds(monthBins);

    // use D3 nest function to group the visits by status
    var visitsByStatus = d3.nest()
                                .key(function(d) {
                                    return d["status"]
                                })
                                .sortKeys(d3.ascending)
                                .entries(visits_data);

    // prepare data in order to be able to stack visit statuses by month
    var statuses = [];
    var histData = [];
    for (var i = 0 ; i < monthBins.length ; ++i) {
        histData[i] = {};
    }
    visitsByStatus.forEach(function(entry) {
        statuses.push(entry.key);
        var monthsData = binByMonth(entry.values);
        for (var i = 0 ; i < monthsData.length ; ++i) {
            histData[i]['x0'] = monthsData[i]['x0'];
            histData[i]['x1'] = monthsData[i]['x1'];
            histData[i][entry.key] = monthsData[i];
        }
    });

    // create function to stack visits statuses by month
    var stacked = d3.stack()
                    .keys(statuses)
                    .value(function(d, key) {
                        return d[key].length;
                    });

    // compute the maximum amount of visits by month
    var yMax = d3.max(histData, function(d) {
        var total = 0;
        for (var i = 0 ; i < statuses.length ; ++i) {
            total += d[statuses[i]].length;
        }
        return total;
    });

    // set y scale domain
    y.domain([0, yMax]);

    // compute ticks values for the y axis
    var step = 5;
    var yTickValues = [];
    for (var i = 0 ; i <= yMax/step ; ++i) {
        yTickValues.push(i*step);
    }
    if (yTickValues.length == 0) {
        for (var i = 0 ; i <= yMax ; ++i) {
            yTickValues.push(i);
        }
    } else if (yMax%step != 0) {
        yTickValues.push(yMax);
    }

    // add histogram background grid
    g.append("g")
     .attr("class", "grid")
     .call(d3.axisLeft(y)
             .tickValues(yTickValues)
             .tickSize(-width)
             .tickFormat(""))

    // create one fill only rectangle by displayed year
    // each rectangle will be made visible when hovering the mouse over a year range
    // user will then be able to select a year by clicking in the rectangle
    g.append("g")
     .selectAll("rect")
     .data(yearBins)
     .enter().append("rect")
     .attr("class", function(d) {return "year" + d.getUTCFullYear()})
     .attr("fill", 'red')
     .attr('fill-opacity', function(d) {
         return d.getUTCFullYear() == currentYear ? 0.3 : 0;
     })
     .attr('stroke', 'none')
     .attr("x", function(d) {
         var date = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
         return x(date);
     })
     .attr("y", 0)
     .attr("height", height)
     .attr("width", function(d) {
         var date = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
         var yearWidth = x(d3.timeYear.offset(date, 1)) - x(date);
         return yearWidth;
     })
     // mouse event callbacks used to show rectangle years
     // when hovering the mouse over the histograms
     .on("mouseover", function(d) {
         svg.selectAll('rect.year' + d.getUTCFullYear())
            .attr('fill-opacity', 0.5);
     })
     .on("mouseout", function(d) {
         svg.selectAll('rect.year' + d.getUTCFullYear())
            .attr('fill-opacity', 0);
         svg.selectAll('rect.year' + currentYear)
            .attr('fill-opacity', 0.3);
     })
     // callback to select a year after a mouse click
     // in a rectangle year
     .on("click", function(d) {
        svg.selectAll('rect.year' + currentYear)
           .attr('fill-opacity', 0);
        svg.selectAll('rect.yearoutline' + currentYear)
           .attr('stroke', 'none');
        currentYear = d.getUTCFullYear();
        svg.selectAll('rect.year' + currentYear)
           .attr('fill-opacity', 0.5);
        svg.selectAll('rect.yearoutline' + currentYear)
           .attr('stroke', 'black');
        year_click_callback(currentYear);
    });

    // create the stacked histogram of visits
    g.append("g")
     .selectAll("g")
     .data(stacked(histData))
     .enter().append("g")
     .attr("fill", function(d) { return colors(d.key); })
     .selectAll("rect")
     .data(function(d) { return d; })
     .enter().append("rect")
     .attr("class", function(d) { return "month" + d.data.x1.getMonth(); })
     .attr("x", function(d) {
         return x(d.data.x0);
     })
     .attr("y", function(d) { return y(d[1]); })
     .attr("height", function(d) { return y(d[0]) - y(d[1]); })
     .attr("width", function(d) {
         return x(d.data.x1) - x(d.data.x0) - 1;
     })
     // mouse event callbacks used to show rectangle years
     // but also to show tooltips when hovering the mouse
     // over the histogram bars
     .on("mouseover", function(d) {
         svg.selectAll('rect.year' + d.data.x1.getUTCFullYear())
            .attr('fill-opacity', 0.5);
         tooltip.transition()
                .duration(200)
                .style("opacity", 1);
         var ds = d.data.x1.toISOString().substr(0, 7).split('-');
         var tootltip_text = '<b>' + ds[1] + ' / ' + ds[0] + ':</b><br/>';
         for (var i = 0 ; i < statuses.length ; ++i) {
             var visit_status = statuses[i];
             var nb_visits = d.data[visit_status].length;
             if (nb_visits == 0) continue;
             tootltip_text += nb_visits + ' ' + visit_status + ' visits';
             if (i != statuses.length - 1) tootltip_text += '<br/>';
         }
         tooltip.html(tootltip_text)
                .style("left", d3.event.pageX + 15 + "px")
                .style("top", d3.event.pageY + "px");
     })
     .on("mouseout", function(d) {
         svg.selectAll('rect.year' + d.data.x1.getUTCFullYear())
            .attr('fill-opacity', 0);
         svg.selectAll('rect.year' + currentYear)
            .attr('fill-opacity', 0.3);
         tooltip.transition()
                .duration(500)
                .style("opacity", 0);
     })
     .on("mousemove", function() {
         tooltip.style("left", d3.event.pageX + 15 + "px")
                .style("top", d3.event.pageY + "px");
     })
     // callback to select a year after a mouse click
     // inside a histogram bar
     .on("click", function(d) {
        svg.selectAll('rect.year' + currentYear)
           .attr('fill-opacity', 0);
        svg.selectAll('rect.yearoutline' + currentYear)
           .attr('stroke', 'none');
        currentYear = d.data.x1.getUTCFullYear();
        svg.selectAll('rect.year' + currentYear)
           .attr('fill-opacity', 0.5);
        svg.selectAll('rect.yearoutline' + currentYear)
           .attr('stroke', 'black');
        year_click_callback(currentYear);
    });

    // create one stroke only rectangle by displayed year
    // that will be displayed on top of the histogram when the user has selected a year
    g.append("g")
     .selectAll("rect")
     .data(yearBins)
     .enter().append("rect")
     .attr("class", function(d) {return "yearoutline" + d.getUTCFullYear()})
     .attr("fill", 'none')
     .attr('stroke', function(d) {
         return d.getUTCFullYear() == currentYear ? 'black' : 'none';
     })
     .attr("x", function(d) {
         var date = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
         return x(date);
     })
     .attr("y", 0)
     .attr("height", height)
     .attr("width", function(d) {
         var date = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
         var yearWidth = x(d3.timeYear.offset(date, 1)) - x(date);
         return yearWidth;
     });

    // add x axis with a tick for every 1st day of each year
    var xAxis = g.append("g")
                 .attr("class", "axis")
                 .attr("transform", "translate(0," + height + ")")
                 .call(d3.axisBottom(x)
                         .ticks(d3.timeYear.every(1))
                         .tickFormat(function(d) {
                            return d.getUTCFullYear();
                         }));

    // shift tick labels in order to display them at the middle
    // of each year range
    xAxis.selectAll("text")
         .attr("transform", function(d) {
            var year = d.getUTCFullYear();
            var date = new Date(Date.UTC(year, 0, 1));
            var yearWidth = x(d3.timeYear.offset(date, 1)) - x(date);
             return "translate(" + -yearWidth/2 + ", 0)"
         });

    // add y axis for the number of visits
    g.append("g")
     .attr("class", "axis")
     .call(d3.axisLeft(y).tickValues(yTickValues));

    // add legend for visit statuses
    var legendGroup = g.append("g")
                       .attr("font-family", "sans-serif")
                       .attr("font-size", 10)
                       .attr("text-anchor", "end");

    legendGroup.append('text')
               .attr("x", width+margin.right-5)
               .attr("y", 9.5)
               .attr("dy", "0.32em")
               .text('visit status:');

    var legend = legendGroup.selectAll("g")
                            .data(statuses.slice().reverse())
                            .enter().append("g")
                            .attr("transform", function(d, i) {
                                return "translate(0," + (i+1) * 20 + ")";
                            });

    legend.append("rect")
          .attr("x", width+2*margin.right/3)
          .attr("width", 19)
          .attr("height", 19)
          .attr("fill", colors);

    legend.append("text")
          .attr("x", width+2*margin.right/3 - 5)
          .attr("y", 9.5)
          .attr("dy", "0.32em")
          .text(function(d) { return d; });

    // add text label for the y axis
    g.append("text")
     .attr("transform", "rotate(-90)")
     .attr("y", -margin.left)
     .attr("x", -(height / 2))
     .attr("dy", "1em")
     .style("text-anchor", "middle")
     .text("Number of visits");
}