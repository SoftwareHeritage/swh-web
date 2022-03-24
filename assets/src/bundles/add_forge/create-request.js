/**
 * Copyright (C) 2022  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import {handleFetchError, removeUrlFragment, csrfPost,
        getHumanReadableDate} from 'utils/functions';

let requestBrowseTable;

export function onCreateRequestPageLoad() {
  $(document).ready(() => {
    $('#requestCreateForm').submit(async function(event) {
      event.preventDefault();
      try {
        const response = await csrfPost($(this).attr('action'),
                                        {'Content-Type': 'application/x-www-form-urlencoded'},
                                        $(this).serialize());
        handleFetchError(response);
        $('#userMessageDetail').empty();
        $('#userMessage').text('Your request has been submitted');
        $('#userMessage').removeClass('badge-danger');
        $('#userMessage').addClass('badge-success');
        requestBrowseTable.draw(); // redraw the table to update the list
      } catch (errorResponse) {
        $('#userMessageDetail').empty();

        let errorMessage;
        let errorMessageDetail = '';
        const errorData = await errorResponse.json();
        // if (errorResponse.content_type === 'text/plain') { // does not work?
        if (errorResponse.status === 409) {
          errorMessage = errorData;
        } else { // assuming json response
          // const exception = errorData['exception'];
          errorMessage = 'An unknown error occurred during the request creation';
          try {
            const reason = JSON.parse(errorData['reason']);
            Object.entries(reason).forEach((keys, _) => {
              const key = keys[0];
              const message = keys[1][0]; // take only the first issue
              errorMessageDetail += `\n${key}: ${message}`;
            });
          } catch (_) {
            errorMessageDetail = errorData['reason']; // can't parse it, leave it raw
          }
        }
        $('#userMessage').text(
          errorMessageDetail ? `Error: ${errorMessageDetail}` : errorMessage
        );
        $('#userMessage').removeClass('badge-success');
        $('#userMessage').addClass('badge-danger');
      }
    });

    $(window).on('hashchange', () => {
      if (window.location.hash === '#browse-requests') {
        $('.nav-tabs a[href="#swh-add-forge-requests-list"]').tab('show');
      } else {
        $('.nav-tabs a[href="#swh-add-forge-submit-request"]').tab('show');
      }
    });

    $('#swh-add-forge-requests-list-tab').on('shown.bs.tab', () => {
      window.location.hash = '#browse-requests';
    });

    $('#swh-add-forge-tab').on('shown.bs.tab', () => {
      removeUrlFragment();
    });

    populateRequestBrowseList(); // Load existing requests
  });
}

export function populateRequestBrowseList() {
  requestBrowseTable = $('#add-forge-request-browse')
    .on('error.dt', (e, settings, techNote, message) => {
      $('#add-forge-browse-request-error').text(message);
    })
    .DataTable({
      serverSide: true,
      processing: true,
      retrieve: true,
      searching: true,
      info: false,
      dom: '<<"d-flex justify-content-between align-items-center"f' +
        '<"#list-exclude">l>rt<"bottom"ip>>',
      ajax: {
        'url': Urls.add_forge_request_list_datatables()
      },
      columns: [
        {
          data: 'submission_date',
          name: 'submission_date',
          render: getHumanReadableDate
        },
        {
          data: 'forge_type',
          name: 'forge_type'
        },
        {
          data: 'forge_url',
          name: 'forge_url'
        },
        {
          data: 'status',
          name: 'status',
          render: function(data, type, row, meta) {
            return swh.add_forge.formatRequestStatusName(data);
          }
        }
      ]
    });
  requestBrowseTable.draw();
}
