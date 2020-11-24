/**
 * Copyright (C) 2018-2020  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import {handleFetchError, csrfPost, isGitRepoUrl, htmlAlert, removeUrlFragment} from 'utils/functions';
import {swhSpinnerSrc} from 'utils/constants';

let saveRequestsTable;

function originSaveRequest(originType, originUrl,
                           acceptedCallback, pendingCallback, errorCallback) {
  let addSaveOriginRequestUrl = Urls.origin_save_request(originType, originUrl);
  let headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
  };
  $('.swh-processing-save-request').css('display', 'block');
  csrfPost(addSaveOriginRequestUrl, headers)
    .then(handleFetchError)
    .then(response => response.json())
    .then(data => {
      $('.swh-processing-save-request').css('display', 'none');
      if (data.save_request_status === 'accepted') {
        acceptedCallback();
      } else {
        pendingCallback();
      }
    })
    .catch(response => {
      $('.swh-processing-save-request').css('display', 'none');
      response.json().then(errorData => {
        errorCallback(response.status, errorData);
      });
    });
}

export function initOriginSave() {

  $(document).ready(() => {

    $.fn.dataTable.ext.errMode = 'none';

    fetch(Urls.origin_save_types_list())
      .then(response => response.json())
      .then(data => {
        for (let originType of data) {
          $('#swh-input-visit-type').append(`<option value="${originType}">${originType}</option>`);
        }
      });

    saveRequestsTable = $('#swh-origin-save-requests')
      .on('error.dt', (e, settings, techNote, message) => {
        $('#swh-origin-save-request-list-error').text('An error occurred while retrieving the save requests list');
        console.log(message);
      })
      .DataTable({
        serverSide: true,
        processing: true,
        language: {
          processing: `<img src="${swhSpinnerSrc}"></img>`
        },
        ajax: Urls.origin_save_requests_list('all'),
        searchDelay: 1000,
        columns: [
          {
            data: 'save_request_date',
            name: 'request_date',
            render: (data, type, row) => {
              if (type === 'display') {
                let date = new Date(data);
                return date.toLocaleString();
              }
              return data;
            }
          },
          {
            data: 'visit_type',
            name: 'visit_type'
          },
          {
            data: 'origin_url',
            name: 'origin_url',
            render: (data, type, row) => {
              if (type === 'display') {
                let html = '';
                const sanitizedURL = $.fn.dataTable.render.text().display(data);
                if (row.save_task_status === 'succeeded') {
                  let browseOriginUrl = `${Urls.browse_origin()}?origin_url=${encodeURIComponent(sanitizedURL)}`;
                  if (row.visit_date) {
                    browseOriginUrl += `&amp;timestamp=${encodeURIComponent(row.visit_date)}`;
                  }
                  html += `<a href="${browseOriginUrl}">${sanitizedURL}</a>`;
                } else {
                  html += sanitizedURL;
                }
                html += `&nbsp;<a href="${sanitizedURL}"><i class="mdi mdi-open-in-new" aria-hidden="true"></i></a>`;
                return html;
              }
              return data;
            }
          },
          {
            data: 'save_request_status',
            name: 'status'
          },
          {
            data: 'save_task_status',
            name: 'loading_task_status'
          },
          {
            name: 'info',
            render: (data, type, row) => {
              if (row.save_task_status === 'succeeded' || row.save_task_status === 'failed') {
                return `<i class="mdi mdi-information-outline swh-save-request-info" ` +
                       'aria-hidden="true" style="cursor: pointer"' +
                       `onclick="swh.save.displaySaveRequestInfo(event, ${row.id})"></i>`;
              } else {
                return '';
              }
            }
          },
          {
            render: (data, type, row) => {
              if (row.save_request_status === 'accepted') {
                const saveAgainButton =
                  '<button class="btn btn-default btn-sm swh-save-origin-again" type="button" ' +
                  `onclick="swh.save.fillSaveRequestFormAndScroll(` +
                  `'${row.visit_type}', '${row.origin_url}');">` +
                  '<i class="mdi mdi-camera mdi-fw" aria-hidden="true"></i>' +
                  'Save again</button>';
                return saveAgainButton;
              } else {
                return '';
              }
            }
          }
        ],
        scrollY: '50vh',
        scrollCollapse: true,
        order: [[0, 'desc']],
        responsive: {
          details: {
            type: 'none'
          }
        }
      });

    swh.webapp.addJumpToPagePopoverToDataTable(saveRequestsTable);

    $('#swh-origin-save-requests-list-tab').on('shown.bs.tab', () => {
      saveRequestsTable.draw();
      window.location.hash = '#requests';
    });

    $('#swh-origin-save-request-help-tab').on('shown.bs.tab', () => {
      removeUrlFragment();
      $('.swh-save-request-info').popover('dispose');
    });

    let saveRequestAcceptedAlert = htmlAlert(
      'success',
      'The "save code now" request has been accepted and will be processed as soon as possible.',
      true
    );

    let saveRequestPendingAlert = htmlAlert(
      'warning',
      'The "save code now" request has been put in pending state and may be accepted for processing after manual review.',
      true
    );

    let saveRequestRateLimitedAlert = htmlAlert(
      'danger',
      'The rate limit for "save code now" requests has been reached. Please try again later.',
      true
    );

    let saveRequestUnknownErrorAlert = htmlAlert(
      'danger',
      'An unexpected error happened when submitting the "save code now request".',
      true
    );

    $('#swh-save-origin-form').submit(event => {
      event.preventDefault();
      event.stopPropagation();
      $('.alert').alert('close');
      if (event.target.checkValidity()) {
        $(event.target).removeClass('was-validated');
        let originType = $('#swh-input-visit-type').val();
        let originUrl = $('#swh-input-origin-url').val();

        originSaveRequest(originType, originUrl,
                          () => $('#swh-origin-save-request-status').html(saveRequestAcceptedAlert),
                          () => $('#swh-origin-save-request-status').html(saveRequestPendingAlert),
                          (statusCode, errorData) => {
                            $('#swh-origin-save-request-status').css('color', 'red');
                            if (statusCode === 403) {
                              const errorAlert = htmlAlert('danger', `Error: ${errorData['detail']}`);
                              $('#swh-origin-save-request-status').html(errorAlert);
                            } else if (statusCode === 429) {
                              $('#swh-origin-save-request-status').html(saveRequestRateLimitedAlert);
                            } else {
                              $('#swh-origin-save-request-status').html(saveRequestUnknownErrorAlert);
                            }
                          });
      } else {
        $(event.target).addClass('was-validated');
      }
    });

    $('#swh-show-origin-save-requests-list').on('click', (event) => {
      event.preventDefault();
      $('.nav-tabs a[href="#swh-origin-save-requests-list"]').tab('show');
    });

    $('#swh-input-origin-url').on('input', function(event) {
      let originUrl = $(this).val().trim();
      $(this).val(originUrl);
      $('#swh-input-visit-type option').each(function() {
        let val = $(this).val();
        if (val && originUrl.includes(val)) {
          $(this).prop('selected', true);
        }
      });
    });

    if (window.location.hash === '#requests') {
      $('.nav-tabs a[href="#swh-origin-save-requests-list"]').tab('show');
    }

  });

}

export function validateSaveOriginUrl(input) {
  let originType = $('#swh-input-visit-type').val();
  let originUrl = null;
  let validUrl = true;

  try {
    originUrl = new URL(input.value.trim());
  } catch (TypeError) {
    validUrl = false;
  }

  if (validUrl) {
    let allowedProtocols = ['http:', 'https:', 'svn:', 'git:'];
    validUrl = (
      allowedProtocols.find(protocol => protocol === originUrl.protocol) !== undefined
    );
  }

  if (validUrl && originType === 'git') {
    // additional checks for well known code hosting providers
    switch (originUrl.hostname) {
      case 'github.com':
        validUrl = isGitRepoUrl(originUrl);
        break;

      case 'git.code.sf.net':
        validUrl = isGitRepoUrl(originUrl, '/p/');
        break;

      case 'bitbucket.org':
        validUrl = isGitRepoUrl(originUrl);
        break;

      default:
        if (originUrl.hostname.startsWith('gitlab.')) {
          validUrl = isGitRepoUrl(originUrl);
        }
        break;
    }
  }

  if (validUrl) {
    input.setCustomValidity('');
  } else {
    input.setCustomValidity('The origin url is not valid or does not reference a code repository');
  }
}

export function initTakeNewSnapshot() {

  let newSnapshotRequestAcceptedAlert = htmlAlert(
    'success',
    'The "take new snapshot" request has been accepted and will be processed as soon as possible.',
    true
  );

  let newSnapshotRequestPendingAlert = htmlAlert(
    'warning',
    'The "take new snapshot" request has been put in pending state and may be accepted for processing after manual review.',
    true
  );

  let newSnapshotRequestRateLimitAlert = htmlAlert(
    'danger',
    'The rate limit for "take new snapshot" requests has been reached. Please try again later.',
    true
  );

  let newSnapshotRequestUnknownErrorAlert = htmlAlert(
    'danger',
    'An unexpected error happened when submitting the "save code now request".',
    true
  );

  $(document).ready(() => {
    $('#swh-take-new-snapshot-form').submit(event => {
      event.preventDefault();
      event.stopPropagation();

      let originType = $('#swh-input-visit-type').val();
      let originUrl = $('#swh-input-origin-url').val();

      originSaveRequest(originType, originUrl,
                        () => $('#swh-take-new-snapshot-request-status').html(newSnapshotRequestAcceptedAlert),
                        () => $('#swh-take-new-snapshot-request-status').html(newSnapshotRequestPendingAlert),
                        (statusCode, errorData) => {
                          $('#swh-take-new-snapshot-request-status').css('color', 'red');
                          if (statusCode === 403) {
                            const errorAlert = htmlAlert('danger', `Error: ${errorData['detail']}`, true);
                            $('#swh-take-new-snapshot-request-status').html(errorAlert);
                          } else if (statusCode === 429) {
                            $('#swh-take-new-snapshot-request-status').html(newSnapshotRequestRateLimitAlert);
                          } else {
                            $('#swh-take-new-snapshot-request-status').html(newSnapshotRequestUnknownErrorAlert);
                          }
                        });
    });
  });
}

export function displaySaveRequestInfo(event, saveRequestId) {
  event.stopPropagation();
  const saveRequestTaskInfoUrl = Urls.origin_save_task_info(saveRequestId);
  // close popover when clicking again on the info icon
  if ($(event.target).data('bs.popover')) {
    $(event.target).popover('dispose');
    return;
  }
  $('.swh-save-request-info').popover('dispose');
  $(event.target).popover({
    animation: false,
    boundary: 'viewport',
    container: 'body',
    title: 'Save request task information ' +
             '<i style="cursor: pointer; position: absolute; right: 1rem;" ' +
             `class="mdi mdi-close swh-save-request-info-close"></i>`,
    content: `<div class="swh-popover swh-save-request-info-popover">
                  <div class="text-center">
                    <img src=${swhSpinnerSrc}></img>
                    <p>Fetching task information ...</p>
                  </div>
                </div>`,
    html: true,
    placement: 'left',
    sanitizeFn: swh.webapp.filterXSS
  });

  $(event.target).on('shown.bs.popover', function() {
    const popoverId = $(this).attr('aria-describedby');
    $(`#${popoverId} .mdi-close`).click(() => {
      $(this).popover('dispose');
    });
  });

  $(event.target).popover('show');
  fetch(saveRequestTaskInfoUrl)
    .then(response => response.json())
    .then(saveRequestTaskInfo => {
      let content;
      if ($.isEmptyObject(saveRequestTaskInfo)) {
        content = 'Not available';
      } else {
        let saveRequestInfo = [];
        if (saveRequestTaskInfo.type) {
          saveRequestInfo.push({
            key: 'Task type',
            value: saveRequestTaskInfo.type
          });
        }
        if (saveRequestTaskInfo.arguments) {
          saveRequestInfo.push({
            key: 'Task arguments',
            value: JSON.stringify(saveRequestTaskInfo.arguments, null, 2)
          });
        }
        if (saveRequestTaskInfo.id) {
          saveRequestInfo.push({
            key: 'Task id',
            value: saveRequestTaskInfo.id
          });
        }
        if (saveRequestTaskInfo.backend_id) {
          saveRequestInfo.push({
            key: 'Task backend id',
            value: saveRequestTaskInfo.backend_id
          });
        }
        if (saveRequestTaskInfo.scheduled) {
          saveRequestInfo.push({
            key: 'Task scheduling date',
            value: new Date(saveRequestTaskInfo.scheduled).toLocaleString()
          });
        }
        if (saveRequestTaskInfo.started) {
          saveRequestInfo.push({
            key: 'Task start date',
            value: new Date(saveRequestTaskInfo.started).toLocaleString()
          });
        }
        if (saveRequestTaskInfo.ended) {
          saveRequestInfo.push({
            key: 'Task termination date',
            value: new Date(saveRequestTaskInfo.ended).toLocaleString()
          });
        }
        if (saveRequestTaskInfo.duration) {
          saveRequestInfo.push({
            key: 'Task duration',
            value: saveRequestTaskInfo.duration + ' seconds'
          });
        }
        if (saveRequestTaskInfo.worker) {
          saveRequestInfo.push({
            key: 'Task executor',
            value: saveRequestTaskInfo.worker
          });
        }
        if (saveRequestTaskInfo.message) {
          saveRequestInfo.push({
            key: 'Task log',
            value: saveRequestTaskInfo.message
          });
        }
        content = '<table class="table"><tbody>';
        for (let info of saveRequestInfo) {
          content +=
            `<tr>
              <th class="swh-metadata-table-row swh-metadata-table-key">${info.key}</th>
              <td class="swh-metadata-table-row swh-metadata-table-value">
                <pre>${info.value}</pre>
              </td>
            </tr>`;
        }
        content += '</tbody></table>';
      }
      $('.swh-popover').html(content);
      $(event.target).popover('update');
    });
}

export function fillSaveRequestFormAndScroll(visitType, originUrl) {
  $('#swh-input-origin-url').val(originUrl);
  let originTypeFound = false;
  $('#swh-input-visit-type option').each(function() {
    let val = $(this).val();
    if (val && originUrl.includes(val)) {
      $(this).prop('selected', true);
      originTypeFound = true;
    }
  });
  if (!originTypeFound) {
    $('#swh-input-visit-type option').each(function() {
      let val = $(this).val();
      if (val === visitType) {
        $(this).prop('selected', true);
      }
    });
  }
  window.scrollTo(0, 0);
}
