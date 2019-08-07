/**
 * Copyright (C) 2019  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import '@cypress/code-coverage/support';

import {httpGetJson} from '../utils';

Cypress.Screenshot.defaults({
  screenshotOnRunFailure: false
});

before(function() {
  this.unarchivedRepo = {
    url: 'https://github.com/SoftwareHeritage/swh-web',
    revision: '7bf1b2f489f16253527807baead7957ca9e8adde',
    snapshot: 'd9829223095de4bb529790de8ba4e4813e38672d',
    rootDirectory: '7d887d96c0047a77e2e8c4ee9bb1528463677663',
    content: [{
      sha1git: 'b203ec39300e5b7e97b6e20986183cbd0b797859'
    }]
  };

  this.origin = [{
    url: 'https://github.com/memononen/libtess2',
    content: [{
      path: 'Source/tess.h'
    }, {
      path: 'premake4.lua'
    }],
    invalidSubDir: 'Source1'
  }, {
    url: 'https://github.com/wcoder/highlightjs-line-numbers.js',
    content: []
  }];

  cy.visit('/').window().then(win => {
    this.Urls = win.Urls;

    for (let origin of this.origin) {
      cy.visit(this.Urls.browse_origin_directory(origin.url))
        .window().then(async win => {
          const metadata = win.swh.webapp.getBrowsedSwhObjectMetadata();

          const apiUrl = Cypress.config().baseUrl + this.Urls.api_1_directory(metadata.directory);
          origin.dirContent = await httpGetJson(apiUrl);

          origin.rootDirectory = metadata.directory;
          origin.revision = metadata.revision;
          origin.snapshot = metadata.snapshot;
        });

      for (let content of origin.content) {
        cy.visit(this.Urls.browse_origin_content(origin.url, content.path))
          .window().then(win => {
            const metadata = win.swh.webapp.getBrowsedSwhObjectMetadata();

            content.name = metadata.filename;
            content.sha1git = metadata.sha1_git;
            content.directory = metadata.directory;

            content.rawFilePath = this.Urls.browse_content_raw(`sha1_git:${content.sha1git}`) +
                                `?filename=${encodeURIComponent(content.name)}`;

            cy.request(content.rawFilePath)
              .then((response) => {
                const fileText = response.body;
                const fileLines = fileText.split('\n');
                content.numberLines = fileLines.length;

                // If last line is empty its not shown
                if (!fileLines[content.numberLines - 1]) content.numberLines -= 1;
              });
          });
      }

    }
  });
});
