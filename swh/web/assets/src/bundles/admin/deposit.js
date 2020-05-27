/**
 * Copyright (C) 2018-2020  The Software Heritage developers
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

function filterDataWithExcludePattern(data, excludePattern) {
  /* Return true if the data is to be filtered, false otherwise.

    Args:
      data (dict): row dict data
      excludePattern (str): pattern to lookup in data columns

    Returns:
      true if the data is to be excluded (because it matches), false otherwise

   */
  if (excludePattern === '') {
    return false; // otherwise, everything gets excluded
  }
  for (const key in data) {
    let value = data[key];
    if ((typeof value === 'string' || value instanceof String) &&
        value.search(excludePattern) !== -1) {
      return true; // exclude the data from filtering
    }
  }
  return false;
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
        dom: '<<f<"#list-exclude">l>rt<"bottom"ip>>',
        // div#list-exclude is a custom filter added next to dataTable
        // initialization below through js dom manipulation, see
        // https://datatables.net/examples/advanced_init/dom_toolbar.html
        ajax: {
          url: Urls.admin_deposit_list(),
          // filtering data set depending on the exclude search input
          dataFilter: function(dataResponse) {
            /* Filter out data returned by the server to exclude entries
               matching the exclude pattern.

              Args
                dataResponse (str): the json response in string

              Returns:
                json response altered (in string)
             */
            //
            let data = jQuery.parseJSON(dataResponse);
            let excludePattern = $('#swh-admin-deposit-list-exclude-filter').val();
            let recordsFiltered = 0;
            let filteredData = [];
            for (const row of data.data) {
              if (filterDataWithExcludePattern(row, excludePattern)) {
                recordsFiltered += 1;
              } else {
                filteredData.push(row);
              }
            }
            // update data values
            data['recordsFiltered'] = recordsFiltered;
            data['data'] = filteredData;
            return JSON.stringify(data);
          }
        },
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
