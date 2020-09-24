/**
 * Copyright (C) 2018-2020  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

function genSwhLink(data, type) {
  if (type === 'display') {
    if (data && data.startsWith('swh')) {
      const browseUrl = Urls.browse_swhid(data);
      const formattedSWHID = data.replace(/;/g, ';<br/>');
      return `<a href="${browseUrl}">${formattedSWHID}</a>`;
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
        processing: true,
        // let's define the order of table options display
        // f: (f)ilter
        // l: (l)ength changing
        // r: p(r)ocessing
        // t: (t)able
        // i: (i)nfo
        // p: (p)agination
        // see https://datatables.net/examples/basic_init/dom.html
        dom: '<<"d-flex justify-content-between align-items-center"f' +
             '<"#list-exclude">l>rt<"bottom"ip>>',
        // div#list-exclude is a custom filter added next to dataTable
        // initialization below through js dom manipulation, see
        // https://datatables.net/examples/advanced_init/dom_toolbar.html
        ajax: {
          url: Urls.admin_deposit_list(),
          data: d => {
            d.excludePattern = $('#swh-admin-deposit-list-exclude-filter').val();
          }
        },
        columns: [
          {
            data: 'id',
            name: 'id'
          },
          {
            data: 'swhid_context',
            name: 'swhid_context',
            render: (data, type, row) => {
              if (data && type === 'display') {
                let originPattern = ';origin=';
                let originPatternIdx = data.indexOf(originPattern);
                if (originPatternIdx !== -1) {
                  let originUrl = data.slice(originPatternIdx + originPattern.length);
                  let nextSepPattern = ';';
                  let nextSepPatternIdx = originUrl.indexOf(nextSepPattern);
                  if (nextSepPatternIdx !== -1) { /* Remove extra context */
                    originUrl = originUrl.slice(0, nextSepPatternIdx);
                  }
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
            data: 'swhid',
            name: 'swhid',
            render: (data, type, row) => {
              return genSwhLink(data, type);
            },
            orderable: false,
            visible: false
          },
          {
            data: 'swhid_context',
            name: 'swhid_context',
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

    // Some more customization is needed on the table
    $('div#list-exclude').html(`<div id="swh-admin-deposit-list-exclude-wrapper">
    <div id="swh-admin-deposit-list-exclude-div-wrapper" class="dataTables_filter">
      <label>
        Exclude:<input id="swh-admin-deposit-list-exclude-filter"
                       type="search"
                       value="check-deposit"
                       class="form-control form-control-sm"
                       placeholder="exclude-pattern" aria-controls="swh-admin-deposit-list">
          </input>
      </label>
    </div>
  </div>
`);
    // Adding exclusion pattern update behavior, when typing, update search
    $('#swh-admin-deposit-list-exclude-filter').keyup(function() {
      depositsTable.draw();
    });
    // at last draw the table
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
