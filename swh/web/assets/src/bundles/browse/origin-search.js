/**
 * Copyright (C) 2018  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import {heapsPermute} from 'utils/heaps-permute';
import {handleFetchError} from 'utils/functions';

let originPatterns;
let perPage = 20;
let limit = perPage * 10;
let offset = 0;
let currentData = null;
let inSearch = false;

function fixTableRowsStyle() {
  setTimeout(() => {
    $('#origin-search-results tbody tr').removeAttr('style');
  });
}

function clearOriginSearchResultsTable() {
  $('#origin-search-results tbody tr').remove();
}

function populateOriginSearchResultsTable(data, offset) {
  let localOffset = offset % limit;
  if (data.length > 0) {
    $('#swh-origin-search-results').show();
    $('#swh-no-origins-found').hide();
    clearOriginSearchResultsTable();
    let table = $('#origin-search-results tbody');
    for (let i = localOffset; i < localOffset + perPage && i < data.length; ++i) {
      let elem = data[i];
      let tableRow = '<tr>';
      tableRow += '<td style="width: 120px;">' + elem.type + '</td>';
      let browseUrl = Urls.browse_origin(elem.type, elem.url);
      tableRow += '<td style="white-space: nowrap;"><a href="' + browseUrl + '">' + browseUrl + '</a></td>';
      tableRow += '<td id="visit-status-origin-' + elem.id + '"><i title="Checking visit status" class="fa fa-refresh fa-spin"></i></td>';
      tableRow += '</tr>';
      table.append(tableRow);
      // get async latest visit snapshot and update visit status icon
      let latestSnapshotUrl = Urls.browse_origin_latest_snapshot(elem.id);
      fetch(latestSnapshotUrl, {credentials: 'same-origin'})
        .then(response => response.json())
        .then(data => {
          let originId = elem.id;
          $('#visit-status-origin-' + originId).children().remove();
          if (data) {
            $('#visit-status-origin-' + originId).append('<i title="Origin has at least one full visit by Software Heritage" class="fa fa-check"></i>');
          } else {
            $('#visit-status-origin-' + originId).append('<i title="Origin has not yet been visited by Software Heritage or does not have at least one full visit" class="fa fa-times"></i>');
          }
        });
    }
    fixTableRowsStyle();
  } else {
    $('#swh-origin-search-results').hide();
    $('#swh-no-origins-found').show();
  }
  if (data.length - localOffset < perPage ||
      (data.length < limit && (localOffset + perPage) === data.length)) {
    $('#origins-next-results-button').addClass('disabled');
  } else {
    $('#origins-next-results-button').removeClass('disabled');
  }
  if (offset > 0) {
    $('#origins-prev-results-button').removeClass('disabled');
  } else {
    $('#origins-prev-results-button').addClass('disabled');
  }
  inSearch = false;
  setTimeout(() => {
    window.scrollTo(0, 0);
  });
}

function searchOrigins(patterns, limit, searchOffset, offset) {
  originPatterns = patterns;
  let patternsArray = patterns.trim().replace(/\s+/g, ' ').split(' ');
  let patternsPermut = [];
  heapsPermute(patternsArray, p => patternsPermut.push(p.join('.*')));
  let regex = patternsPermut.join('|');
  let searchUrl = Urls.browse_origin_search(regex) + `?limit=${limit}&offset=${searchOffset}&regexp=true`;

  clearOriginSearchResultsTable();
  $('.swh-loading').addClass('show');
  fetch(searchUrl, {credentials: 'same-origin'})
    .then(handleFetchError)
    .then(response => response.json())
    .then(data => {
      currentData = data;
      if (typeof Storage !== 'undefined') {
        sessionStorage.setItem('last-swh-origin-url-patterns', patterns);
        sessionStorage.setItem('last-swh-origin-search-results', JSON.stringify(data));
        sessionStorage.setItem('last-swh-origin-search-offset', offset);
      }
      $('.swh-loading').removeClass('show');
      populateOriginSearchResultsTable(data, offset);
    })
    .catch(() => {
      $('.swh-loading').removeClass('show');
      inSearch = false;
    });
}

export function initOriginSearch() {
  $(document).ready(() => {
    if (typeof Storage !== 'undefined') {
      originPatterns = sessionStorage.getItem('last-swh-origin-url-patterns');
      let data = sessionStorage.getItem('last-swh-origin-search-results');
      offset = sessionStorage.getItem('last-swh-origin-search-offset');
      if (data) {
        $('#origins-url-patterns').val(originPatterns);
        offset = parseInt(offset);
        populateOriginSearchResultsTable(JSON.parse(data), offset);
      }
    }

    $('#search_origins').submit(event => {
      let patterns = $('#origins-url-patterns').val();
      offset = 0;
      inSearch = true;
      searchOrigins(patterns, limit, offset, offset);
      event.preventDefault();
    });

    $('#origins-next-results-button').click(event => {
      if ($('#origins-next-results-button').hasClass('disabled') || inSearch) {
        return;
      }
      inSearch = true;
      offset += perPage;
      if (!currentData || offset % limit === 0) {
        searchOrigins(originPatterns, limit, offset, offset);
      } else {
        populateOriginSearchResultsTable(currentData, offset);
      }
      event.preventDefault();
    });

    $('#origins-prev-results-button').click(event => {
      if ($('#origins-prev-results-button').hasClass('disabled') || inSearch) {
        return;
      }
      inSearch = true;
      offset -= perPage;
      if (!currentData || (offset > 0 && (offset + perPage) % limit === 0)) {
        searchOrigins(originPatterns, limit, (offset + perPage) - limit, offset);
      } else {
        populateOriginSearchResultsTable(currentData, offset);
      }
      event.preventDefault();
    });

    $(document).on('shown.bs.tab', 'a[data-toggle="tab"]', e => {
      if (e.currentTarget.text.trim() === 'Search') {
        fixTableRowsStyle();
      }
    });
  });
}
