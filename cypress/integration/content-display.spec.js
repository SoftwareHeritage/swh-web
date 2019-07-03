/**
 * Copyright (C) 2019  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

const origin = 'https://github.com/memononen/libtess2';
const contentPath = 'Source/tess.h';

let fileName, filePath, sha1git, rawFilePath, numberLines, originUrl;

let url;

describe('Test File Rendering', function() {
  before(function() {
    url = this.Urls.browse_origin_content(origin, contentPath);

    cy.visit(url);
    cy.window().then(async win => {
      const metadata = win.swh.webapp.getBrowsedSwhObjectMetadata();

      fileName = metadata.filename;
      filePath = metadata.path;
      originUrl = metadata['origin url'];
      sha1git = metadata.sha1_git;
      rawFilePath = this.Urls.browse_content_raw(`sha1_git:${sha1git}`) +
                    `?filename=${encodeURIComponent(fileName)}`;

      cy.request(rawFilePath)
        .then((response) => {
          const fileText = response.body;
          const fileLines = fileText.split('\n');
          numberLines = fileLines.length;

          // If last line is empty its not shown
          if (!fileLines[numberLines - 1]) numberLines -= 1;
        });
    });
  });

  beforeEach(function() {
    cy.visit(url);
  });

  it('should display correct file name', function() {
    cy.get('.swh-content-filename')
      .should('be.visible')
      .and('contain', fileName)
      .and('have.css', 'background-color', 'rgb(242, 244, 245)');
  });

  it('should display all lines', function() {
    cy.get('.hljs-ln-code')
      .should('have.length', numberLines)
      .and('be.visible')
      .and('have.css', 'background-color', 'rgba(0, 0, 0, 0)');
  });

  it('should show correct path', function() {
    // Array containing names of all the ancestor directories of the file
    const filePathArr = filePath.slice(1, -1).slice('/');

    filePathArr.split('/').forEach(dirName => {
      cy.get('.swh-browse-bread-crumbs')
        .should('contain', dirName);
    });
  });

  it('should have links to all ancestor directories', function() {
    const rootDirUrl = this.Urls.browse_origin_directory(originUrl);
    cy.get(`a[href='${rootDirUrl}']`)
      .should('be.visible');

    let splittedPath = filePath.split('/');
    for (let i = 2; i < splittedPath.length; ++i) {

      const subDirPath = splittedPath.slice(1, i).join('/');
      const subDirUrl = this.Urls.browse_origin_directory(originUrl, subDirPath);

      cy.get(`a[href='${subDirUrl}']`)
        .should('be.visible');
    }

  });

  it('should have correct url to raw file', function() {
    cy.get(`a[href='${rawFilePath}']`)
      .should('be.visible');
  });
});
