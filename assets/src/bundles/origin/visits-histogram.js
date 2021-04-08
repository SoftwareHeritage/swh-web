/**
 * Copyright (C) 2018-2019  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

// Creation of a stacked histogram with D3.js for software origin visits history
// Parameters description:
//  - container: selector for the div that will contain the histogram
//  - visitsData: raw swh origin visits data
//  - currentYear: the visits year to display by default
//  - yearClickCallback: callback when the user selects a year through the histogram

export async function createVisitsHistogram(container, visitsData, currentYear, yearClickCallback) {

  const d3 = await import(/* webpackChunkName: "d3" */ 'utils/d3');

  // remove previously created histogram and tooltip if any
  d3.select(container).select('svg').remove();
  d3.select('div.d3-tooltip').remove();

  // histogram size and margins
  let width = 1000;
  let height = 200;
  let margin = {top: 20, right: 80, bottom: 30, left: 50};

  // create responsive svg
  let svg = d3.select(container)
    .attr('style',
          'padding-bottom: ' + Math.ceil(height * 100 / width) + '%')
    .append('svg')
    .attr('viewBox', '0 0 ' + width + ' ' + height);

  // create tooltip div
  let tooltip = d3.select('body')
    .append('div')
    .attr('class', 'd3-tooltip')
    .style('opacity', 0);

  // update width and height without margins
  width = width - margin.left - margin.right;
  height = height - margin.top - margin.bottom;

  // create main svg group element
  let g = svg.append('g').attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

  // create x scale
  let x = d3.scaleTime().rangeRound([0, width]);

  // create y scale
  let y = d3.scaleLinear().range([height, 0]);

  // create ordinal colorscale mapping visit status
  let colors = d3.scaleOrdinal()
    .domain(['full', 'partial', 'failed', 'ongoing'])
    .range(['#008000', '#edc344', '#ff0000', '#0000ff']);

  // first swh crawls were made in 2015
  let startYear = 2015;
  // set latest display year as the current one
  let now = new Date();
  let endYear = now.getUTCFullYear() + 1;
  let monthExtent = [new Date(Date.UTC(startYear, 0, 1)), new Date(Date.UTC(endYear, 0, 1))];

  // create months bins based on setup extent
  let monthBins = d3.timeMonths(d3.timeMonth.offset(monthExtent[0], -1), monthExtent[1]);
  // create years bins based on setup extent
  let yearBins = d3.timeYears(monthExtent[0], monthExtent[1]);

  // set x scale domain
  x.domain(d3.extent(monthBins));

  // use D3 histogram layout to create a function that will bin the visits by month
  let binByMonth = d3.histogram()
    .value(d => d.date)
    .domain(x.domain())
    .thresholds(monthBins);

  // use D3 nest function to group the visits by status
  let visitsByStatus = d3.groups(visitsData, d => d['status'])
    .sort((a, b) => d3.ascending(a[0], b[0]));

  // prepare data in order to be able to stack visit statuses by month
  let statuses = [];
  let histData = [];
  for (let i = 0; i < monthBins.length; ++i) {
    histData[i] = {};
  }
  visitsByStatus.forEach(entry => {
    statuses.push(entry[0]);
    let monthsData = binByMonth(entry[1]);
    for (let i = 0; i < monthsData.length; ++i) {
      histData[i]['x0'] = monthsData[i]['x0'];
      histData[i]['x1'] = monthsData[i]['x1'];
      histData[i][entry[0]] = monthsData[i];
    }
  });

  // create function to stack visits statuses by month
  let stacked = d3.stack()
    .keys(statuses)
    .value((d, key) => d[key].length);

  // compute the maximum amount of visits by month
  let yMax = d3.max(histData, d => {
    let total = 0;
    for (let i = 0; i < statuses.length; ++i) {
      total += d[statuses[i]].length;
    }
    return total;
  });

  // set y scale domain
  y.domain([0, yMax]);

  // compute ticks values for the y axis
  let step = 5;
  let yTickValues = [];
  for (let i = 0; i <= yMax / step; ++i) {
    yTickValues.push(i * step);
  }
  if (yTickValues.length === 0) {
    for (let i = 0; i <= yMax; ++i) {
      yTickValues.push(i);
    }
  } else if (yMax % step !== 0) {
    yTickValues.push(yMax);
  }

  // add histogram background grid
  g.append('g')
    .attr('class', 'grid')
    .call(d3.axisLeft(y)
      .tickValues(yTickValues)
      .tickSize(-width)
      .tickFormat(''));

  // create one fill only rectangle by displayed year
  // each rectangle will be made visible when hovering the mouse over a year range
  // user will then be able to select a year by clicking in the rectangle

  g.append('g')
    .selectAll('rect')
    .data(yearBins)
    .enter().append('rect')
    .attr('class', d => 'year' + d.getUTCFullYear())
    .attr('fill', 'red')
    .attr('fill-opacity', d => d.getUTCFullYear() === currentYear ? 0.3 : 0)
    .attr('stroke', 'none')
    .attr('x', d => {
      let date = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
      return x(date);
    })
    .attr('y', 0)
    .attr('height', height)
    .attr('width', d => {
      let date = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
      let yearWidth = x(d3.timeYear.offset(date, 1)) - x(date);
      return yearWidth;
    })
    // mouse event callbacks used to show rectangle years
    // when hovering the mouse over the histograms
    .on('mouseover', (event, d) => {
      svg.selectAll('rect.year' + d.getUTCFullYear())
        .attr('fill-opacity', 0.5);
    })
    .on('mouseout', (event, d) => {
      svg.selectAll('rect.year' + d.getUTCFullYear())
        .attr('fill-opacity', 0);
      svg.selectAll('rect.year' + currentYear)
        .attr('fill-opacity', 0.3);
    })
    // callback to select a year after a mouse click
    // in a rectangle year
    .on('click', (event, d) => {
      svg.selectAll('rect.year' + currentYear)
        .attr('fill-opacity', 0);
      svg.selectAll('rect.yearoutline' + currentYear)
        .attr('stroke', 'none');
      currentYear = d.getUTCFullYear();
      svg.selectAll('rect.year' + currentYear)
        .attr('fill-opacity', 0.5);
      svg.selectAll('rect.yearoutline' + currentYear)
        .attr('stroke', 'black');
      yearClickCallback(currentYear);
    });

  // create the stacked histogram of visits
  g.append('g')
    .selectAll('g')
    .data(stacked(histData))
    .enter().append('g')
    .attr('fill', d => colors(d.key))
    .selectAll('rect')
    .data(d => d)
    .enter().append('rect')
    .attr('class', d => 'month' + d.data.x1.getMonth())
    .attr('x', d => x(d.data.x0))
    .attr('y', d => y(d[1]))
    .attr('height', d => y(d[0]) - y(d[1]))
    .attr('width', d => x(d.data.x1) - x(d.data.x0) - 1)
    // mouse event callbacks used to show rectangle years
    // but also to show tooltip when hovering the mouse
    // over the histogram bars
    .on('mouseover', (event, d) => {
      svg.selectAll('rect.year' + d.data.x1.getUTCFullYear())
        .attr('fill-opacity', 0.5);
      tooltip.transition()
        .duration(200)
        .style('opacity', 1);
      let ds = d.data.x1.toISOString().substr(0, 7).split('-');
      let tooltipText = '<b>' + ds[1] + ' / ' + ds[0] + ':</b><br/>';
      for (let i = 0; i < statuses.length; ++i) {
        let visitStatus = statuses[i];
        let nbVisits = d.data[visitStatus].length;
        if (nbVisits === 0) continue;
        tooltipText += nbVisits + ' ' + visitStatus + ' visits';
        if (i !== statuses.length - 1) tooltipText += '<br/>';
      }
      tooltip.html(tooltipText)
        .style('left', event.pageX + 15 + 'px')
        .style('top', event.pageY + 'px');
    })
    .on('mouseout', (event, d) => {
      svg.selectAll('rect.year' + d.data.x1.getUTCFullYear())
        .attr('fill-opacity', 0);
      svg.selectAll('rect.year' + currentYear)
        .attr('fill-opacity', 0.3);
      tooltip.transition()
        .duration(500)
        .style('opacity', 0);
    })
    .on('mousemove', (event) => {
      tooltip.style('left', event.pageX + 15 + 'px')
        .style('top', event.pageY + 'px');
    })
    // callback to select a year after a mouse click
    // inside a histogram bar
    .on('click', (event, d) => {
      svg.selectAll('rect.year' + currentYear)
        .attr('fill-opacity', 0);
      svg.selectAll('rect.yearoutline' + currentYear)
        .attr('stroke', 'none');
      currentYear = d.data.x1.getUTCFullYear();
      svg.selectAll('rect.year' + currentYear)
        .attr('fill-opacity', 0.5);
      svg.selectAll('rect.yearoutline' + currentYear)
        .attr('stroke', 'black');
      yearClickCallback(currentYear);
    });

  // create one stroke only rectangle by displayed year
  // that will be displayed on top of the histogram when the user has selected a year
  g.append('g')
    .selectAll('rect')
    .data(yearBins)
    .enter().append('rect')
    .attr('class', d => 'yearoutline' + d.getUTCFullYear())
    .attr('fill', 'none')
    .attr('stroke', d => d.getUTCFullYear() === currentYear ? 'black' : 'none')
    .attr('x', d => {
      let date = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
      return x(date);
    })
    .attr('y', 0)
    .attr('height', height)
    .attr('width', d => {
      let date = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
      let yearWidth = x(d3.timeYear.offset(date, 1)) - x(date);
      return yearWidth;
    });

  // add x axis with a tick for every 1st day of each year
  let xAxis = g.append('g')
    .attr('class', 'axis')
    .attr('transform', 'translate(0,' + height + ')')
    .call(
      d3.axisBottom(x)
        .ticks(d3.timeYear.every(1))
        .tickFormat(d => d.getUTCFullYear())
    );

  // shift tick labels in order to display them at the middle
  // of each year range
  xAxis.selectAll('text')
    .attr('transform', d => {
      let year = d.getUTCFullYear();
      let date = new Date(Date.UTC(year, 0, 1));
      let yearWidth = x(d3.timeYear.offset(date, 1)) - x(date);
      return 'translate(' + -yearWidth / 2 + ', 0)';
    });

  // add y axis for the number of visits
  g.append('g')
    .attr('class', 'axis')
    .call(d3.axisLeft(y).tickValues(yTickValues));

  // add legend for visit statuses
  let legendGroup = g.append('g')
    .attr('font-family', 'sans-serif')
    .attr('font-size', 10)
    .attr('text-anchor', 'end');

  legendGroup.append('text')
    .attr('x', width + margin.right - 5)
    .attr('y', 9.5)
    .attr('dy', '0.32em')
    .text('visit status:');

  let legend = legendGroup.selectAll('g')
    .data(statuses.slice().reverse())
    .enter().append('g')
    .attr('transform', (d, i) => 'translate(0,' + (i + 1) * 20 + ')');

  legend.append('rect')
    .attr('x', width + 2 * margin.right / 3)
    .attr('width', 19)
    .attr('height', 19)
    .attr('fill', colors);

  legend.append('text')
    .attr('x', width + 2 * margin.right / 3 - 5)
    .attr('y', 9.5)
    .attr('dy', '0.32em')
    .text(d => d);

  // add text label for the y axis
  g.append('text')
    .attr('transform', 'rotate(-90)')
    .attr('y', -margin.left)
    .attr('x', -(height / 2))
    .attr('dy', '1em')
    .style('text-anchor', 'middle')
    .text('Number of visits');
}
