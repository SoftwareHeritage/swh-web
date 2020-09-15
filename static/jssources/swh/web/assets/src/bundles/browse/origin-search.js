/**
 * Copyright (C) 2018-2020  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import {handleFetchError} from 'utils/functions';

const limit = 100;
let linksPrev = [];
let linkNext = null;
let linkCurrent = null;
let inSearch = false;

function parseLinkHeader(s) {
  let re = /<(.+)>; rel="next"/;
  return s.match(re)[1];
}

function fixTableRowsStyle() {
  setTimeout(() => {
    $('#origin-search-results tbody tr').removeAttr('style');
  });
}

function clearOriginSearchResultsTable() {
  $('#origin-search-results tbody tr').remove();
}

function populateOriginSearchResultsTable(origins) {
  if (origins.length > 0) {
    $('#swh-origin-search-results').show();
    $('#swh-no-result').hide();
    clearOriginSearchResultsTable();
    let table = $('#origin-search-results tbody');
    for (let [i, origin] of origins.entries()) {
      let browseUrl = `${Urls.browse_origin()}?origin_url=${encodeURIComponent(origin.url)}`;
      let tableRow =
        `<tr id="origin-${i}" class="swh-search-result-entry swh-tr-hover-highlight">`;
      tableRow +=
        `<td id="visit-type-origin-${i}" style="width: 120px;">` +
        '<i title="Checking software origin type" class="mdi mdi-sync mdi-spin mdi-fw"></i>' +
        'Checking</td>';
      tableRow +=
        '<td style="white-space: nowrap;">' +
        `<a href="${browseUrl}">${origin.url}</a></td>`;
      tableRow +=
        `<td class="swh-visit-status" id="visit-status-origin-${i}">` +
        '<i title="Checking archiving status" class="mdi mdi-sync mdi-spin mdi-fw"></i>' +
        'Checking</td>';
      tableRow += '</tr>';
      table.append(tableRow);
      // get async latest visit snapshot and update visit status icon
      let latestSnapshotUrl = Urls.api_1_origin_visit_latest(origin.url);
      latestSnapshotUrl += '?require_snapshot=true';
      fetch(latestSnapshotUrl)
        .then(response => response.json())
        .then(data => {
          $(`#visit-type-origin-${i}`).html(data.type);
          $(`#visit-status-origin-${i}`).children().remove();
          if (data) {
            $(`#visit-status-origin-${i}`).html(
              '<i title="Software origin has been archived by Software Heritage" ' +
              'class="mdi mdi-check-bold mdi-fw"></i>Archived');
          } else {
            $(`#visit-status-origin-${i}`).html(
              '<i title="Software origin archival by Software Heritage is pending" ' +
              'class="mdi mdi-close-thick mdi-fw"></i>Pending archival');
            if ($('#swh-filter-empty-visits').prop('checked')) {
              $(`#origin-${i}`).remove();
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

  if (linkNext === null) {
    $('#origins-next-results-button').addClass('disabled');
  } else {
    $('#origins-next-results-button').removeClass('disabled');
  }

  if (linksPrev.length === 0) {
    $('#origins-prev-results-button').addClass('disabled');
  } else {
    $('#origins-prev-results-button').removeClass('disabled');
  }

  inSearch = false;
  setTimeout(() => {
    window.scrollTo(0, 0);
  });
}

function searchOriginsFirst(searchQueryText, limit) {
  let baseSearchUrl;
  let searchMetadata = $('#swh-search-origin-metadata').prop('checked');
  if (searchMetadata) {
    baseSearchUrl = new URL(Urls.api_1_origin_metadata_search(), window.location);
    baseSearchUrl.searchParams.append('fulltext', searchQueryText);
  } else {
    baseSearchUrl = new URL(Urls.api_1_origin_search(searchQueryText), window.location);
  }

  let withVisit = $('#swh-search-origins-with-visit').prop('checked');
  baseSearchUrl.searchParams.append('limit', limit);
  baseSearchUrl.searchParams.append('with_visit', withVisit);
  let searchUrl = baseSearchUrl.toString();
  searchOrigins(searchUrl);
}

function searchOrigins(searchUrl) {
  clearOriginSearchResultsTable();
  $('.swh-loading').addClass('show');
  let response = fetch(searchUrl)
    .then(handleFetchError)
    .then(resp => {
      response = resp;
      return response.json();
    })
    .then(data => {
      // Save link to the current results page
      linkCurrent = searchUrl;
      // Save link to the next results page.
      linkNext = null;
      if (response.headers.has('Link')) {
        let parsedLink = parseLinkHeader(response.headers.get('Link'));
        if (parsedLink !== undefined) {
          linkNext = parsedLink;
        }
      }
      // prevLinks is updated by the caller, which is the one to know if
      // we're going forward or backward in the pages.

      $('.swh-loading').removeClass('show');
      populateOriginSearchResultsTable(data);
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
  let searchQueryText = $('#origins-url-patterns').val();
  inSearch = true;
  if (searchQueryText.startsWith('swh:')) {
    // searchQueryText may be a PID so sending search queries to PID resolve endpoint
    let resolveSWHIDUrl = Urls.api_1_resolve_swhid(searchQueryText);
    fetch(resolveSWHIDUrl)
      .then(handleFetchError)
      .then(response => response.json())
      .then(data => {
        // SWHID has been successfully resolved,
        // so redirect to browse page
        window.location = data.browse_url;
      })
      .catch(response => {
        // display a useful error message if the input
        // looks like a SWHID
        response.json().then(data => {
          $('#swh-origin-search-results').hide();
          $('.swh-search-pagination').hide();
          $('#swh-no-result').text(data.reason);
          $('#swh-no-result').show();
        });

      });
  } else {
    // otherwise, proceed with origins search
    $('#swh-origin-search-results').show();
    $('.swh-search-pagination').show();
    searchOriginsFirst(searchQueryText, limit);
  }
}

export function initOriginSearch() {
  $(document).ready(() => {
    $('#swh-search-origins').submit(event => {
      event.preventDefault();
      let searchQueryText = $('#origins-url-patterns').val().trim();
      let withVisit = $('#swh-search-origins-with-visit').prop('checked');
      let withContent = $('#swh-filter-empty-visits').prop('checked');
      let searchMetadata = $('#swh-search-origin-metadata').prop('checked');
      let queryParameters = new URLSearchParams();
      queryParameters.append('q', searchQueryText);
      if (withVisit) {
        queryParameters.append('with_visit', withVisit);
      }
      if (withContent) {
        queryParameters.append('with_content', withContent);
      }
      if (searchMetadata) {
        queryParameters.append('search_metadata', searchMetadata);
      }
      // Update the url, triggering page reload and effective search
      window.location = `${Urls.browse_search()}?${queryParameters.toString()}`;
    });

    $('#origins-next-results-button').click(event => {
      if ($('#origins-next-results-button').hasClass('disabled') || inSearch) {
        return;
      }
      inSearch = true;
      linksPrev.push(linkCurrent);
      searchOrigins(linkNext);
      event.preventDefault();
    });

    $('#origins-prev-results-button').click(event => {
      if ($('#origins-prev-results-button').hasClass('disabled') || inSearch) {
        return;
      }
      inSearch = true;
      searchOrigins(linksPrev.pop());
      event.preventDefault();
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
