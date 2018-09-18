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
            data: 'external_id',
            name: 'external_id',
            render: (data, type, row) => {
              if (type === 'display') {
                if (data && data.startsWith('hal')) {
                  return `<a href="https://hal.archives-ouvertes.fr/${data}">${data}</a>`;
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
            orderable: false
          },
          {
            data: 'swh_id',
            name: 'swh_id',
            render: (data, type, row) => {
              if (type === 'display') {
                if (data && data.startsWith('swh')) {
                  let browseUrl = Urls.browse_swh_id(data);
                  return `<a href="${browseUrl}">${data}</a>`;
                }
              }
              return data;
            }
          }
        ],
        scrollY: '50vh',
        scrollCollapse: true,
        order: [[0, 'desc']]
      });
    depositsTable.draw();
  });
}
