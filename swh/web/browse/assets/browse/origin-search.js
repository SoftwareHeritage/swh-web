/**
 * Copyright (C) 2018-2022  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import {errorMessageFromResponse, handleFetchError, isArchivedOrigin} from 'utils/functions';

const limit = 100;
const linksPrev = [];
let linkNext = null;
let linkCurrent = null;
let inSearch = false;

function parseLinkHeader(s) {
  const re = /<(.+)>; rel="next"/;
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

async function populateOriginSearchResultsTable(origins) {
  if (origins.length > 0) {
    $('#swh-origin-search-results').show();
    $('#swh-no-result').hide();
    clearOriginSearchResultsTable();
    const table = $('#origin-search-results tbody');
    const promises = [];
    for (const [i, origin] of origins.entries()) {
      const browseUrl = `${Urls.browse_origin()}?origin_url=${encodeURIComponent(origin.url)}`;
      let tableRow =
        `<tr id="origin-${i}" class="swh-search-result-entry swh-tr-hover-highlight">`;
      tableRow +=
        `<td id="visit-type-origin-${i}" class="swh-origin-visit-type" style="width: 120px;">` +
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
      let latestSnapshotUrl = Urls.api_1_origin_visit_latest(origin.url.replace('?', '%3F'));
      latestSnapshotUrl += '?require_snapshot=true';
      promises.push(fetch(latestSnapshotUrl));
    }
    const responses = await Promise.all(promises);
    const responsesData = await Promise.all(responses.map(r => r.json()));
    for (let i = 0; i < responses.length; ++i) {
      const response = responses[i];
      const data = responsesData[i];
      if (response.status !== 404 && data.type) {
        $(`#visit-type-origin-${i}`).html(data.type);
        $(`#visit-status-origin-${i}`).html(
          '<i title="Software origin has been archived by Software Heritage" ' +
          'class="mdi mdi-check-bold mdi-fw"></i>Archived');
      } else {
        $(`#visit-type-origin-${i}`).html('unknown');
        $(`#visit-status-origin-${i}`).html(
          '<i title="Software origin archival by Software Heritage is pending" ' +
          'class="mdi mdi-close-thick mdi-fw"></i>Pending archival');
        if ($('#swh-filter-empty-visits').prop('checked')) {
          $(`#origin-${i}`).remove();
        }
      }
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
  const searchMetadata = $('#swh-search-origin-metadata').prop('checked');
  if (searchMetadata) {
    baseSearchUrl = new URL(Urls.api_1_origin_metadata_search(), window.location);
    baseSearchUrl.searchParams.append('fulltext', searchQueryText);
  } else {
    const useSearchQL = $('#swh-search-use-ql').prop('checked');
    baseSearchUrl = new URL(Urls.api_1_origin_search(searchQueryText), window.location);
    baseSearchUrl.searchParams.append('use_ql', useSearchQL ?? false);
  }

  // As we only use the 'url' field of results, tell the server not to send metadata
  baseSearchUrl.searchParams.append('fields', 'url');

  const withVisit = $('#swh-search-origins-with-visit').prop('checked');
  baseSearchUrl.searchParams.append('limit', limit);
  baseSearchUrl.searchParams.append('with_visit', withVisit);
  const visitType = $('#swh-search-visit-type').val();
  if (visitType !== 'any') {
    baseSearchUrl.searchParams.append('visit_type', visitType);
  }
  const searchUrl = baseSearchUrl.toString();
  searchOrigins(searchUrl);
}

async function searchOrigins(searchUrl) {
  clearOriginSearchResultsTable();
  $('.swh-loading').addClass('show');
  try {
    const response = await fetch(searchUrl);
    handleFetchError(response);
    const data = await response.json();
    // Save link to the current results page
    linkCurrent = searchUrl;
    // Save link to the next results page.
    linkNext = null;
    if (response.headers.has('Link')) {
      const parsedLink = parseLinkHeader(response.headers.get('Link'));
      if (parsedLink !== undefined) {
        linkNext = parsedLink;
      }
    }
    // prevLinks is updated by the caller, which is the one to know if
    // we're going forward or backward in the pages.

    $('.swh-loading').removeClass('show');
    populateOriginSearchResultsTable(data);
  } catch (errorResponse) {
    const errorData = await errorResponse.json();
    $('.swh-loading').removeClass('show');
    inSearch = false;
    $('#swh-origin-search-results').hide();
    $('#swh-no-result').text(errorMessageFromResponse(
      errorData, 'An unknown error occurred while searching origins'));
    $('#swh-no-result').show();
  }
}

async function doSearch() {
  $('#swh-no-result').hide();
  const searchQueryText = $('#swh-origins-url-patterns').val();
  inSearch = true;
  if (searchQueryText.startsWith('swh:')) {
    try {
      // searchQueryText may be a PID so sending search queries to PID resolve endpoint
      const resolveSWHIDUrl = Urls.api_1_resolve_swhid(searchQueryText);
      const response = await fetch(resolveSWHIDUrl);
      handleFetchError(response);
      const data = await response.json();
      // SWHID has been successfully resolved,
      // so redirect to browse page
      window.location = data.browse_url;
    } catch (response) {
      // display a useful error message if the input
      // looks like a SWHID
      const data = await response.json();
      $('#swh-origin-search-results').hide();
      $('.swh-search-pagination').hide();
      $('#swh-no-result').text(data.reason);
      $('#swh-no-result').show();
    }
  } else if (await isArchivedOrigin(searchQueryText)) {
    // redirect to the browse origin
    window.location.href =
      `${Urls.browse_origin()}?origin_url=${encodeURIComponent(searchQueryText)}`;
  } else {
    // otherwise, proceed with origins search irrespective of the error
    $('#swh-origin-search-results').show();
    $('.swh-search-pagination').show();
    searchOriginsFirst(searchQueryText, limit);
  }
}

export function initOriginSearch() {
  $(document).ready(() => {
    $('#swh-search-origins').submit(event => {
      event.preventDefault();
      if (event.target.checkValidity()) {
        $(event.target).removeClass('was-validated');
        const searchQueryText = $('#swh-origins-url-patterns').val().trim();
        const withVisit = $('#swh-search-origins-with-visit').prop('checked');
        const withContent = $('#swh-filter-empty-visits').prop('checked');
        const useSearchQL = $('#swh-search-use-ql').prop('checked');
        const searchMetadata = $('#swh-search-origin-metadata').prop('checked');
        const visitType = $('#swh-search-visit-type').val();
        const queryParameters = new URLSearchParams();
        queryParameters.append('q', searchQueryText);
        if (withVisit) {
          queryParameters.append('with_visit', withVisit);
        }
        if (withContent) {
          queryParameters.append('with_content', withContent);
        }
        if (useSearchQL) {
          queryParameters.append('use_ql', useSearchQL ?? false);
        }
        if (searchMetadata) {
          queryParameters.append('search_metadata', searchMetadata);
        }
        if (visitType !== 'any') {
          queryParameters.append('visit_type', visitType);
        }
        // Update the url, triggering page reload and effective search
        window.location = `${Urls.browse_search()}?${queryParameters.toString()}`;
      } else {
        $(event.target).addClass('was-validated');
      }
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

    if (window.location.search) {
      const urlParams = new URLSearchParams(window.location.search);
      const query = urlParams.get('q');
      const withVisit = urlParams.has('with_visit');
      const useSearchQL = urlParams.has('use_ql');
      const withContent = urlParams.has('with_content');
      const searchMetadata = urlParams.has('search_metadata');
      const visitType = urlParams.get('visit_type');

      $('#swh-origins-url-patterns').val(query);
      $('#swh-search-origins-with-visit').prop('checked', withVisit);
      $('#swh-search-use-ql').prop('checked', useSearchQL ?? false);
      $('#swh-filter-empty-visits').prop('checked', withContent);
      $('#swh-search-origin-metadata').prop('checked', searchMetadata);
      if (visitType) {
        $('#swh-search-visit-type').val(visitType);
      }
      doSearch();
    }
  });
}
