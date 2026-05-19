/**
 * Copyright (C) 2022-2026  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import {genLink, getHumanReadableDate, dtUpdateSettings} from 'utils/functions';
import {dataTableCommonConfig} from 'utils/constants';

export function onModerationPageLoad() {
  populateModerationList();
}

export async function populateModerationList() {
  $('#swh-add-forge-now-moderation-list')
    .on('error.dt', (e, settings, techNote, message) => {
      $('#swh-add-forge-now-moderation-list-error').text(message);
    })
    .DataTable(dtUpdateSettings({
      ...dataTableCommonConfig,
      searching: true,
      dom: '<"row mb-2"<"col-sm-3"l><"col-sm-6"><"col-sm-3"f>>' +
           '<"row"<"col-sm-12"tr>>' +
           '<"row mt-2"<"col-sm-5"i><"col-sm-7"p>>',
      ajax: {
        'url': Urls.add_forge_request_list_datatables(),
      },
      rowId: 'id',
      columns: [
        {
          data: 'id',
          name: 'id',
          render: function(data, type, row, meta) {
            const dashboardUrl = Urls.add_forge_now_request_dashboard(data);
            return `<a href=${dashboardUrl}>${data}</a>`;
          },
        },
        {
          data: 'submission_date',
          name: 'submission_date',
          urlParam: 'submission',
          render: getHumanReadableDate,
        },
        {
          data: 'forge_type',
          name: 'forge_type',
          urlParam: 'type',
          render: $.fn.dataTable.render.text(),
        },
        {
          data: 'forge_url',
          name: 'forge_url',
          urlParam: 'url',
          render: (data, type, row) => {
            const sanitizedURL = $.fn.dataTable.render.text().display(data);
            return genLink(sanitizedURL, type, true);
          },
        },
        {
          data: 'last_moderator',
          name: 'last_moderator',
          urlParam: 'moderator',
          render: $.fn.dataTable.render.text(),
        },
        {
          data: 'last_modified_date',
          name: 'last_modified_date',
          urlParam: 'modified',
          render: getHumanReadableDate,
        },
        {
          data: 'status',
          name: 'status',
          render: function(data, type, row, meta) {
            return swh.add_forge_now.formatRequestStatusName(data);
          },
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
          },
          orderable: false,
        },
      ],
      order: [[0, 'desc']],
    }));
}
