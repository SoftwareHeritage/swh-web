/**
 * Copyright (C) 2018  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import {heapsPermute} from 'utils/heaps-permute';
import {handleFetchError} from 'utils/functions';

let originPatterns;
let perPage = 100;
let limit = perPage * 2;
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
    $('#swh-no-result').hide();
    clearOriginSearchResultsTable();
    let table = $('#origin-search-results tbody');
    for (let i = localOffset; i < localOffset + perPage && i < data.length; ++i) {
      let elem = data[i];
      let browseUrl = Urls.browse_origin(elem.url);
      let tableRow = `<tr id="origin-${elem.id}" class="swh-search-result-entry swh-tr-hover-highlight">`;
      tableRow += `<td style="width: 120px;">${elem.type}</td>`;
      tableRow += `<td style="white-space: nowrap;"><a href="${encodeURI(browseUrl)}">${encodeURI(elem.url)}</a></td>`;
      tableRow += `<td id="visit-status-origin-${elem.id}"><i title="Checking visit status" class="fa fa-refresh fa-spin"></i></td>`;
      tableRow += '</tr>';
      table.append(tableRow);
      // get async latest visit snapshot and update visit status icon
      let latestSnapshotUrl = Urls.browse_origin_latest_snapshot(elem.id);
      fetch(latestSnapshotUrl)
        .then(response => response.json())
        .then(data => {
          let originId = elem.id;
          $(`#visit-status-origin-${originId}`).children().remove();
          if (data) {
            $(`#visit-status-origin-${originId}`).append('<i title="Origin has at least one full visit by Software Heritage" class="fa fa-check"></i>');
          } else {
            $(`#visit-status-origin-${originId}`).append('<i title="Origin has not yet been visited by Software Heritage or does not have at least one full visit" class="fa fa-times"></i>');
            if ($('#swh-filter-empty-visits').prop('checked')) {
              $(`#origin-${originId}`).remove();
            }
          }
        });
    }
    fixTableRowsStyle();
  } else {
    $('#swh-origin-search-results').hide();
    $('#swh-no-result').text('No origins matching the search criteria were found.');
    $('#swh-no-result').show();
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

function escapeStringRegexp(str) {
  let matchOperatorsRe = /[|\\{}()[\]^$+*?.]/g;
  return str.replace(matchOperatorsRe, '\\\\\\$&');
}

function searchOrigins(patterns, limit, searchOffset, offset) {
  let baseSearchUrl;
  let searchMetadata = $('#swh-search-origin-metadata').prop('checked');
  if (searchMetadata) {
    baseSearchUrl = Urls.api_origin_metadata_search() + `?fulltext=${patterns}`;
  } else {
    originPatterns = patterns;
    let patternsArray = patterns.trim().replace(/\s+/g, ' ').split(' ');
    for (let i = 0; i < patternsArray.length; ++i) {
      patternsArray[i] = escapeStringRegexp(patternsArray[i]);
    }
    // url length must be less than 4096 for modern browsers
    // assuming average word length, 6 is max patternArray.length
    if (patternsArray.length < 7) {
      let patternsPermut = [];
      heapsPermute(patternsArray, p => patternsPermut.push(p.join('.*')));
      let regex = patternsPermut.join('|');
      baseSearchUrl = Urls.browse_origin_search(regex) + `?regexp=true`;
    } else {
      baseSearchUrl = Urls.browse_origin_search(patternsArray.join('.*')) + `?regexp=true`;
    }
  }

  let withVisit = $('#swh-search-origins-with-visit').prop('checked');
  let searchUrl = baseSearchUrl + `&limit=${limit}&offset=${searchOffset}&with_visit=${withVisit}`;

  clearOriginSearchResultsTable();
  $('.swh-loading').addClass('show');
  fetch(searchUrl)
    .then(handleFetchError)
    .then(response => response.json())
    .then(data => {
      currentData = data;
      $('.swh-loading').removeClass('show');
      populateOriginSearchResultsTable(data, offset);
    })
    .catch(response => {
      $('.swh-loading').removeClass('show');
      inSearch = false;
      $('#swh-origin-search-results').hide();
      $('#swh-no-result').text(`Error ${response.status}: ${response.statusText}`);
      $('#swh-no-result').show();
    });
}

function doSearch() {
  $('#swh-no-result').hide();
  let patterns = $('#origins-url-patterns').val();
  offset = 0;
  inSearch = true;
  // first try to resolve a swh persistent identifier
  let resolvePidUrl = Urls.api_resolve_swh_pid(patterns);
  fetch(resolvePidUrl)
    .then(handleFetchError)
    .then(response => response.json())
    .then(data => {
      // pid has been successfully resolved,
      // so redirect to browse page
      window.location = data.browse_url;
    })
    .catch(response => {
      // pid resolving failed
      if (patterns.startsWith('swh:')) {
        // display a useful error message if the input
        // looks like a swh pid
        response.json().then(data => {
          $('#swh-origin-search-results').hide();
          $('.swh-search-pagination').hide();
          $('#swh-no-result').text(data.reason);
          $('#swh-no-result').show();
        });
      } else {
        // otherwise, proceed with origins search
        $('#swh-origin-search-results').show();
        $('.swh-search-pagination').show();
        searchOrigins(patterns, limit, offset, offset);
      }
    });
}

export function initOriginSearch() {
  $(document).ready(() => {
    $('#swh-search-origins').submit(event => {
      event.preventDefault();
      let patterns = $('#origins-url-patterns').val().trim();
      let withVisit = $('#swh-search-origins-with-visit').prop('checked');
      let withContent = $('#swh-filter-empty-visits').prop('checked');
      let searchMetadata = $('#swh-search-origin-metadata').prop('checked');
      let queryParameters = '?q=' + encodeURIComponent(patterns);
      if (withVisit) {
        queryParameters += '&with_visit';
      }
      if (withContent) {
        queryParameters += '&with_content';
      }
      if (searchMetadata) {
        queryParameters += '&search_metadata';
      }
      // Update the url, triggering page reload and effective search
      window.location.search = queryParameters;
    });

    $('#origins-next-results-button').click(event => {
      if ($('#origins-next-results-button').hasClass('disabled') || inSearch) {
        return;
      }
      inSearch = true;
      offset += perPage;
      if (!currentData || (offset >= limit && offset % limit === 0)) {
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

    let urlParams = new URLSearchParams(window.location.search);
    let query = urlParams.get('q');
    let withVisit = urlParams.has('with_visit');
    let withContent = urlParams.has('with_content');
    let searchMetadata = urlParams.has('search_metadata');
    if (query) {
      $('#origins-url-patterns').val(query);
      $('#swh-search-origins-with-visit').prop('checked', withVisit);
      $('#swh-filter-empty-visits').prop('checked', withContent);
      $('#swh-search-origin-metadata').prop('checked', searchMetadata);
      doSearch();
    }
  });
}
