/**
 * Copyright (C) 2022  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import {handleFetchError} from 'utils/functions';

export function initAddForge() {
  $(document).ready(() => {
    // populateRequests
    $('#requestForm').submit(function(event) {
      event.preventDefault();

      $.ajax({
        data: $(this).serialize(),
        type: $(this).attr('method'),
        url: $(this).attr('action'),
        success: function(response) {
          $('#userMessage').text('Your request has been submitted');
          $('#userMessage').addClass('badge-success');
        },
        error: function(request, status, error) {
          $('#userMessage').text('Sorry following error happened, ' + error);
          $('#userMessage').addClass('badge-danger');
        }
      });
    });
  });
}

export async function getRequests() {
  // Retrieve the list of add forge now requests promise

  const requestsListUrl = Urls.api_1_add_forge_request_list();
  const response = await fetch(requestsListUrl, {
    credentials: 'include'
  });
  handleFetchError(response);
  return response;
}

export async function populateDraft() {
  const promise = await getRequests();
  promise
    .then(response => response.json())
    .then(data => {
      console.log(data);
      // FIXME actually populate
    })
    .catch((error) => {
      console.error('Error:', error);
    });
}

export function populateModerationList() {
  $('#swh-add-forge-now-moderation-list')
    .on('error.dt', (e, settings, techNote, message) => {
      $('#swh-add-forge-now-moderation-list-error').text(message);
    })
    .DataTable({
      serverSide: true,
      processing: true,
      // let's define the order of table options display
      // f: (f)ilter
      // l: (l)ength changing
      // r: p(r)ocessing
      // t: (t)able
      // i: (i)nfo
      // p: (p)agination
      // see https://datatables.net/examples/basic_init/dom.html
      dom: '<<"d-flex justify-content-between align-items-center"f' +
        '<"#list-exclude">l>rt<"bottom"ip>>',
      // div#list-exclude is a custom filter added next to dataTable
      // initialization below through js dom manipulation, see
      // https://datatables.net/examples/advanced_init/dom_toolbar.html
      ajax: {
        url: Urls.api_1_add_forge_request_list()
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
