/**
 * Copyright (C) 2018-2024  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import {swhSpinnerSrc, dataTableCommonConfig} from 'utils/constants';
import {
  csrfPost, getCanonicalOriginURL, getHumanReadableDate, handleFetchError,
  htmlAlert, isGitRepoUrl, validateUrl
} from 'utils/functions';
import userRequestsFilterCheckboxFn from 'utils/requests-filter-checkbox.ejs';
import artifactFormRowTemplate from './artifact-form-row.ejs';

let saveRequestsTable;

async function originSaveRequest(
  originType, originUrl, extraData,
  acceptedCallback, pendingCallback, errorCallback
) {
  // Actually trigger the origin save request
  const addSaveOriginRequestUrl = Urls.api_1_save_origin(originType, originUrl);
  $('.swh-processing-save-request').css('display', 'block');
  let headers = {};
  let body = null;
  if (extraData !== {}) {
    body = JSON.stringify(extraData);
    headers = {
      'Content-Type': 'application/json'
    };
  };

  try {
    const response = await csrfPost(addSaveOriginRequestUrl, headers, body);
    handleFetchError(response);
    const data = await response.json();
    $('.swh-processing-save-request').css('display', 'none');
    if (data.save_request_status === 'accepted') {
      acceptedCallback();
    } else {
      pendingCallback();
    }
  } catch (response) {
    $('.swh-processing-save-request').css('display', 'none');
    const errorData = await response.json();
    errorCallback(response.status, errorData);
  };
}

function addArtifactVersionAutofillHandler(formId) {
  // autofill artifact version input with the filename from
  // the artifact url without extensions
  $(`#swh-input-artifact-url-${formId}`).on('input', function(event) {
    const artifactUrl = $(this).val().trim();
    let filename = artifactUrl.split('/').slice(-1)[0];
    if (filename !== artifactUrl) {
      filename = filename.replace(/tar.*$/, 'tar');
      const filenameNoExt = filename.split('.').slice(0, -1).join('.');
      const artifactVersion = $(`#swh-input-artifact-version-${formId}`);
      if (filenameNoExt !== filename) {
        artifactVersion.val(filenameNoExt);
      }
    }
  });
}

export function maybeRequireExtraInputs() {
  // Read the actual selected value and depending on the origin type, display some extra
  // inputs or hide them. This makes the extra inputs disabled when not displayed.
  const originType = $('#swh-input-visit-type').val();
  let display = 'none';
  let disabled = true;

  if (originType === 'archives') {
    display = 'flex';
    disabled = false;
  }
  $('.swh-save-origin-archives-form').css('display', display);
  if (!disabled) {
    // help paragraph must have block display for proper rendering
    $('#swh-save-origin-archives-help').css('display', 'block');
  }
  $('.swh-save-origin-archives-form .form-control').prop('disabled', disabled);

  if (originType === 'archives' && $('.swh-save-origin-archives-form').length === 1) {
    // insert first artifact row when the archives visit type is selected for the first time
    $('.swh-save-origin-archives-form').last().after(
      artifactFormRowTemplate({deletableRow: false, formId: 0}));
    addArtifactVersionAutofillHandler(0);
  }
}

export function addArtifactFormRow() {
  const formId = $('.swh-save-origin-artifact-form').length;
  $('.swh-save-origin-artifact-form').last().after(
    artifactFormRowTemplate({
      deletableRow: true,
      formId: formId
    })
  );
  addArtifactVersionAutofillHandler(formId);
}

export function deleteArtifactFormRow(event) {
  $(event.target).closest('.swh-save-origin-artifact-form').remove();
}

const saveRequestCheckboxId = 'swh-save-requests-user-filter';
const userRequestsFilterCheckbox = userRequestsFilterCheckboxFn({
  'inputId': saveRequestCheckboxId,
  'checked': false // no filtering by default on that view
});

const csvExportButton = `
<a href="${Urls.admin_origin_save_requests_csv()}"
   class="btn btn-secondary btn-sm swh-tr-link"
   role="button">
  <i class="mdi mdi-table mdi-fw" aria-hidden="true"></i>
  CSV export
</a>
`;

export function initOriginSave() {

  $(document).ready(() => {

    $.fn.dataTable.ext.errMode = 'none';

    // set git as the default value as before
    $('#swh-input-visit-type').val('git');

    saveRequestsTable = $('#swh-origin-save-requests')
      .on('error.dt', (e, settings, techNote, message) => {
        $('#swh-origin-save-request-list-error').text('An error occurred while retrieving the save requests list');
        console.log(message);
      })
      .DataTable({
        ...dataTableCommonConfig,
        ajax: {
          url: Urls.origin_save_requests_list('all'),
          data: (d) => {
            if (swh.webapp.isUserLoggedIn() && $(`#${saveRequestCheckboxId}`).prop('checked')) {
              d.user_requests_only = '1';
            }
          }
        },
        // see https://datatables.net/examples/advanced_init/dom_toolbar.html and the comments section
        // this option customizes datatables UI components by adding an extra checkbox above the table
        // while keeping bootstrap layout
        dom: '<"row mb-2"<"col-sm-3"l><"col-sm-3 text-start user-requests-filter">' +
             '<"col-sm-3 requests-csv-export"><"col-sm-3"f>>' +
             '<"row"<"col-sm-12"tr>>' +
             '<"row mt-2"<"col-sm-5"i><"col-sm-7"p>>',
        fnInitComplete: function() {
          if (swh.webapp.isUserLoggedIn()) {
            $('div.user-requests-filter').html(userRequestsFilterCheckbox);
            if (swh.webapp.isStaffUser()) {
              $('div.requests-csv-export').html(csvExportButton);
            }
            $(`#${saveRequestCheckboxId}`).on('change', () => {
              saveRequestsTable.draw();
            });
          }
        },
        columns: [
          {
            data: 'save_request_date',
            name: 'request_date',
            render: getHumanReadableDate
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
                  if (row.visit_status === 'full' || row.visit_status === 'partial') {
                    let browseOriginUrl = `${Urls.browse_origin()}?origin_url=${encodeURIComponent(sanitizedURL)}`;
                    if (row.visit_date) {
                      browseOriginUrl += `&amp;timestamp=${encodeURIComponent(row.visit_date)}`;
                    }
                    html += `<a href="${browseOriginUrl}">${sanitizedURL}</a>`;
                  } else {
                    const tooltip = 'origin was successfully loaded, waiting for data to be available in database';
                    html += `<span title="${tooltip}">${sanitizedURL}</span>`;
                  }
                } else {
                  html += sanitizedURL;
                }
                html += `&nbsp;<a href="${sanitizedURL}" target="_blank" rel="noopener noreferrer">` +
                  '<i class="mdi mdi-open-in-new" aria-hidden="true"></i></a>';
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
              let info = '';
              if (row.save_task_status === 'succeeded' || row.save_task_status === 'failed' ||
                  row.note != null) {
                info += `<i class="mdi mdi-information-outline swh-save-request-info"
                           aria-hidden="true" style="cursor: pointer"
                           onclick="swh.save_code_now.displaySaveRequestInfo(event, ${row.id})"></i>`;
              }
              if (row.from_webhook) {
                info += `<i class="mdi mdi-webhook" aria-hidden="true"
                          title="save request created from webhook"></i>`;
              }
              return info;

            }
          },
          {
            render: (data, type, row) => {
              if (row.save_request_status === 'accepted') {
                const saveAgainButton =
                  '<button class="btn btn-secondary btn-sm swh-save-origin-again" type="button" ' +
                  `onclick="swh.save_code_now.fillSaveRequestFormAndScroll(` +
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

        order: [[0, 'desc']],
        responsive: {
          details: {
            type: 'none'
          }
        }
      });

    swh.webapp.addJumpToPagePopoverToDataTable(saveRequestsTable);

    if (window.location.pathname === Urls.origin_save() && window.location.hash === '#requests') {
      // Keep old URLs to the save list working
      window.location = Urls.origin_save_list();
    } else if ($('#swh-origin-save-requests')) {
      saveRequestsTable.draw();
    }

    const saveRequestAcceptedAlert = htmlAlert(
      'success',
      'The "save code now" request has been accepted and will be processed as soon as possible.',
      true
    );

    const saveRequestPendingAlert = htmlAlert(
      'warning',
      'The "save code now" request has been put in pending state and may be accepted for processing after manual review.',
      true
    );

    const saveRequestRateLimitedAlert = htmlAlert(
      'danger',
      'The rate limit for "save code now" requests has been reached. Please try again later.',
      true
    );

    const saveRequestUnknownErrorAlert = htmlAlert(
      'danger',
      'An unexpected error happened when submitting the "save code now request".',
      true
    );

    updateVisitType();

    $('#swh-save-origin-form').submit(async event => {
      event.preventDefault();
      event.stopPropagation();
      $('.alert').alert('close');
      if (event.target.checkValidity()) {
        $(event.target).removeClass('was-validated');
        const originType = $('#swh-input-visit-type').val();
        let originUrl = $('#swh-input-origin-url').val();

        originUrl = await getCanonicalOriginURL(originUrl);

        // read the extra inputs for the 'archives' type
        const extraData = {};
        if (originType === 'archives') {
          extraData['archives_data'] = [];
          for (let i = 0; i < $('.swh-save-origin-artifact-form').length; ++i) {
            extraData['archives_data'].push({
              'artifact_url': $(`#swh-input-artifact-url-${i}`).val(),
              'artifact_version': $(`#swh-input-artifact-version-${i}`).val()
            });
          }
        }

        originSaveRequest(originType, originUrl, extraData,
                          () => $('#swh-origin-save-request-status').html(saveRequestAcceptedAlert),
                          () => $('#swh-origin-save-request-status').html(saveRequestPendingAlert),
                          (statusCode, errorData) => {
                            $('#swh-origin-save-request-status').css('color', 'red');
                            if (statusCode === 403) {
                              const errorAlert = htmlAlert('danger', `Error: ${errorData['reason']}`);
                              $('#swh-origin-save-request-status').html(errorAlert);
                            } else if (statusCode === 429) {
                              $('#swh-origin-save-request-status').html(saveRequestRateLimitedAlert);
                            } else if (statusCode === 400) {
                              const errorAlert = htmlAlert('danger', errorData['reason']);
                              $('#swh-origin-save-request-status').html(errorAlert);
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
      updateVisitType();
    });

    if (window.location.hash === '#requests') {
      $('.nav-tabs a[href="#swh-origin-save-requests-list"]').tab('show');
    }

    $(window).on('hashchange', () => {
      if (window.location.hash === '#requests') {
        $('.nav-tabs a[href="#swh-origin-save-requests-list"]').tab('show');
      } else {
        $('.nav-tabs a[href="#swh-origin-save-requests-create"]').tab('show');
      }
    });

  });

}

function updateVisitType() {
  const originUrl = $('#swh-input-origin-url').val().trim();
  $(this).val(originUrl);
  $('#swh-input-visit-type option').each(function() {
    const val = $(this).val();
    if (val && originUrl.includes(val)) {
      $(this).prop('selected', true);
      // origin URL input need to be validated once new visit type set
      validateSaveOriginUrl($('#swh-input-origin-url')[0]);
    }
  });
}

export function validateSaveOriginUrl(input) {
  const originType = $('#swh-input-visit-type').val();
  const allowedProtocols = ['http:', 'https:', 'svn:', 'git:', 'rsync:',
                            'pserver:', 'ssh:', 'bzr:'];
  const originUrl = validateUrl(input.value.trim(), allowedProtocols);

  let validUrl = originUrl !== null;

  if (validUrl && originType === 'git') {
    validUrl = isGitRepoUrl(originUrl);
  }

  let customValidity = '';
  if (validUrl) {
    if (['', 'anonymous', 'guest', 'password'].indexOf(originUrl.password) === -1) {
      customValidity = 'The origin url contains a password and cannot be accepted for security reasons';
    }
  } else {
    customValidity = 'The origin url is not valid or does not reference a code repository';
  }
  input.setCustomValidity(customValidity);
  $(input).siblings('.invalid-feedback').text(customValidity);
}

export function initTakeNewSnapshot() {

  const newSnapshotRequestAcceptedAlert = htmlAlert(
    'success',
    'The "take new snapshot" request has been accepted and will be processed as soon as possible.',
    true
  );

  const newSnapshotRequestPendingAlert = htmlAlert(
    'warning',
    'The "take new snapshot" request has been put in pending state and may be accepted for processing after manual review.',
    true
  );

  const newSnapshotRequestRateLimitAlert = htmlAlert(
    'danger',
    'The rate limit for "take new snapshot" requests has been reached. Please try again later.',
    true
  );

  const newSnapshotRequestUnknownErrorAlert = htmlAlert(
    'danger',
    'An unexpected error happened when submitting the "save code now request".',
    true
  );

  $(document).ready(() => {
    $('#swh-take-new-snapshot-form').submit(event => {
      event.preventDefault();
      event.stopPropagation();

      const originType = $('#swh-input-visit-type').val();
      const originUrl = $('#swh-input-origin-url').val();
      const extraData = {};

      originSaveRequest(originType, originUrl, extraData,
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

export function formatValuePerType(type, value) {
  // Given some typed value, format and return accordingly formatted value
  const mapFormatPerTypeFn = {
    'json': (v) => JSON.stringify(v, null, 2),
    'date': (v) => new Date(v).toLocaleString(),
    'raw': (v) => v,
    'duration': (v) => v + ' seconds'
  };

  return value === null ? null : mapFormatPerTypeFn[type](value);
}

export async function displaySaveRequestInfo(event, saveRequestId) {
  event.stopPropagation();
  const saveRequestTaskInfoUrl = Urls.origin_save_task_info(saveRequestId);
  // close popover when clicking again on the info icon
  if ($(event.target).data('has.popover')) {
    $(event.target).data('has.popover', false);
    $(event.target).popover('dispose');
    return;
  }
  $('.swh-save-request-info').popover('dispose');
  $(event.target).data('has.popover', true);
  $(event.target).popover({
    animation: false,
    boundary: 'viewport',
    container: 'body',
    title: 'Save request task information',
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

  $(event.target).popover('show');
  const response = await fetch(saveRequestTaskInfoUrl);
  const saveRequestTaskInfo = await response.json();

  let content;
  if ($.isEmptyObject(saveRequestTaskInfo)) {
    content = 'Not available';

  } else if (saveRequestTaskInfo.note != null) {
    content = `<pre>${saveRequestTaskInfo.note}</pre>`;
  } else {
    const saveRequestInfo = [];
    const taskData = {
      'Type': ['raw', 'type'],
      'Visit status': ['raw', 'visit_status'],
      'Arguments': ['json', 'arguments'],
      'Metadata': ['json', 'metadata'],
      'Id': ['raw', 'id'],
      'Backend id': ['raw', 'backend_id'],
      'Scheduling date': ['date', 'scheduled'],
      'Start date': ['date', 'started'],
      'Completion date': ['date', 'ended'],
      'Duration': ['duration', 'duration'],
      'Runner': ['raw', 'worker'],
      'Log': ['raw', 'message']
    };
    for (const [title, [type, property]] of Object.entries(taskData)) {
      if (saveRequestTaskInfo.hasOwnProperty(property)) {
        saveRequestInfo.push({
          key: title,
          value: formatValuePerType(type, saveRequestTaskInfo[property])
        });
      }
    }
    content = '<table class="table"><tbody>';
    for (const info of saveRequestInfo) {
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
}

export function fillSaveRequestFormAndScroll(visitType, originUrl) {
  $('#swh-input-origin-url').val(originUrl);
  let originTypeFound = false;
  $('#swh-input-visit-type option').each(function() {
    const val = $(this).val();
    if (val && originUrl.includes(val)) {
      $(this).prop('selected', true);
      originTypeFound = true;
    }
  });
  if (!originTypeFound) {
    $('#swh-input-visit-type option').each(function() {
      const val = $(this).val();
      if (val === visitType) {
        $(this).prop('selected', true);
      }
    });
  }
  window.scrollTo(0, 0);
}
