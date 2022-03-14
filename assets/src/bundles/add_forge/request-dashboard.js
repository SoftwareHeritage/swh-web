/**
 * Copyright (C) 2022  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

export function onRequestDashboardLoad(requestId) {
  populateRequestDetails(requestId);

  $('#contactForgeAdmin').click((event) => {
    contactForgeAdmin(event);
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

        populateRequestDetails(requestId); // FIXME, this is not upating the options list; maybe we should clear everything before re-populating
      },
      error: function(request, status, error) {
        // FIXME, show error response from server
        $('#userMessage').text('Sorry following error happened, ' + error);
        $('#userMessage').removeClass('badge-success');
        $('#userMessage').addClass('badge-danger');
      }
    });
  });
}

async function populateRequestDetails(requestId) {
  fetch(Urls.api_1_add_forge_request_get(requestId))
    .then(response => response.json())
    .then(data => {
      $('#requestStatus').text(data.request.status);
      $('#requestType').text(data.request.forge_type);
      $('#requestURL').text(data.request.forge_url);
      $('#requestEmail').text(data.request.forge_contact_email);
      // FIXME, set the correct email address in send button
      // $('#requestEmail').(data.request.forge_contact_email);
      populateRequestHistory(data.history);
      populateDecisionSelectOption(data.request.status);
    })
    .catch(error => {
      // FIXME, handle error case
      console.log(error);
    });
}

function populateRequestHistory(history) {
  history.forEach((each) => {
    $('#swh-request-history').append(
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

function contactForgeAdmin(event) {
  // Open the mailclient with pre-filled text
  const mailTo = $('#contactForgeAdmin').attr('emailTo');
  const subject = $('#contactForgeAdmin').attr('emailSubject');
  const emailText = $('#swh-input-forge-comment').val();
  window.location = `mailto: ${mailTo}?subject=${subject}&body=${emailText}`;
}
