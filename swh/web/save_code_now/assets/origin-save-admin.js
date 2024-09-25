/**
 * Copyright (C) 2018-2024  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import {csrfPost, getHumanReadableDate, handleFetchError, htmlAlert} from 'utils/functions';
import {dataTableCommonConfig} from 'utils/constants';

let authorizedOriginTable;
let unauthorizedOriginTable;
let pendingSaveRequestsTable;
let acceptedSaveRequestsTable;
let rejectedSaveRequestsTable;

function enableRowSelection(tableSel) {
  $(`${tableSel} tbody`).on('click', 'tr', function() {
    if ($(this).hasClass('selected')) {
      $(this).removeClass('selected');
      $(tableSel).closest('.tab-pane').find('.swh-action-need-selection').prop('disabled', true);
    } else {
      $(`${tableSel} tr.selected`).removeClass('selected');
      $(this).addClass('selected');
      $(tableSel).closest('.tab-pane').find('.swh-action-need-selection').prop('disabled', false);
    }
  });
}

export function initOriginSaveAdmin() {
  $(document).ready(() => {

    $.fn.dataTable.ext.errMode = 'throw';

    authorizedOriginTable = $('#swh-authorized-origin-urls').DataTable({
      ...dataTableCommonConfig,
      ajax: Urls.admin_origin_save_authorized_urls_list(),
      columns: [{data: 'url', name: 'url'}],
      info: false
    });
    enableRowSelection('#swh-authorized-origin-urls');
    swh.webapp.addJumpToPagePopoverToDataTable(authorizedOriginTable);

    unauthorizedOriginTable = $('#swh-unauthorized-origin-urls').DataTable({
      ...dataTableCommonConfig,
      ajax: Urls.admin_origin_save_unauthorized_urls_list(),
      columns: [{data: 'url', name: 'url'}],
      info: false
    });
    enableRowSelection('#swh-unauthorized-origin-urls');
    swh.webapp.addJumpToPagePopoverToDataTable(unauthorizedOriginTable);

    const columnsData = [
      {
        data: 'id',
        name: 'id',
        visible: false,
        searchable: false
      },
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
              let browseOriginUrl = `${Urls.browse_origin()}?origin_url=${encodeURIComponent(sanitizedURL)}`;
              if (row.visit_date) {
                browseOriginUrl += `&amp;timestamp=${encodeURIComponent(row.visit_date)}`;
              }
              html += `<a href="${browseOriginUrl}">${sanitizedURL}</a>`;
            } else {
              html += sanitizedURL;
            }
            html += `&nbsp;<a href="${sanitizedURL}" target="_blank" rel="noopener noreferrer">` +
              '<i class="mdi mdi-open-in-new" aria-hidden="true"></i></a>';
            return html;
          }
          return data;
        }
      }
    ];

    pendingSaveRequestsTable = $('#swh-origin-save-pending-requests').DataTable({
      ...dataTableCommonConfig,
      ajax: Urls.origin_save_requests_list('pending'),
      columns: columnsData,
      order: [[0, 'desc']],
      responsive: {
        details: {
          type: 'none'
        }
      }
    });
    enableRowSelection('#swh-origin-save-pending-requests');
    swh.webapp.addJumpToPagePopoverToDataTable(pendingSaveRequestsTable);

    columnsData.push({
      name: 'info',
      render: (data, type, row) => {
        let info = '';
        if (row.save_task_status === 'succeeded' || row.save_task_status === 'failed' ||
            row.note != null) {
          info += `<i class="mdi mdi-information-outline swh-save-request-info" aria-hidden="true"
                     style="cursor: pointer"
                     onclick="swh.save_code_now.displaySaveRequestInfo(event, ${row.id})"></i>`;
        }
        if (row.from_webhook) {
          info += `<i class="mdi mdi-webhook" aria-hidden="true"
                    title="save request created from webhook"></i>`;
        }
        return info;
      }
    });

    rejectedSaveRequestsTable = $('#swh-origin-save-rejected-requests').DataTable({
      ...dataTableCommonConfig,
      ajax: Urls.origin_save_requests_list('rejected'),
      columns: columnsData,
      order: [[0, 'desc']],
      responsive: {
        details: {
          type: 'none'
        }
      }
    });
    enableRowSelection('#swh-origin-save-rejected-requests');
    swh.webapp.addJumpToPagePopoverToDataTable(rejectedSaveRequestsTable);

    columnsData.splice(columnsData.length - 1, 0, {
      data: 'save_task_status',
      name: 'save_task_status'
    });

    acceptedSaveRequestsTable = $('#swh-origin-save-accepted-requests').DataTable({
      ...dataTableCommonConfig,
      ajax: Urls.origin_save_requests_list('accepted'),
      columns: columnsData,
      order: [[0, 'desc']],
      responsive: {
        details: {
          type: 'none'
        }
      }
    });
    enableRowSelection('#swh-origin-save-accepted-requests');
    swh.webapp.addJumpToPagePopoverToDataTable(acceptedSaveRequestsTable);

    $('#swh-authorized-origins-tab').on('shown.bs.tab', () => {
      authorizedOriginTable.draw();
    });

    $('#swh-unauthorized-origins-tab').on('shown.bs.tab', () => {
      unauthorizedOriginTable.draw();
    });

    $('#swh-save-requests-pending-tab').on('shown.bs.tab', () => {
      pendingSaveRequestsTable.draw();
    });

    $('#swh-save-requests-accepted-tab').on('shown.bs.tab', () => {
      acceptedSaveRequestsTable.draw();
    });

    $('#swh-save-requests-rejected-tab').on('shown.bs.tab', () => {
      rejectedSaveRequestsTable.draw();
    });

    $('#swh-save-requests-pending-tab').click(() => {
      pendingSaveRequestsTable.ajax.reload(null, false);
    });

    $('#swh-save-requests-accepted-tab').click(() => {
      acceptedSaveRequestsTable.ajax.reload(null, false);
    });

    $('#swh-save-requests-rejected-tab').click(() => {
      rejectedSaveRequestsTable.ajax.reload(null, false);
    });

    $('body').on('click', e => {
      if ($(e.target).parents('.popover').length > 0) {
        e.stopPropagation();
      } else if ($(e.target).parents('.swh-save-request-info').length === 0) {
        $('.swh-save-request-info').popover('dispose');
      }
    });

  });
}

export async function addAuthorizedOriginUrl() {
  const originUrl = $('#swh-authorized-url-prefix').val();
  const addOriginUrl = Urls.admin_origin_save_add_authorized_url(encodeURI(originUrl));
  try {
    const response = await csrfPost(addOriginUrl);
    handleFetchError(response);
    authorizedOriginTable.row.add({'url': originUrl}).draw();
    $('.swh-add-authorized-origin-status').html(
      htmlAlert('success', 'The origin url prefix has been successfully added in the authorized list.', true)
    );
  } catch (_) {
    $('.swh-add-authorized-origin-status').html(
      htmlAlert('warning', 'The provided origin url prefix is already registered in the authorized list.', true)
    );
  }
}

export async function removeAuthorizedOriginUrl() {
  const originUrl = $('#swh-authorized-origin-urls tr.selected').text();
  if (originUrl) {
    const removeOriginUrl = Urls.admin_origin_save_remove_authorized_url(encodeURI(originUrl));
    try {
      const response = await csrfPost(removeOriginUrl);
      handleFetchError(response);
      authorizedOriginTable.row('.selected').remove().draw();
    } catch (_) {}
  }
}

export async function addUnauthorizedOriginUrl() {
  const originUrl = $('#swh-unauthorized-url-prefix').val();
  const addOriginUrl = Urls.admin_origin_save_add_unauthorized_url(encodeURI(originUrl));
  try {
    const response = await csrfPost(addOriginUrl);
    handleFetchError(response);
    unauthorizedOriginTable.row.add({'url': originUrl}).draw();
    $('.swh-add-unauthorized-origin-status').html(
      htmlAlert('success', 'The origin url prefix has been successfully added in the unauthorized list.', true)
    );
  } catch (_) {
    $('.swh-add-unauthorized-origin-status').html(
      htmlAlert('warning', 'The provided origin url prefix is already registered in the unauthorized list.', true)
    );
  }
}

export async function removeUnauthorizedOriginUrl() {
  const originUrl = $('#swh-unauthorized-origin-urls tr.selected').text();
  if (originUrl) {
    const removeOriginUrl = Urls.admin_origin_save_remove_unauthorized_url(encodeURI(originUrl));
    try {
      const response = await csrfPost(removeOriginUrl);
      handleFetchError(response);
      unauthorizedOriginTable.row('.selected').remove().draw();
    } catch (_) {};
  }
}

export function acceptOriginSaveRequest() {
  const selectedRow = pendingSaveRequestsTable.row('.selected');
  if (selectedRow.length) {
    const acceptOriginSaveRequestCallback = async() => {
      const rowData = selectedRow.data();
      const acceptSaveRequestUrl = Urls.admin_origin_save_request_accept(rowData['visit_type'], encodeURI(rowData['origin_url']));
      await csrfPost(acceptSaveRequestUrl);
      pendingSaveRequestsTable.ajax.reload(null, false);
      // ensure to remove notification icon in sidebar admin menu when
      // there is no remaining pending requests
      setTimeout(() => {
        if ($('td.dt-empty').is(':visible')) {
          location.reload(true);
        }
      }, 100);
    };

    swh.webapp.showModalConfirm(
      'Accept origin save request ?',
      'Are you sure to accept this origin save request ?',
      acceptOriginSaveRequestCallback);
  }
}

const rejectModalHtml = `
<form id="swh-rejection-form">
  <div class="row">
    <label for="swh-rejection-reason" class="col-4 col-form-label">
      Rejection reason:
    </label>
    <div class="col-8">
      <select class="form-select" id="swh-rejection-reason">
        <option value="custom" selected>Custom</option>
        <option value="invalid-origin">Invalid origin</option>
        <option value="invalid-origin-type">Invalid origin type</option>
        <option value="origin-not-found">Origin not found</option>
      </select>
    </div>
  </div>
  <div class="row mt-3 mb-3">
    <textarea class="form-control" id="swh-rejection-text"></textarea>
  </div>
  <button type="submit" class="btn btn-secondary float-end" id="swh-rejection-submit">
    Reject
  </button>
</form>
`;

export function rejectOriginSaveRequest() {
  const selectedRow = pendingSaveRequestsTable.row('.selected');
  const rowData = selectedRow.data();
  if (selectedRow.length) {
    const rejectOriginSaveRequestCallback = async() => {
      $('#swh-web-modal-html').modal('hide');
      const rejectSaveRequestUrl = Urls.admin_origin_save_request_reject(
        rowData['visit_type'], encodeURI(rowData['origin_url']));
      await csrfPost(rejectSaveRequestUrl, {},
                     JSON.stringify({note: $('#swh-rejection-text').val()}));
      pendingSaveRequestsTable.ajax.reload(null, false);
    };

    let currentRejectionReason = 'custom';
    const rejectionTexts = {};
    swh.webapp.showModalHtml('Reject origin save request ?', rejectModalHtml);
    $('#swh-rejection-reason').on('change', (event) => {
      // backup current textarea value
      rejectionTexts[currentRejectionReason] = $('#swh-rejection-text').val();
      currentRejectionReason = event.target.value;
      let newRejectionText = '';
      if (rejectionTexts.hasOwnProperty(currentRejectionReason)) {
        // restore previous textarea value
        newRejectionText = rejectionTexts[currentRejectionReason];
      } else {
        // fill textarea with default text according to rejection type
        if (currentRejectionReason === 'invalid-origin') {
          newRejectionText = `The origin with URL ${rowData['origin_url']} is not ` +
            `a link to a  ${rowData['visit_type']} repository.`;
        } else if (currentRejectionReason === 'invalid-origin-type') {
          newRejectionText = `The origin with URL ${rowData['origin_url']} is not ` +
            `of type ${rowData['visit_type']}.`;
        } else if (currentRejectionReason === 'origin-not-found') {
          newRejectionText = `The origin with URL ${rowData['origin_url']} cannot be found.`;
        }
      }
      $('#swh-rejection-text').val(newRejectionText);
    });
    $('#swh-rejection-form').on('submit', (event) => {
      event.preventDefault();
      event.stopPropagation();
      // ensure confirmation modal will be displayed above the html modal
      $('#swh-web-modal-html').css('z-index', 4000);
      swh.webapp.showModalConfirm(
        'Reject origin save request ?',
        'Are you sure to reject this origin save request ?',
        rejectOriginSaveRequestCallback);
    });
  }
}

function removeOriginSaveRequest(requestTable) {
  const selectedRow = requestTable.row('.selected');
  if (selectedRow.length) {
    const requestId = selectedRow.data()['id'];
    const removeOriginSaveRequestCallback = async() => {
      const removeSaveRequestUrl = Urls.admin_origin_save_request_remove(requestId);
      await csrfPost(removeSaveRequestUrl);
      requestTable.ajax.reload(null, false);
    };

    swh.webapp.showModalConfirm(
      'Remove origin save request ?',
      'Are you sure to remove this origin save request ?',
      removeOriginSaveRequestCallback);
  }
}

export function removePendingOriginSaveRequest() {
  removeOriginSaveRequest(pendingSaveRequestsTable);
}

export function removeAcceptedOriginSaveRequest() {
  removeOriginSaveRequest(acceptedSaveRequestsTable);
}

export function removeRejectedOriginSaveRequest() {
  removeOriginSaveRequest(rejectedSaveRequestsTable);
}
