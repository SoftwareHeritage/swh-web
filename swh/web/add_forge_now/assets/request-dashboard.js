/**
 * Copyright (C) 2022  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import {csrfPost, getHumanReadableDate, handleFetchError} from 'utils/functions';
import requestHistoryItem from './add-request-history-item.ejs';
import initialEmailTempate from './forge-admin-email.ejs';
import successEmailTempate from './forge-success-email.ejs';

let forgeRequest;

export function onRequestDashboardLoad(requestId, nextStatusesFor) {
  $(document).ready(() => {
    populateRequestDetails(requestId, nextStatusesFor);

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
        populateRequestDetails(requestId, nextStatusesFor);
      } catch (response) {
        $('#userMessage').text('Sorry; Updating the request failed');
        $('#userMessage').removeClass('badge-success');
        $('#userMessage').addClass('badge-danger');
      }
    });
  });
}

async function populateRequestDetails(requestId, nextStatusesFor) {
  try {
    const response = await fetch(Urls.api_1_add_forge_request_get(requestId));
    handleFetchError(response);
    const data = await response.json();
    forgeRequest = data.request;

    $('#requestStatus').text(swh.add_forge_now.formatRequestStatusName(forgeRequest.status));
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
    $('#contactForgeAdmin').attr('emailSubject', `Software Heritage archival notification for ${forgeRequest.forge_domain}`);
    populateRequestHistory(data.history);
    populateDecisionSelectOption(forgeRequest.status, nextStatusesFor);
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

export function populateDecisionSelectOption(currentStatus, nextStatusesFor) {

  // Determine the possible next status out of the current one
  const nextStatuses = nextStatusesFor[currentStatus];

  function addStatusOption(status, index) {
    // Push the next possible status options
    const label = swh.add_forge_now.formatRequestStatusName(status);
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
  const mailTo = encodeURIComponent($('#contactForgeAdmin').attr('emailTo'));
  const mailCc = encodeURIComponent($('#contactForgeAdmin').attr('emailCc'));
  const subject = encodeURIComponent($('#contactForgeAdmin').attr('emailSubject'));
  // select email template according to the status:
  let emailText = '';
  if (forgeRequest.status === 'PENDING') {
    emailText = encodeURIComponent(initialEmailTempate({'forgeUrl': forgeRequest.forge_url}).trim().replace(/\n/g, '\r\n'));
  }
  if (forgeRequest.status === 'FIRST_ORIGIN_LOADED') {
    emailText = encodeURIComponent(successEmailTempate({'forgeUrl': encodeURIComponent(forgeRequest.forge_url)}).trim().replace(/\n/g, '\r\n'));
  }
  const w = window.open('', '_blank', '', true);
  w.location.href = `mailto:${mailTo}?Cc=${mailCc}&Reply-To=${mailCc}&Subject=${subject}&body=${emailText}`;
  w.focus();
}
