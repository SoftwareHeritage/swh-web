/**
 * Copyright (C) 2018-2019  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import {handleFetchError, csrfPost, isGitRepoUrl, htmlAlert, removeUrlFragment} from 'utils/functions';
import {swhSpinnerSrc} from 'utils/constants';
import {validate} from 'validate.js';

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
      errorCallback(response.status);
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
                const sanitizedURL = $.fn.dataTable.render.text().display(data);
                return `<a href="${sanitizedURL}">${sanitizedURL}</a>`;
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
            name: 'loading_task_status',
            render: (data, type, row) => {
              if (data === 'succeed' && row.visit_date) {
                let browseOriginUrl = Urls.browse_origin(row.origin_url);
                browseOriginUrl += `visit/${row.visit_date}/`;
                return `<a href="${browseOriginUrl}">${data}</a>`;
              }
              return data;
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

    $('#swh-origin-save-request-create-tab').on('shown.bs.tab', () => {
      removeUrlFragment();
    });

    let saveRequestAcceptedAlert = htmlAlert(
      'success',
      'The "save code now" request has been accepted and will be processed as soon as possible.'
    );

    let saveRequestPendingAlert = htmlAlert(
      'warning',
      'The "save code now" request has been put in pending state and may be accepted for processing after manual review.'
    );

    let saveRequestRejectedAlert = htmlAlert(
      'danger',
      'The "save code now" request has been rejected because the provided origin url is blacklisted.'
    );

    let saveRequestRateLimitedAlert = htmlAlert(
      'danger',
      'The rate limit for "save code now" requests has been reached. Please try again later.'
    );

    let saveRequestUnknownErrorAlert = htmlAlert(
      'danger',
      'An unexpected error happened when submitting the "save code now request'
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
                          (statusCode) => {
                            $('#swh-origin-save-request-status').css('color', 'red');
                            if (statusCode === 403) {
                              $('#swh-origin-save-request-status').html(saveRequestRejectedAlert);
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
  let originUrl = input.value.trim();
  let validUrl = validate({website: originUrl}, {
    website: {
      url: {
        schemes: ['http', 'https', 'svn', 'git']
      }
    }
  }) === undefined;
  let originType = $('#swh-input-visit-type').val();
  if (originType === 'git' && validUrl) {
    // additional checks for well known code hosting providers
    let githubIdx = originUrl.indexOf('://github.com');
    let gitlabIdx = originUrl.indexOf('://gitlab.');
    let gitSfIdx = originUrl.indexOf('://git.code.sf.net');
    let bitbucketIdx = originUrl.indexOf('://bitbucket.org');
    if (githubIdx !== -1 && githubIdx <= 5) {
      validUrl = isGitRepoUrl(originUrl, 'github.com');
    } else if (gitlabIdx !== -1 && gitlabIdx <= 5) {
      let startIdx = gitlabIdx + 3;
      let idx = originUrl.indexOf('/', startIdx);
      if (idx !== -1) {
        let gitlabDomain = originUrl.substr(startIdx, idx - startIdx);
        validUrl = isGitRepoUrl(originUrl, gitlabDomain);
      } else {
        validUrl = false;
      }
    } else if (gitSfIdx !== -1 && gitSfIdx <= 5) {
      validUrl = isGitRepoUrl(originUrl, 'git.code.sf.net/p');
    } else if (bitbucketIdx !== -1 && bitbucketIdx <= 5) {
      validUrl = isGitRepoUrl(originUrl, 'bitbucket.org');
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
    'The "take new snapshot" request has been accepted and will be processed as soon as possible.'
  );

  let newSnapshotRequestPendingAlert = htmlAlert(
    'warning',
    'The "take new snapshot" request has been put in pending state and may be accepted for processing after manual review.'
  );

  let newSnapshotRequestRejectedAlert = htmlAlert(
    'danger',
    'The "take new snapshot" request has been rejected.'
  );

  let newSnapshotRequestRateLimitAlert = htmlAlert(
    'danger',
    'The rate limit for "take new snapshot" requests has been reached. Please try again later.'
  );

  let newSnapshotRequestUnknownErrorAlert = htmlAlert(
    'danger',
    'An unexpected error happened when submitting the "save code now request".'
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
                        (statusCode) => {
                          $('#swh-take-new-snapshot-request-status').css('color', 'red');
                          if (statusCode === 403) {
                            $('#swh-take-new-snapshot-request-status').html(newSnapshotRequestRejectedAlert);
                          } else if (statusCode === 429) {
                            $('#swh-take-new-snapshot-request-status').html(newSnapshotRequestRateLimitAlert);
                          } else {
                            $('#swh-take-new-snapshot-request-status').html(newSnapshotRequestUnknownErrorAlert);
                          }
                        });
    });
  });
}
