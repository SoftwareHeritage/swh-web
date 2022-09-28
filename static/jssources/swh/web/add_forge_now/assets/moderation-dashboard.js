/**
 * Copyright (C) 2022  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import {genLink, getHumanReadableDate} from 'utils/functions';

export function onModerationPageLoad() {
  populateModerationList();
}

export async function populateModerationList() {
  $('#swh-add-forge-now-moderation-list')
    .on('error.dt', (e, settings, techNote, message) => {
      $('#swh-add-forge-now-moderation-list-error').text(message);
    })
    .DataTable({
      serverSide: true,
      processing: true,
      searching: true,
      dom: '<<"d-flex justify-content-between align-items-center"f' +
        '<"#list-exclude">l>rt<"bottom"ip>>',
      ajax: {
        'url': Urls.add_forge_request_list_datatables()
      },
      columns: [
        {
          data: 'id',
          name: 'id',
          render: function(data, type, row, meta) {
            const dashboardUrl = Urls.add_forge_now_request_dashboard(data);
            return `<a href=${dashboardUrl}>${data}</a>`;
          }
        },
        {
          data: 'submission_date',
          name: 'submission_date',
          render: getHumanReadableDate
        },
        {
          data: 'forge_type',
          name: 'forge_type',
          render: $.fn.dataTable.render.text()
        },
        {
          data: 'forge_url',
          name: 'forge_url',
          render: (data, type, row) => {
            const sanitizedURL = $.fn.dataTable.render.text().display(data);
            return genLink(sanitizedURL, type, true);
          }
        },
        {
          data: 'last_moderator',
          name: 'last_moderator',
          render: $.fn.dataTable.render.text()
        },
        {
          data: 'last_modified_date',
          name: 'last_modified_date',
          render: getHumanReadableDate
        },
        {
          data: 'status',
          name: 'status',
          render: function(data, type, row, meta) {
            return swh.add_forge_now.formatRequestStatusName(data);
          }
        },
        {
          render: (data, type, row) => {
            let html = '<div class="d-flex">';
            const dashboardUrl = Urls.add_forge_now_request_dashboard(row.id);
            html += `<a class="swh-forge-request-dashboard-link" href="${dashboardUrl}" title="Go to request dashboard">` +
                    '<i class="mdi mdi-square-edit-outline" aria-hidden="true"></i></a>';
            if (row.status === 'FIRST_ORIGIN_LOADED') {
              const sanitizedURL = $.fn.dataTable.render.text().display(row.forge_url);
              let originsSearchUrl = `${Urls.browse_search()}?q=${encodeURIComponent(sanitizedURL)}`;
              originsSearchUrl += '&with_visit=true&with_content=true';
              html += `<a href="${originsSearchUrl}" target="_blank" rel="noopener noreferrer" ` +
                     'class="swh-search-forge-origins" title="Search for origins listed from that forge">' +
                     '<i class="mdi mdi-magnify" aria-hidden="true"></i></a>';
            }
            html += '</div>';
            return html;
          }
        }
      ],
      order: [[0, 'desc']]
    });
}
