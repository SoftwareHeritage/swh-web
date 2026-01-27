/**
 * Copyright (C) 2018-2026  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import {createVisitsHistogram} from './visits-histogram';
import {updateCalendar} from './visits-calendar';
import './visits-reporting.css';

// will hold filtered visits to display
let filteredVisits;
// will hold currently displayed year
let currentYear;

// function to update the visits list view based on the selected year
function updateVisitsList(year) {
  $('#swh-visits-list').children().remove();
  const visitsByYear = [];
  for (let i = 0; i < filteredVisits.length; ++i) {
    if (filteredVisits[i].date.getUTCFullYear() === year) {
      visitsByYear.push(filteredVisits[i]);
    }
  }
  let visitsCpt = 0;
  const nbVisitsByRow = 4;
  let visitsListHtml = '<div class="swh-visits-list-row">';
  for (let i = 0; i < visitsByYear.length; ++i) {
    if (visitsCpt > 0 && visitsCpt % nbVisitsByRow === 0) {
      visitsListHtml += '</div><div class="swh-visits-list-row">';
    }
    visitsListHtml += '<div class="swh-visits-list-column" style="width: ' + 100 / nbVisitsByRow + '%;">';
    visitsListHtml += '<a class="swh-visit-icon swh-visit-' + visitsByYear[i].status + '" title="' + visitsByYear[i].status +
                        ' visit" href="' + visitsByYear[i].url + '">' + visitsByYear[i].formatted_date + '</a>';
    visitsListHtml += '</div>';
    ++visitsCpt;
  }
  visitsListHtml += '</div>';
  $('#swh-visits-list').append($(visitsListHtml));
}

function yearChangedCalendar(year) {
  currentYear = year;
  updateVisitsList(year);
  createVisitsHistogram('.d3-wrapper', filteredVisits, currentYear, yearClickedTimeline);
}

// callback when the user selects a year through the visits histogram
function yearClickedTimeline(year) {
  currentYear = year;
  updateCalendar(year, filteredVisits, yearChangedCalendar);
  updateVisitsList(year);
}

// function to update the visits views (histogram, calendar, list)
function updateDisplayedVisits() {
  if (filteredVisits.length === 0) {
    return;
  }
  if (!currentYear) {
    currentYear = filteredVisits[filteredVisits.length - 1].date.getUTCFullYear();
  }
  createVisitsHistogram('.d3-wrapper', filteredVisits, currentYear, yearClickedTimeline);
  updateCalendar(currentYear, filteredVisits, yearChangedCalendar);
  updateVisitsList(currentYear);
}

// bootstrap 5 popovers on calendar days have display issues after dynamically updating calendar
// so we refresh the page instead when changing visits filter
export function reloadPage() {
  location.reload();
}

export function initVisitsReporting(visits) {
  $(() => {
    filteredVisits = visits;
    // process input visits
    filteredVisits.forEach((v, i) => {
      // Turn Unix epoch into Javascript Date object
      v.date = new Date(Math.floor(v.date * 1000));
    });

    updateDisplayedVisits();
  });

}
