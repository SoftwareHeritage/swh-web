/**
 * Copyright (C) 2022  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

export function onCreateRequestPageLoad() {
  $('#requestForm').submit(function(event) {
    event.preventDefault();
    $.ajax({
      data: $(this).serialize(),
      type: $(this).attr('method'),
      url: $(this).attr('action'),
      success: function(response) {
        $('#userMessageDetail').empty();
        $('#userMessage').text('Your request has been submitted');
        $('#userMessage').removeClass('badge-danger');
        $('#userMessage').addClass('badge-success');
        populateRequesBrowseList();
      },
      error: function(response, status, error) {
        $('#userMessage').text('Sorry; an error occurred');
        $('#userMessageDetail').text(response.responseText);
        $('#userMessage').removeClass('badge-success');
        $('#userMessage').addClass('badge-danger');
      }
    });
  });
  populateRequesBrowseList(); // Load existing requests
}

export async function populateRequesBrowseList() {
  // FIXME, reverse the listing order
  $('#add-forge-request-browse')
    .on('error.dt', (e, settings, techNote, message) => {
      $('#add-forge-browse-request-error').text(message);
    })
    .DataTable({
      serverSide: true,
      processing: true,
      retrieve: true,
      searching: false,
      info: false,
      dom: '<<"d-flex justify-content-between align-items-center"f' +
        '<"#list-exclude">l>rt<"bottom"ip>>',
      ajax: {
        'url': Urls.api_1_add_forge_request_list()
      },
      columns: [
        {
          data: 'submission_date',
          name: 'submission_date'
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
          name: 'status'
        }
      ]
    });
}
