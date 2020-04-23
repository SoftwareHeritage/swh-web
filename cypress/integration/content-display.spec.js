/**
 * Copyright (C) 2019-2020  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

let origin;
let url;

describe('Test File Rendering', function() {
  before(function() {
    origin = this.origin[0];
    url = `${this.Urls.browse_origin_content()}?origin_url=${origin.url}&path=${origin.content[0].path}`;
  });

  beforeEach(function() {
    cy.visit(url);
  });

  it('should display correct file name', function() {
    cy.get('.swh-content-filename')
      .should('be.visible')
      .and('contain', origin.content[0].name)
      .and('have.css', 'background-color', 'rgb(242, 244, 245)');
  });

  it('should display all lines', function() {
    cy.get('.hljs-ln-code')
      .should('have.length', origin.content[0].numberLines)
      .and('be.visible')
      .and('have.css', 'background-color', 'rgba(0, 0, 0, 0)');
  });

  it('should show correct path', function() {
    // Array containing names of all the ancestor directories of the file
    const filePathArr = origin.content[0].path.slice(1, -1).slice('/');

    filePathArr.split('/').forEach(dirName => {
      cy.get('.swh-browse-bread-crumbs')
        .should('contain', dirName);
    });
  });

  it('should have links to all ancestor directories', function() {
    const rootDirUrl = `${this.Urls.browse_origin_directory()}?origin_url=${origin.url}`;
    cy.get(`a[href='${rootDirUrl}']`)
      .should('be.visible');

    const splittedPath = origin.content[0].path.split('/');
    for (let i = 2; i < splittedPath.length; ++i) {

      const subDirPath = splittedPath.slice(1, i).join('/');
      const subDirUrl = `${this.Urls.browse_origin_directory()}?origin_url=${origin.url}&path=${subDirPath}`;

      cy.get(`a[href='${subDirUrl}']`)
        .should('be.visible');
    }

  });

  it('should have correct url to raw file', function() {
    cy.get(`a[href='${origin.content[0].rawFilePath}']`)
      .should('be.visible');
  });
});
