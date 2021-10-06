/**
 * Copyright (C) 2018-2021  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import Calendar from 'js-year-calendar';
import 'js-year-calendar/dist/js-year-calendar.css';
import hexRgb from 'hex-rgb';

import {visitStatusColor} from './utils';

const minSize = 15;
const maxSize = 28;
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
    const date = new Date(filteredVisits[i]['date']);
    date.setHours(0, 0, 0, 0);
    const dateStr = date.toDateString();
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
      const dateStr = date.toDateString();
      const nbVisits = visitsByDate[dateStr].length;
      let t = nbVisits / maxNbVisitsByDate;
      if (maxNbVisitsByDate === 1) {
        t = 0;
      }
      const size = minSize + t * (maxSize - minSize);
      const offsetX = (maxSize - size) / 2 - parseInt($(element).css('padding-left'));
      const offsetY = (maxSize - size) / 2 - parseInt($(element).css('padding-top')) + 1;
      const cellWrapper = $('<div></div>');
      cellWrapper.css('position', 'relative');
      const dayNumber = $('<div></div>');
      dayNumber.text($(element).text());
      const circle = $('<div></div>');
      const color = {red: 0, green: 0, blue: 0, alpha: 0.4};
      for (let i = 0; i < nbVisits; ++i) {
        const visit = visitsByDate[dateStr][i];
        const visitColor = hexRgb(visitStatusColor[visit.status]);
        color.red += visitColor.red;
        color.green += visitColor.green;
        color.blue += visitColor.blue;
      }
      color.red /= nbVisits;
      color.green /= nbVisits;
      color.blue /= nbVisits;
      circle.css('background-color', `rgba(${color.red}, ${color.green}, ${color.blue}, ${color.alpha})`);
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
      const dateStr = e.date.toDateString();
      if (visitsByDate.hasOwnProperty(dateStr)) {

        const visits = visitsByDate[dateStr];
        let content = '<div><h6>' + e.date.toDateString() + '</h6></div>';
        content += '<ul class="swh-list-unstyled">';
        for (let i = 0; i < visits.length; ++i) {
          const visitTime = visits[i].formatted_date.substr(visits[i].formatted_date.indexOf(',') + 2);
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
