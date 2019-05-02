/**
 * Copyright (C) 2018  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import {handleFetchError, csrfPost} from 'utils/functions';

let authorizedOriginTable;
let unauthorizedOriginTable;
let pendingSaveRequestsTable;
let acceptedSaveRequestsTable;
let rejectedSaveRequestsTable;

function enableRowSelection(tableSel) {
  $(`${tableSel} tbody`).on('click', 'tr', function() {
    if ($(this).hasClass('selected')) {
      $(this).removeClass('selected');
    } else {
      $(`${tableSel} tr.selected`).removeClass('selected');
      $(this).addClass('selected');
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

    unauthorizedOriginTable = $('#swh-unauthorized-origin-urls').DataTable({
      serverSide: true,
      ajax: Urls.admin_origin_save_unauthorized_urls_list(),
      columns: [{data: 'url', name: 'url'}],
      scrollY: '50vh',
      scrollCollapse: true,
      info: false
    });
    enableRowSelection('#swh-unauthorized-origin-urls');

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
        data: 'origin_type',
        name: 'origin_type'
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
      }
    ];

    pendingSaveRequestsTable = $('#swh-origin-save-pending-requests').DataTable({
      serverSide: true,
      ajax: Urls.browse_origin_save_requests_list('pending'),
      searchDelay: 1000,
      columns: columnsData,
      scrollY: '50vh',
      scrollCollapse: true,
      order: [[0, 'desc']]
    });
    enableRowSelection('#swh-origin-save-pending-requests');

    rejectedSaveRequestsTable = $('#swh-origin-save-rejected-requests').DataTable({
      serverSide: true,
      ajax: Urls.browse_origin_save_requests_list('rejected'),
      searchDelay: 1000,
      columns: columnsData,
      scrollY: '50vh',
      scrollCollapse: true,
      order: [[0, 'desc']]
    });
    enableRowSelection('#swh-origin-save-rejected-requests');

    columnsData.push({
      data: 'save_task_status',
      name: 'save_task_status',
      render: (data, type, row) => {
        if (data === 'succeed') {
          let browseOriginUrl = Urls.browse_origin(row.origin_url);
          return `<a href="${browseOriginUrl}">${data}</a>`;
        }
        return data;
      }
    });

    acceptedSaveRequestsTable = $('#swh-origin-save-accepted-requests').DataTable({
      serverSide: true,
      ajax: Urls.browse_origin_save_requests_list('accepted'),
      searchDelay: 1000,
      columns: columnsData,
      scrollY: '50vh',
      scrollCollapse: true,
      order: [[0, 'desc']]
    });
    enableRowSelection('#swh-origin-save-accepted-requests');

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

  });
}

export function addAuthorizedOriginUrl() {
  let originUrl = $('#swh-authorized-url-prefix').val();
  let addOriginUrl = Urls.admin_origin_save_add_authorized_url(originUrl);
  csrfPost(addOriginUrl)
    .then(handleFetchError)
    .then(() => {
      authorizedOriginTable.row.add({'url': originUrl}).draw();
    })
    .catch(response => {
      swh.webapp.showModalMessage(
        'Duplicated origin url prefix',
        'The provided origin url prefix is already registered in the authorized list.');
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
    })
    .catch(() => {
      swh.webapp.showModalMessage(
        'Duplicated origin url prefix',
        'The provided origin url prefix is already registered in the unauthorized list.');
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
      let acceptSaveRequestUrl = Urls.admin_origin_save_request_accept(rowData['origin_type'], rowData['origin_url']);
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
      let rejectSaveRequestUrl = Urls.admin_origin_save_request_reject(rowData['origin_type'], rowData['origin_url']);
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
