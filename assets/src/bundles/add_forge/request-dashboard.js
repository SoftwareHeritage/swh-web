/**
 * Copyright (C) 2022  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import {handleFetchError, csrfPost, getHumanReadableDate} from 'utils/functions';
import emailTempate from './forge-admin-email.ejs';
import requestHistoryItem from './add-request-history-item.ejs';

let forgeRequest;

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
    forgeRequest = data.request;

    $('#requestStatus').text(swh.add_forge.formatRequestStatusName(forgeRequest.status));
    $('#requestType').text(forgeRequest.forge_type);
    $('#requestURL').text(forgeRequest.forge_url);
    $('#requestContactName').text(forgeRequest.forge_contact_name);
    $('#requestContactConsent').text(forgeRequest.submitter_forward_username);
    $('#requestContactEmail').text(forgeRequest.forge_contact_email);
    $('#submitterMessage').text(forgeRequest.forge_contact_comment);
    $('#updateComment').val('');

    // Setting data for the email, now adding static data
    $('#contactForgeAdmin').attr('emailTo', forgeRequest.forge_contact_email);
    $('#contactForgeAdmin').attr('emailCc', forgeRequest.inbound_email_address);
    $('#contactForgeAdmin').attr('emailSubject', `Software Heritage archival request for ${forgeRequest.forge_domain}`);
    populateRequestHistory(data.history);
    populateDecisionSelectOption(forgeRequest.status);
  } catch (e) {
    if (e instanceof Response) {
      // The fetch request failed (in handleFetchError), show the error message
      $('#fetchError').removeClass('d-none');
      $('#requestDetails').addClass('d-none');
    } else {
      // Unknown exception, pass it through
      throw e;
    }
  }
}

function populateRequestHistory(history) {
  $('#requestHistory').children().remove();

  history.forEach((event, index) => {
    const historyEvent = requestHistoryItem({
      'event': event,
      'index': index,
      'getHumanReadableDate': getHumanReadableDate
    });
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

  // Determine the possible next status out of the current one
  const nextStatuses = nextStatusesFor[currentStatus];

  function addStatusOption(status, index) {
    // Push the next possible status options
    const label = swh.add_forge.formatRequestStatusName(status);
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
  const mailCc = $('#contactForgeAdmin').attr('emailCc');
  const subject = $('#contactForgeAdmin').attr('emailSubject');
  const emailText = emailTempate({'forgeUrl': forgeRequest.forge_url}).trim().replace(/\n/g, '%0D%0A');
  const w = window.open('', '_blank', '', true);
  w.location.href = `mailto:${mailTo}?Cc=${mailCc}&Reply-To=${mailCc}&Subject=${subject}&body=${emailText}`;
  w.focus();
}
