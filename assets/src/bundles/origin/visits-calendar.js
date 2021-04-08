/**
 * Copyright (C) 2018-2019  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import Calendar from 'js-year-calendar';
import 'js-year-calendar/dist/js-year-calendar.css';

let minSize = 15;
let maxSize = 28;
let currentPopover = null;
let visitsByDate = {};

function closePopover() {
  if (currentPopover) {
    $(currentPopover).popover('dispose');
    currentPopover = null;
  }
}

// function to update the visits calendar view based on the selected year
export function updateCalendar(year, filteredVisits, yearClickedCallback) {
  visitsByDate = {};
  let maxNbVisitsByDate = 0;
  let minDate, maxDate;
  for (let i = 0; i < filteredVisits.length; ++i) {
    filteredVisits[i]['startDate'] = filteredVisits[i]['date'];
    filteredVisits[i]['endDate'] = filteredVisits[i]['startDate'];
    let date = new Date(filteredVisits[i]['date']);
    date.setHours(0, 0, 0, 0);
    let dateStr = date.toDateString();
    if (!visitsByDate.hasOwnProperty(dateStr)) {
      visitsByDate[dateStr] = [filteredVisits[i]];
    } else {
      visitsByDate[dateStr].push(filteredVisits[i]);
    }
    maxNbVisitsByDate = Math.max(maxNbVisitsByDate, visitsByDate[dateStr].length);
    if (i === 0) {
      minDate = maxDate = date;
    } else {
      if (date.getTime() < minDate.getTime()) {
        minDate = date;
      }
      if (date.getTime() > maxDate.getTime()) {
        maxDate = date;
      }
    }
  }

  closePopover();

  new Calendar('#swh-visits-calendar', {
    dataSource: filteredVisits,
    style: 'custom',
    minDate: minDate,
    maxDate: maxDate,
    startYear: year,
    renderEnd: e => yearClickedCallback(e.currentYear),
    customDataSourceRenderer: (element, date, events) => {
      let dateStr = date.toDateString();
      let nbVisits = visitsByDate[dateStr].length;
      let t = nbVisits / maxNbVisitsByDate;
      if (maxNbVisitsByDate === 1) {
        t = 0;
      }
      let size = minSize + t * (maxSize - minSize);
      let offsetX = (maxSize - size) / 2 - parseInt($(element).css('padding-left'));
      let offsetY = (maxSize - size) / 2 - parseInt($(element).css('padding-top')) + 1;
      let cellWrapper = $('<div></div>');
      cellWrapper.css('position', 'relative');
      let dayNumber = $('<div></div>');
      dayNumber.text($(element).text());
      let circle = $('<div></div>');
      let r = 0;
      let g = 0;
      for (let i = 0; i < nbVisits; ++i) {
        let visit = visitsByDate[dateStr][i];
        if (visit.status === 'full') {
          g += 255;
        } else if (visit.status === 'partial') {
          r += 255;
          g += 255;
        } else {
          r += 255;
        }
      }
      r /= nbVisits;
      g /= nbVisits;
      circle.css('background-color', 'rgba(' + r + ', ' + g + ', 0, 0.3)');
      circle.css('width', size + 'px');
      circle.css('height', size + 'px');
      circle.css('border-radius', size + 'px');
      circle.css('position', 'absolute');
      circle.css('top', offsetY + 'px');
      circle.css('left', offsetX + 'px');
      cellWrapper.append(dayNumber);
      cellWrapper.append(circle);
      $(element)[0].innerHTML = $(cellWrapper)[0].outerHTML;
    },
    mouseOnDay: e => {
      if (currentPopover !== e.element) {
        closePopover();
      }
      let dateStr = e.date.toDateString();
      if (visitsByDate.hasOwnProperty(dateStr)) {

        let visits = visitsByDate[dateStr];
        let content = '<div><h6>' + e.date.toDateString() + '</h6></div>';
        content += '<ul class="swh-list-unstyled">';
        for (let i = 0; i < visits.length; ++i) {
          let visitTime = visits[i].formatted_date.substr(visits[i].formatted_date.indexOf(',') + 2);
          content += '<li><a class="swh-visit-icon swh-visit-' + visits[i].status + '" title="' + visits[i].status +
                     ' visit" href="' + visits[i].url + '">' + visitTime + '</a></li>';
        }
        content += '</ul>';

        $(e.element).popover({
          trigger: 'manual',
          container: 'body',
          html: true,
          content: content
        }).on('mouseleave', () => {
          if (!$('.popover:hover').length) {
            // close popover when leaving day in calendar
            // except if the pointer is hovering it
            closePopover();
          }
        });

        $(e.element).on('shown.bs.popover', () => {
          $('.popover').mouseleave(() => {
            // close popover when pointer leaves it
            closePopover();
          });
        });

        $(e.element).popover('show');
        currentPopover = e.element;
      }
    }
  });
  $('#swh-visits-calendar.calendar table td').css('width', maxSize + 'px');
  $('#swh-visits-calendar.calendar table td').css('height', maxSize + 'px');
  $('#swh-visits-calendar.calendar table td').css('padding', '0px');
}
