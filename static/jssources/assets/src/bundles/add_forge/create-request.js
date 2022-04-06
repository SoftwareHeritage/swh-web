/**
 * Copyright (C) 2022  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import {handleFetchError, errorMessageFromResponse, csrfPost,
        getHumanReadableDate} from 'utils/functions';
import userRequestsFilterCheckboxFn from 'utils/requests-filter-checkbox.ejs';
import {swhSpinnerSrc} from 'utils/constants';

let requestBrowseTable;

const addForgeCheckboxId = 'swh-add-forge-user-filter';
const userRequestsFilterCheckbox = userRequestsFilterCheckboxFn({
  'inputId': addForgeCheckboxId,
  'checked': true // by default, display only user requests
});

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
        const errorData = await errorResponse.json();
        // if (errorResponse.content_type === 'text/plain') { // does not work?
        if (errorResponse.status === 409) {
          errorMessage = errorData;
        } else { // assuming json response
          // const exception = errorData['exception'];
          errorMessage = errorMessageFromResponse(
            errorData, 'An unknown error occurred during the request creation');
        }
        $('#userMessage').text(errorMessage);
        $('#userMessage').removeClass('badge-success');
        $('#userMessage').addClass('badge-danger');
      }
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
      language: {
        processing: `<img src="${swhSpinnerSrc}"></img>`
      },
      retrieve: true,
      searching: true,
      info: false,
      // Layout configuration, see [1] for more details
      // [1] https://datatables.net/reference/option/dom
      dom: '<"row"<"col-sm-3"l><"col-sm-6 text-left user-requests-filter"><"col-sm-3"f>>' +
           '<"row"<"col-sm-12"tr>>' +
           '<"row"<"col-sm-5"i><"col-sm-7"p>>',
      ajax: {
        'url': Urls.add_forge_request_list_datatables(),
        data: (d) => {
          const checked = $(`#${addForgeCheckboxId}`).prop('checked');
          // If this function is called while the page is loading, 'checked' is
          // undefined. As the checkbox defaults to being checked, coerce this to true.
          if (swh.webapp.isUserLoggedIn() && (checked === undefined || checked)) {
            d.user_requests_only = '1';
          }
        }
      },
      fnInitComplete: function() {
        if (swh.webapp.isUserLoggedIn()) {
          $('div.user-requests-filter').html(userRequestsFilterCheckbox);
          $(`#${addForgeCheckboxId}`).on('change', () => {
            requestBrowseTable.draw();
          });
        }
      },
      columns: [
        {
          data: 'submission_date',
          name: 'submission_date',
          render: getHumanReadableDate
        },
        {
          data: 'forge_type',
          name: 'forge_type',
          render: $.fn.dataTable.render.text()
        },
        {
          data: 'forge_url',
          name: 'forge_url',
          render: function(data, type, row) {
            if (type === 'display') {
              let html = '';
              const sanitizedURL = $.fn.dataTable.render.text().display(data);
              html += sanitizedURL;
              html += `&nbsp;<a href="${sanitizedURL}" target="_blank" rel="noopener noreferrer">` +
                '<i class="mdi mdi-open-in-new" aria-hidden="true"></i></a>';
              return html;
            }
            return data;
          }
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
}
