/**
 * Copyright (C) 2018  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import {createVisitsHistogram} from './visits-histogram';
import {updateCalendar} from './visits-calendar';
import './visits-reporting.css';

// will hold all visits
let allVisits;
// will hold filtered visits to display
let filteredVisits;
// will hold currently displayed year
let currentYear;

// function to gather full visits
function filterFullVisits(differentSnapshots) {
  let filteredVisits = [];
  for (let i = 0; i < allVisits.length; ++i) {
    if (allVisits[i].status !== 'full') continue;
    if (!differentSnapshots) {
      filteredVisits.push(allVisits[i]);
    } else if (filteredVisits.length === 0) {
      filteredVisits.push(allVisits[i]);
    } else {
      let lastVisit = filteredVisits[filteredVisits.length - 1];
      if (allVisits[i].snapshot !== lastVisit.snapshot) {
        filteredVisits.push(allVisits[i]);
      }
    }
  }
  return filteredVisits;
}

// function to update the visits list view based on the selected year
function updateVisitsList(year) {
  $('#swh-visits-list').children().remove();
  let visitsByYear = [];
  for (let i = 0; i < filteredVisits.length; ++i) {
    if (filteredVisits[i].date.getUTCFullYear() === year) {
      visitsByYear.push(filteredVisits[i]);
    }
  }
  let visitsCpt = 0;
  let nbVisitsByRow = 4;
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

// callback when the user only wants to see full visits pointing
// to different snapshots (default)
export function showFullVisitsDifferentSnapshots(event) {
  filteredVisits = filterFullVisits(true);
  updateDisplayedVisits();
}

// callback when the user only wants to see full visits
export function showFullVisits(event) {
  filteredVisits = filterFullVisits(false);
  updateDisplayedVisits();
}

// callback when the user wants to see all visits (including partial, ongoing and failed ones)
export function showAllVisits(event) {
  filteredVisits = allVisits;
  updateDisplayedVisits();
}

export function initVisitsReporting(visits) {
  $(document).ready(() => {
    allVisits = visits;
    // process input visits
    let firstFullVisit;
    allVisits.forEach((v, i) => {
      // Turn Unix epoch into Javascript Date object
      v.date = new Date(Math.floor(v.date * 1000));
      let visitLink = '<a class="swh-visit-icon swh-visit-' + v.status + '" href="' + v.url + '">' + v.formatted_date + '</a>';
      if (v.status === 'full') {
        if (!firstFullVisit) {
          firstFullVisit = v;
          $('#swh-first-full-visit').append($(visitLink));
          if (allVisits.length === 1) {
            $('#swh-last-full-visit')[0].innerHTML = visitLink;
          }
        } else {
          $('#swh-last-full-visit')[0].innerHTML = visitLink;
        }
      }
      if (i === allVisits.length - 1) {
        $('#swh-last-visit').append($(visitLink));
      }
    });

    // display full visits pointing to different snapshots by default
    showFullVisitsDifferentSnapshots();
  });

}
