/**
 * Copyright (C) 2018-2020  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import {handleFetchError, csrfPost, htmlAlert} from 'utils/functions';
import {swhSpinnerSrc} from 'utils/constants';

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
      serverSide: true,
      ajax: Urls.admin_origin_save_authorized_urls_list(),
      columns: [{data: 'url', name: 'url'}],
      scrollY: '50vh',
      scrollCollapse: true,
      info: false
    });
    enableRowSelection('#swh-authorized-origin-urls');
    swh.webapp.addJumpToPagePopoverToDataTable(authorizedOriginTable);

    unauthorizedOriginTable = $('#swh-unauthorized-origin-urls').DataTable({
      serverSide: true,
      ajax: Urls.admin_origin_save_unauthorized_urls_list(),
      columns: [{data: 'url', name: 'url'}],
      scrollY: '50vh',
      scrollCollapse: true,
      info: false
    });
    enableRowSelection('#swh-unauthorized-origin-urls');
    swh.webapp.addJumpToPagePopoverToDataTable(unauthorizedOriginTable);

    let columnsData = [
      {
        data: 'id',
        name: 'id',
        visible: false,
        searchable: false
      },
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
      }
    ];

    pendingSaveRequestsTable = $('#swh-origin-save-pending-requests').DataTable({
      serverSide: true,
      processing: true,
      language: {
        processing: `<img src="${swhSpinnerSrc}"></img>`
      },
      ajax: Urls.origin_save_requests_list('pending'),
      searchDelay: 1000,
      columns: columnsData,
      scrollY: '50vh',
      scrollCollapse: true,
      order: [[0, 'desc']],
      responsive: {
        details: {
          type: 'none'
        }
      }
    });
    enableRowSelection('#swh-origin-save-pending-requests');
    swh.webapp.addJumpToPagePopoverToDataTable(pendingSaveRequestsTable);

    rejectedSaveRequestsTable = $('#swh-origin-save-rejected-requests').DataTable({
      serverSide: true,
      processing: true,
      language: {
        processing: `<img src="${swhSpinnerSrc}"></img>`
      },
      ajax: Urls.origin_save_requests_list('rejected'),
      searchDelay: 1000,
      columns: columnsData,
      scrollY: '50vh',
      scrollCollapse: true,
      order: [[0, 'desc']],
      responsive: {
        details: {
          type: 'none'
        }
      }
    });
    enableRowSelection('#swh-origin-save-rejected-requests');
    swh.webapp.addJumpToPagePopoverToDataTable(rejectedSaveRequestsTable);

    columnsData.push({
      data: 'save_task_status',
      name: 'save_task_status'
    });

    columnsData.push({
      name: 'info',
      render: (data, type, row) => {
        if (row.save_task_status === 'succeeded' || row.save_task_status === 'failed') {
          return '<i class="mdi mdi-information-outline swh-save-request-info" aria-hidden="true" style="cursor: pointer"' +
                  `onclick="swh.save.displaySaveRequestInfo(event, ${row.id})"></i>`;
        } else {
          return '';
        }
      }
    });

    acceptedSaveRequestsTable = $('#swh-origin-save-accepted-requests').DataTable({
      serverSide: true,
      processing: true,
      language: {
        processing: `<img src="${swhSpinnerSrc}"></img>`
      },
      ajax: Urls.origin_save_requests_list('accepted'),
      searchDelay: 1000,
      columns: columnsData,
      scrollY: '50vh',
      scrollCollapse: true,
      order: [[0, 'desc']],
      responsive: {
        details: {
          type: 'none'
        }
      }
    });
    enableRowSelection('#swh-origin-save-accepted-requests');
    swh.webapp.addJumpToPagePopoverToDataTable(acceptedSaveRequestsTable);

    $('#swh-origin-save-requests-nav-item').on('shown.bs.tab', () => {
      pendingSaveRequestsTable.draw();
    });

    $('#swh-origin-save-url-filters-nav-item').on('shown.bs.tab', () => {
      authorizedOriginTable.draw();
    });

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
        event.stopPropagation();
      } else if ($(e.target).parents('.swh-save-request-info').length === 0) {
        $('.swh-save-request-info').popover('dispose');
      }
    });

  });
}

export function addAuthorizedOriginUrl() {
  let originUrl = $('#swh-authorized-url-prefix').val();
  let addOriginUrl = Urls.admin_origin_save_add_authorized_url(originUrl);
  csrfPost(addOriginUrl)
    .then(handleFetchError)
    .then(() => {
      authorizedOriginTable.row.add({'url': originUrl}).draw();
      $('.swh-add-authorized-origin-status').html(
        htmlAlert('success', 'The origin url prefix has been successfully added in the authorized list.', true)
      );
    })
    .catch(response => {
      $('.swh-add-authorized-origin-status').html(
        htmlAlert('warning', 'The provided origin url prefix is already registered in the authorized list.', true)
      );
    });
}

export function removeAuthorizedOriginUrl() {
  let originUrl = $('#swh-authorized-origin-urls tr.selected').text();
  if (originUrl) {
    let removeOriginUrl = Urls.admin_origin_save_remove_authorized_url(originUrl);
    csrfPost(removeOriginUrl)
      .then(handleFetchError)
      .then(() => {
        authorizedOriginTable.row('.selected').remove().draw();
      })
      .catch(() => {});
  }
}

export function addUnauthorizedOriginUrl() {
  let originUrl = $('#swh-unauthorized-url-prefix').val();
  let addOriginUrl = Urls.admin_origin_save_add_unauthorized_url(originUrl);
  csrfPost(addOriginUrl)
    .then(handleFetchError)
    .then(() => {
      unauthorizedOriginTable.row.add({'url': originUrl}).draw();
      $('.swh-add-unauthorized-origin-status').html(
        htmlAlert('success', 'The origin url prefix has been successfully added in the unauthorized list.', true)
      );
    })
    .catch(() => {
      $('.swh-add-unauthorized-origin-status').html(
        htmlAlert('warning', 'The provided origin url prefix is already registered in the unauthorized list.', true)
      );
    });
}

export function removeUnauthorizedOriginUrl() {
  let originUrl = $('#swh-unauthorized-origin-urls tr.selected').text();
  if (originUrl) {
    let removeOriginUrl = Urls.admin_origin_save_remove_unauthorized_url(originUrl);
    csrfPost(removeOriginUrl)
      .then(handleFetchError)
      .then(() => {
        unauthorizedOriginTable.row('.selected').remove().draw();
      })
      .catch(() => {});
  }
}

export function acceptOriginSaveRequest() {
  let selectedRow = pendingSaveRequestsTable.row('.selected');
  if (selectedRow.length) {
    let acceptOriginSaveRequestCallback = () => {
      let rowData = selectedRow.data();
      let acceptSaveRequestUrl = Urls.admin_origin_save_request_accept(rowData['visit_type'], rowData['origin_url']);
      csrfPost(acceptSaveRequestUrl)
        .then(() => {
          pendingSaveRequestsTable.ajax.reload(null, false);
        });
    };

    swh.webapp.showModalConfirm(
      'Accept origin save request ?',
      'Are you sure to accept this origin save request ?',
      acceptOriginSaveRequestCallback);
  }
}

export function rejectOriginSaveRequest() {
  let selectedRow = pendingSaveRequestsTable.row('.selected');
  if (selectedRow.length) {
    let rejectOriginSaveRequestCallback = () => {
      let rowData = selectedRow.data();
      let rejectSaveRequestUrl = Urls.admin_origin_save_request_reject(rowData['visit_type'], rowData['origin_url']);
      csrfPost(rejectSaveRequestUrl)
        .then(() => {
          pendingSaveRequestsTable.ajax.reload(null, false);
        });
    };

    swh.webapp.showModalConfirm(
      'Reject origin save request ?',
      'Are you sure to reject this origin save request ?',
      rejectOriginSaveRequestCallback);
  }
}

function removeOriginSaveRequest(requestTable) {
  let selectedRow = requestTable.row('.selected');
  if (selectedRow.length) {
    let requestId = selectedRow.data()['id'];
    let removeOriginSaveRequestCallback = () => {
      let removeSaveRequestUrl = Urls.admin_origin_save_request_remove(requestId);
      csrfPost(removeSaveRequestUrl)
        .then(() => {
          requestTable.ajax.reload(null, false);
        });
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
