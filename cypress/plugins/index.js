/**
 * Copyright (C) 2019-2022  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

const axios = require('axios');
const fs = require('fs');

async function httpGet(url) {
  const response = await axios.get(url);
  return response.data;
}

async function getMetadataForOrigin(originUrl, baseUrl) {
  const originVisitsApiUrl = `${baseUrl}/api/1/origin/${originUrl}/visits`;
  const originVisits = await httpGet(originVisitsApiUrl);
  const lastVisit = originVisits[0];
  const snapshotApiUrl = `${baseUrl}/api/1/snapshot/${lastVisit.snapshot}`;
  const lastOriginSnapshot = await httpGet(snapshotApiUrl);
  let revision = lastOriginSnapshot.branches.HEAD.target;
  if (lastOriginSnapshot.branches.HEAD.target_type === 'alias') {
    revision = lastOriginSnapshot.branches[revision].target;
  }
  const revisionApiUrl = `${baseUrl}/api/1/revision/${revision}`;
  const lastOriginHeadRevision = await httpGet(revisionApiUrl);
  return {
    'directory': lastOriginHeadRevision.directory,
    'revision': lastOriginHeadRevision.id,
    'snapshot': lastOriginSnapshot.id
  };
};

module.exports = (on, config) => {
  require('@cypress/code-coverage/task')(on, config);
  // produce JSON files prior launching browser in order to dynamically generate tests
  on('before:browser:launch', function(browser, launchOptions) {
    return new Promise((resolve) => {
      const p1 = axios.get(`${config.baseUrl}/tests/data/content/code/extensions/`);
      const p2 = axios.get(`${config.baseUrl}/tests/data/content/code/filenames/`);
      Promise.all([p1, p2])
        .then(function(responses) {
          fs.writeFileSync('cypress/fixtures/source-file-extensions.json', JSON.stringify(responses[0].data));
          fs.writeFileSync('cypress/fixtures/source-file-names.json', JSON.stringify(responses[1].data));
          resolve();
        });
    });
  });
  on('task', {
    getSwhTestsData: async() => {
      if (!global.swhTestsData) {
        const swhTestsData = {};
        swhTestsData.unarchivedRepo = {
          url: 'https://github.com/SoftwareHeritage/swh-web',
          type: 'git',
          revision: '7bf1b2f489f16253527807baead7957ca9e8adde',
          snapshot: 'd9829223095de4bb529790de8ba4e4813e38672d',
          rootDirectory: '7d887d96c0047a77e2e8c4ee9bb1528463677663',
          content: [{
            sha1git: 'b203ec39300e5b7e97b6e20986183cbd0b797859'
          }]
        };

        swhTestsData.origin = [{
          url: 'https://github.com/memononen/libtess2',
          type: 'git',
          content: [{
            path: 'Source/tess.h'
          }, {
            path: 'premake4.lua'
          }],
          directory: [{
            path: 'Source',
            id: 'cd19126d815470b28919d64b2a8e6a3e37f900dd'
          }],
          revisions: [],
          invalidSubDir: 'Source1'
        }, {
          url: 'https://github.com/wcoder/highlightjs-line-numbers.js',
          type: 'git',
          content: [{
            path: 'src/highlightjs-line-numbers.js'
          }],
          directory: [],
          revisions: ['1c480a4573d2a003fc2630c21c2b25829de49972'],
          release: {
            name: 'v2.6.0',
            id: '6877028d6e5412780517d0bfa81f07f6c51abb41',
            directory: '5b61d50ef35ca9a4618a3572bde947b8cccf71ad'
          }
        }];

        for (const origin of swhTestsData.origin) {

          const metadata = await getMetadataForOrigin(origin.url, config.baseUrl);
          const directoryApiUrl = `${config.baseUrl}/api/1/directory/${metadata.directory}`;

          origin.dirContent = await httpGet(directoryApiUrl);
          origin.rootDirectory = metadata.directory;
          origin.revisions.push(metadata.revision);
          origin.snapshot = metadata.snapshot;

          for (const content of origin.content) {

            const contentPathApiUrl = `${config.baseUrl}/api/1/directory/${origin.rootDirectory}/${content.path}`;
            const contentMetaData = await httpGet(contentPathApiUrl);

            content.name = contentMetaData.name.split('/').slice(-1)[0];
            content.sha1git = contentMetaData.target;
            content.directory = contentMetaData.dir_id;

            const rawFileUrl = `${config.baseUrl}/browse/content/sha1_git:${content.sha1git}/raw/?filename=${content.name}`;
            const fileText = await httpGet(rawFileUrl);
            const fileLines = fileText.split('\n');
            content.numberLines = fileLines.length;

            if (!fileLines[content.numberLines - 1]) {
              // If last line is empty its not shown
              content.numberLines -= 1;
            }
          }
        }
        global.swhTestsData = swhTestsData;
      }
      return global.swhTestsData;
    }
  });
  return config;
};
