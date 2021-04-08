/**
 * Copyright (C) 2020  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import './status-widget.css';

const statusCodeColor = {
  '100': 'green', // Operational
  '200': 'blue', // Scheduled Maintenance
  '300': 'yellow', // Degraded Performance
  '400': 'yellow', // Partial Service Disruption
  '500': 'red', // Service Disruption
  '600': 'red' // Security Event
};

export function initStatusWidget(statusDataURL) {
  $('.swh-current-status-indicator').ready(() => {
    let maxStatusCode = '';
    let maxStatusDescription = '';
    let sc = '';
    let sd = '';
    fetch(statusDataURL)
      .then(resp => resp.json())
      .then(data => {
        for (let s of data.result.status) {
          sc = s.status_code;
          sd = s.status;
          if (maxStatusCode < sc) {
            maxStatusCode = sc;
            maxStatusDescription = sd;
          }
        }
        if (maxStatusCode === '') {
          $('.swh-current-status').remove();
          return;
        }
        $('.swh-current-status-indicator').removeClass('green');
        $('.swh-current-status-indicator').addClass(statusCodeColor[maxStatusCode]);
        $('#swh-current-status-description').text(maxStatusDescription);
      })
      .catch(e => {
        console.log(e);
        $('.swh-current-status').remove();
      });

  });
}
