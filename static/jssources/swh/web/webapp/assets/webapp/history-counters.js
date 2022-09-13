/**
 * Copyright (C) 2019  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import './history-counters.css';

export async function drawHistoryCounterGraph(container, historyData) {

  const d3 = await import(/* webpackChunkName: "d3" */ 'utils/d3');

  // remove previously created histogram and tooltip if any
  d3.select(container).select('svg').remove();
  d3.select(`${container}-tooltip`).remove();

  // histogram size and margins
  let width = 400;
  let height = 300;
  const margin = {top: 20, right: 50, bottom: 70, left: 30};

  // create responsive svg
  const svg = d3.select(container)
                .attr('style',
                      `padding-bottom: ${Math.ceil(height * 100 / width)}%`)
                .append('svg')
                .attr('viewBox', `0 0 ${width} ${height}`);

  // create tooltip div
  const tooltip = d3.select('body')
                    .append('div')
                    .attr('class', 'd3-tooltip')
                    .attr('id', `${container}-tooltip`)
                    .style('opacity', 0);

  // update width and height without margins
  width = width - margin.left - margin.right;
  height = height - margin.top - margin.bottom;

  // Make sure data points are sorted, by x coordinate then y coordinate.
  historyData.sort(function(a, b) {
    return a[0] - b[0] !== 0 ? a[0] - b[0] : a[1] - b[1];
  });

  const firstPoint = historyData[0];
  const lastPoint = historyData[historyData.length - 1];

  // create main svg group element
  const g = svg.append('g')
               .attr('transform', `translate(${margin.left}, ${margin.top})`);

  // create x scale
  const xScale = d3.scaleTime()
                   .rangeRound([0, width])
                   .domain([firstPoint[0], lastPoint[0]])
                   .nice();

  // create y scale
  const yScale = d3.scaleLinear()
                   .range([height, 0])
                   .domain([firstPoint[1], lastPoint[1]])
                   .nice();

  // create line generator
  const line = d3.line()
                 .x(d => xScale(d[0]))
                 .y(d => yScale(d[1]));

  // utility functions
  const dateFormatter = d3.timeFormat('%d %b %Y');
  const valueFormatter = (v) => {
    return d3.format('.3s')(v).replace(/G/, 'B');
  };
  const bisectDate = d3.bisector(d => d[0]).left;

  // add x axis
  g.append('g')
   .attr('class', 'axis')
   .attr('transform', `translate(0, ${height})`)
   .call(
     d3.axisBottom(xScale)
       .ticks(10)
       .tickFormat(dateFormatter)
   )
   .selectAll('text')
   .style('text-anchor', 'end')
   .attr('dx', '-.8em')
   .attr('dy', '.15em')
   .attr('transform', 'rotate(-65)');

  // add y axis
  g.append('g')
   .attr('class', 'axis')
   .attr('transform', `translate(${width}, 0)`)
   .call(
     d3.axisRight(yScale)
       .ticks(10)
       .tickFormat(valueFormatter)
   );

  // add data plot
  g.append('path')
   .datum(historyData)
   .attr('class', 'swh-history-counter-line')
   .attr('d', line);

  // add tooltip
  const focus = g.append('g')
                 .attr('class', 'swh-history-counter-focus')
                 .style('display', 'none');

  focus.append('circle')
       .attr('r', 8);

  g.append('rect')
   .attr('class', 'swh-history-counter-overlay')
   .attr('width', width)
   .attr('height', height)
   .on('mouseover', function(event) {
     focus.style('display', null);
     updateTooltip(event);
     tooltip.transition()
            .duration(200)
            .style('opacity', 1);
   })
   .on('mouseout', () => {
     focus.style('display', 'none');
     tooltip.transition()
            .duration(200)
            .style('opacity', 0);
   })
   .on('mousemove', function(event) {
     updateTooltip(event);
   });

  function updateTooltip(event) {
    const x0 = xScale.invert(d3.pointer(event)[0]);
    const i = bisectDate(historyData, x0, 1);
    if (i >= historyData.length) return;
    const d0 = historyData[i - 1];
    const d1 = historyData[i];
    const d = x0 - d0[0] > d1[0] - x0 ? d1 : d0;
    focus.attr('transform', `translate(${xScale(d[0])}, ${yScale(d[1])})`);
    const tooltipText = `${dateFormatter(d[0])} ${valueFormatter(d[1])}`;
    tooltip.html(tooltipText)
           .style('left', event.pageX + 15 + 'px')
           .style('top', event.pageY + 'px');
  }
}
