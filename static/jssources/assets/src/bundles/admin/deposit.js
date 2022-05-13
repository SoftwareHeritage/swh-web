/**
 * Copyright (C) 2018-2022  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import {getHumanReadableDate} from 'utils/functions';

function genSwhLink(data, type, linkText = '') {
  if (type === 'display' && data && data.startsWith('swh')) {
    const browseUrl = Urls.browse_swhid(data);
    const formattedSWHID = data.replace(/;/g, ';<br/>');
    if (!linkText) {
      linkText = formattedSWHID;
    }
    return `<a href="${browseUrl}">${linkText}</a>`;
  }
  return data;
}

function genLink(data, type, openInNewTab = false, linkText = '') {
  if (type === 'display' && data) {
    const sData = encodeURI(data);
    if (!linkText) {
      linkText = sData;
    }
    let attrs = '';
    if (openInNewTab) {
      attrs = 'target="_blank" rel="noopener noreferrer"';
    }
    return `<a href="${sData}" ${attrs}>${linkText}</a>`;
  }
  return data;
}

export function initDepositAdmin(username, isStaff) {
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
            data: 'type',
            name: 'type'
          },
          {
            data: 'uri',
            name: 'uri',
            render: (data, type, row) => {
              const sanitizedURL = $.fn.dataTable.render.text().display(data);
              let swhLink = '';
              let originLink = '';
              if (row.swhid_context && data) {
                swhLink = genSwhLink(row.swhid_context, type, sanitizedURL);
              } else if (data) {
                swhLink = sanitizedURL;
              }
              if (data) {
                originLink = genLink(sanitizedURL, type, true,
                                     '<i class="mdi mdi-open-in-new" aria-hidden="true"></i>');
              }
              return swhLink + '&nbsp;' + originLink;
            }
          },
          {
            data: 'reception_date',
            name: 'reception_date',
            render: getHumanReadableDate
          },
          {
            data: 'status',
            name: 'status'
          },
          {
            data: 'raw_metadata',
            name: 'raw_metadata',
            render: (data, type, row) => {
              if (type === 'display') {
                if (row.raw_metadata) {
                  return `<button class="btn btn-default metadata">display</button>`;
                }
              }
              return data;
            }
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

    // Show a modal when the "metadata" button is clicked
    $('#swh-admin-deposit-list tbody').on('click', 'tr button.metadata', function() {
      var row = depositsTable.row(this.parentNode.parentNode).data();
      var metadata = row.raw_metadata;
      var escapedMetadata = $('<div/>').text(metadata).html();
      swh.webapp.showModalHtml(`Metadata of deposit ${row.id}`,
                               `<pre style="max-height: 75vh;"><code class="xml">${escapedMetadata}</code></pre>`,
                               '90%');
      swh.webapp.highlightCode();
    });

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
