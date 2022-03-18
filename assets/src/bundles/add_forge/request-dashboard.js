/**
 * Copyright (C) 2022  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import {handleFetchError, csrfPost} from 'utils/functions';
import emailTempate from './forge-admin-email.ejs';
import requestHistoryItem from './add-request-history-item.ejs';

export function onRequestDashboardLoad(requestId) {
  $(document).ready(() => {
    populateRequestDetails(requestId);

    $('#contactForgeAdmin').click((event) => {
      contactForgeAdmin(event);
    });

    $('#updateRequestForm').submit(async function(event) {
      event.preventDefault();
      try {
        const response = await csrfPost($(this).attr('action'),
                                        {'Content-Type': 'application/x-www-form-urlencoded'},
                                        $(this).serialize());
        handleFetchError(response);
        $('#userMessage').text('The request status has been updated ');
        $('#userMessage').removeClass('badge-danger');
        $('#userMessage').addClass('badge-success');
        populateRequestDetails(requestId);
      } catch (response) {
        $('#userMessage').text('Sorry; Updating the request failed');
        $('#userMessage').removeClass('badge-success');
        $('#userMessage').addClass('badge-danger');
      }
    });
  });
}

async function populateRequestDetails(requestId) {
  try {
    const response = await fetch(Urls.api_1_add_forge_request_get(requestId));
    handleFetchError(response);
    const data = await response.json();
    $('#requestStatus').text(data.request.status);
    $('#requestType').text(data.request.forge_type);
    $('#requestURL').text(data.request.forge_url);
    $('#requestEmail').text(data.request.forge_contact_email);
    $('#submitterMessage').text(data.request.forge_contact_comment);
    $('#updateComment').val('');

    // Setting data for the email, now adding static data
    $('#swh-input-forge-admin-email').val(emailTempate({'forgeUrl': data.request.forge_url}).trim());
    $('#contactForgeAdmin').attr('emailTo', data.request.forge_contact_email);
    $('#contactForgeAdmin').attr('emailSubject', `[swh-add_forge_now] Request ${data.request.id}`);
    populateRequestHistory(data.history);
    populateDecisionSelectOption(data.request.status);
  } catch (response) {
    // The error message
    $('#fetchError').removeClass('d-none');
    $('#requestDetails').addClass('d-none');
  }
}

function populateRequestHistory(history) {
  $('#requestHistory').children().remove();

  history.forEach((event, index) => {
    const historyEvent = requestHistoryItem({'event': event, 'index': index});
    $('#requestHistory').append(historyEvent);
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
    // Push the next possible status options
    const label = statusLabel[status];
    $('#decisionOptions').append(
      `<option value="${status}">${label}</option>`
    );
  }
  // Remove all the options and add new ones
  $('#decisionOptions').children().remove();
  nextStatuses.forEach(addStatusOption);
  $('#decisionOptions').append(
    '<option hidden disabled selected value> -- Add a comment -- </option>'
  );
}

function contactForgeAdmin(event) {
  // Open the mailclient with pre-filled text
  const mailTo = $('#contactForgeAdmin').attr('emailTo');
  const subject = $('#contactForgeAdmin').attr('emailSubject');
  const emailText = $('#swh-input-forge-admin-email').val().replace(/\n/g, '%0D%0A');
  const w = window.open('', '_blank', '', true);
  w.location.href = `mailto: ${mailTo}?subject=${subject}&body=${emailText}`;
  w.focus();
}
