/**
 * Copyright (C) 2019  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

const axios = require('axios');
const fs = require('fs');

module.exports = (on, config) => {
  require('@cypress/code-coverage/task')(on, config);
  // produce JSON files prior launching browser in order to dynamically generate tests
  on('before:browser:launch', function(browser, launchOptions) {
    return new Promise((resolve) => {
      let p1 = axios.get(`${config.baseUrl}/tests/data/content/code/extensions/`);
      let p2 = axios.get(`${config.baseUrl}/tests/data/content/code/filenames/`);
      Promise.all([p1, p2])
        .then(function(responses) {
          fs.writeFileSync('cypress/fixtures/source-file-extensions.json', JSON.stringify(responses[0].data));
          fs.writeFileSync('cypress/fixtures/source-file-names.json', JSON.stringify(responses[1].data));
          resolve();
        });
    });
  });
  return config;
};
