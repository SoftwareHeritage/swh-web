/**
 * Copyright (C) 2022  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

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
          $('#userMessage').removeClass('badge-danger');
          $('#userMessage').addClass('badge-success');
        },
        error: function(request, status, error) {
          $('#userMessage').text('Sorry following error happened, ' + error);
          $('#userMessage').removeClass('badge-success');
          $('#userMessage').addClass('badge-danger');
        }
      });
    });

    $('#updateRequestForm').submit(function(event) {
      event.preventDefault();

      $.ajax({
        data: $(this).serialize(),
        // header:
        type: $(this).attr('method'),
        url: $(this).attr('action'),
        success: function(response) {
          $('#userMessage').text('The request status has been updated ');
          $('#userMessage').removeClass('badge-danger');
          $('#userMessage').addClass('badge-success');
        },
        error: function(request, status, error) {
          $('#userMessage').text('Sorry following error happened, ' + error);
          $('#userMessage').removeClass('badge-success');
          $('#userMessage').addClass('badge-danger');
        }
      });
    });

    $('#swh-add-forge-requests-list-tab').click((event) => {
      populateRequesBrowseList();
    });
  });
}

export function populateRequesBrowseList() {
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
        'url': Urls.api_1_add_forge_request_list(),
        'dataSrc': function(data) {
          return data;
        }
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

export function populateModerationList() {
  $('#swh-add-forge-now-moderation-list')
    .on('error.dt', (e, settings, techNote, message) => {
      $('#swh-add-forge-now-moderation-list-error').text(message);
    })
    .DataTable({
      serverSide: true,
      processing: true,
      searching: false,
      info: false,
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
        'url': Urls.api_1_add_forge_request_list(),
        'dataSrc': function(data) {
          return data;
        }
      },
      columns: [
        {
          data: 'id',
          name: 'request_id',
          render: function(fieldData, type, row, meta) {
            return ''.concat('<a href="/forge/request/', fieldData, '">', fieldData, '</a>');
          }
        },
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

export function populateRequestDetails(requestId) {
  fetch(Urls.api_1_add_forge_request_get(requestId))
    .then(response => response.json())
    .then(data => {
      // FIXME, handle non 200 status
      $('#requestStatus').text(data.request.status);
      $('#requestType').text(data.request.forge_type);
      $('#requestURL').text(data.request.forge_url);
      $('#requestEmail').text(data.request.forge_contact_email);

      populateDecisionSelectOption(data.request.status);
    })
    .catch(error => {
      console.log(error);
    });
}

export function populateRequestHistory() {
}

export function populateDecisionSelectOption(status) {
  if (status === 'PENDING') {
    $('#decisionOptions').append(
      '<option value="SUSPEND">Suspend</option>',
      '<option value="REJECT">Reject</option>'
    );
  } else { // FIX ME add other checks
    $('#decisionOptions').append(
      '<option value="SUSPEND">Suspend</option>',
      '<option value="REJECT">Reject</option>',
      '<option value="DENY">Deny</option>',
      '<option value="ACCEPT">Accept</option>'
    );
  }
  // FIXME, remove all options in terminal state
  // $('select').children().remove();
  // $('select').append('<option id="foo">You can't</option>');
}

export function updateForgeRequest() {
}
