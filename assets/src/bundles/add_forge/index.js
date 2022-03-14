/**
 * Copyright (C) 2022  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

export function initAddForge() {
  $(document).ready(() => {
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
        },
        error: function(response, status, error) {
          $('#userMessage').text('Sorry; an error occurred');
          $('#userMessageDetail').text(response.responseText);
          $('#userMessage').removeClass('badge-success');
          $('#userMessage').addClass('badge-danger');
        }
      });
    });

    $('#updateRequestForm').submit(function(event) {
      event.preventDefault();

      $.ajax({
        data: $(this).serialize(),
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

    $('#contactForgeAdmin').click((event) => {
      contactForgeAdmin(event);
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
      dom: '<<"d-flex justify-content-between align-items-center"f' +
        '<"#list-exclude">l>rt<"bottom"ip>>',
      ajax: {
        'url': Urls.api_1_add_forge_request_list()
      },
      columns: [
        {
          data: 'id',
          name: 'id',
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
      // $('#requestEmail').(data.request.forge_contact_email);

      populateRequestHistory(data.history);
      populateDecisionSelectOption(data.request.status);
    })
    .catch(error => {
      console.log(error);
    });
}

export function populateRequestHistory(history) {
  const parent = $('#swh-request-history');
  history.forEach((each) => {
    parent.append(
      `<li class="list-group-item d-flex justify-content-between lh-condensed">
       On ${each.date} by ${each.actor} (${each.actor_role})
       New status: ${each.new_status}</li>`
    );
  });
}

export function populateDecisionSelectOption(currentStatus) {
  const nextStatusesFor = {
    'PENDING': ['WAITING_FOR_FEEDBACK', 'REJECTED', 'SUSPENDED'],
    'WAITING_FOR_FEEDBACK': ['FEEDBACK_TO_HANDLE'],
    'FEEDBACK_TO_HANDLE': [
      'WAITING_FOR_FEEDBACK',
      'ACCEPTED',
      'REJECTED',
      'SUSPENDED'
    ],
    'ACCEPTED': ['SCHEDULED'],
    'SCHEDULED': [
      'FIRST_LISTING_DONE',
      'FIRST_ORIGIN_LOADED'
    ],
    'FIRST_LISTING_DONE': ['FIRST_ORIGIN_LOADED'],
    'FIRST_ORIGIN_LOADED': [],
    'REJECTED': [],
    'SUSPENDED': ['PENDING'],
    'DENIED': []
  };

  const statusLabel = {
    'PENDING': 'pending',
    'WAITING_FOR_FEEDBACK': 'waiting for feedback',
    'FEEDBACK_TO_HANDLE': 'feedback to handle',
    'ACCEPTED': 'accepted',
    'SCHEDULED': 'scheduled',
    'FIRST_LISTING_DONE': 'first listing done',
    'FIRST_ORIGIN_LOADED': 'first origin loaded',
    'REJECTED': 'rejected',
    'SUSPENDED': 'suspended',
    'DENIED': 'denied'
  };

  // Determine the possible next status out of the current one
  const nextStatuses = nextStatusesFor[currentStatus];

  function addStatusOption(status, index) {
    // Push the next possible status option
    const label = statusLabel[status];
    $('#decisionOptions').append(
      `<option value="${status}">${label}</option>`
    );
  }

  nextStatuses.forEach(addStatusOption);
}

export function updateForgeRequest() {
}

function contactForgeAdmin(event) {
  // Open the mailclient with pre-filled text
  const mailTo = $('#contactForgeAdmin').attr('emailTo');
  const subject = $('#contactForgeAdmin').attr('emailSubject');
  const emailText = $('#swh-input-forge-comment').val();
  window.location = `mailto: ${mailTo}?subject=${subject}&body=${emailText}`;
}
