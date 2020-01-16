/**
 * Copyright (C) 2018-2019  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

function genSwhLink(data, type) {
  if (type === 'display') {
    if (data && data.startsWith('swh')) {
      let browseUrl = Urls.browse_swh_id(data);
      return `<a href="${browseUrl}">${data}</a>`;
    }
  }
  return data;
}

export function initDepositAdmin() {
  let depositsTable;
  $(document).ready(() => {
    $.fn.dataTable.ext.errMode = 'none';
    depositsTable = $('#swh-admin-deposit-list')
      .on('error.dt', (e, settings, techNote, message) => {
        $('#swh-admin-deposit-list-error').text(message);
      })
      .DataTable({
        serverSide: true,
        ajax: Urls.admin_deposit_list(),
        columns: [
          {
            data: 'id',
            name: 'id'
          },
          {
            data: 'swh_id_context',
            name: 'swh_id_context',
            render: (data, type, row) => {
              if (data && type === 'display') {
                let originPattern = ';origin=';
                let originPatternIdx = data.indexOf(originPattern);
                if (originPatternIdx !== -1) {
                  let originUrl = data.slice(originPatternIdx + originPattern.length);
                  return `<a href="${originUrl}">${originUrl}</a>`;
                }
              }
              return data;
            }
          },
          {
            data: 'reception_date',
            name: 'reception_date',
            render: (data, type, row) => {
              if (type === 'display') {
                let date = new Date(data);
                return date.toLocaleString();
              }
              return data;
            }
          },
          {
            data: 'status',
            name: 'status'
          },
          {
            data: 'status_detail',
            name: 'status_detail',
            render: (data, type, row) => {
              if (type === 'display' && data) {
                let text = data;
                if (typeof data === 'object') {
                  text = JSON.stringify(data, null, 4);
                }
                return `<div style="width: 200px; white-space: pre; overflow-x: auto;">${text}</div>`;
              }
              return data;
            },
            orderable: false,
            visible: false
          },
          {
            data: 'swh_anchor_id',
            name: 'swh_anchor_id',
            render: (data, type, row) => {
              return genSwhLink(data, type);
            },
            orderable: false
          },
          {
            data: 'swh_anchor_id_context',
            name: 'swh_anchor_id_context',
            render: (data, type, row) => {
              return genSwhLink(data, type);
            },
            orderable: false,
            visible: false
          },
          {
            data: 'swh_id',
            name: 'swh_id',
            render: (data, type, row) => {
              return genSwhLink(data, type);
            },
            orderable: false,
            visible: false
          },
          {
            data: 'swh_id_context',
            name: 'swh_id_context',
            render: (data, type, row) => {
              return genSwhLink(data, type);
            },
            orderable: false,
            visible: false
          }
        ],
        scrollX: true,
        scrollY: '50vh',
        scrollCollapse: true,
        order: [[0, 'desc']]
      });
    depositsTable.draw();
  });

  $('a.toggle-col').on('click', function(e) {
    e.preventDefault();
    var column = depositsTable.column($(this).attr('data-column'));
    column.visible(!column.visible());
    if (column.visible()) {
      $(this).removeClass('col-hidden');
    } else {
      $(this).addClass('col-hidden');
    }
  });

}
