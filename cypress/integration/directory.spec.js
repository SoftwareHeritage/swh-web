/**
 * Copyright (C) 2019  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import {httpGetJson} from '../utils';

const origin = 'https://github.com/memononen/libtess2';
const $ = Cypress.$;

let url, dirs, files;

describe('Directory Tests', function() {

  before(function() {
    url = this.Urls.browse_origin_directory(origin);
    cy.visit(url).window().then(async win => {
      const metadata = win.swh.webapp.getBrowsedSwhObjectMetadata();
      const apiUrl = Cypress.config().baseUrl + this.Urls.api_1_directory(metadata.directory);
      let dirContent = await httpGetJson(apiUrl);
      files = [];
      dirs = [];
      for (let entry of dirContent) {
        if (entry.type === 'file') {
          files.push(entry);
        } else {
          dirs.push(entry);
        }
      }
    });
  });

  beforeEach(function() {
    cy.visit(url);
  });

  it('should display all files and directories', function() {
    cy.get('.swh-directory')
      .should('have.length', dirs.length)
      .and('be.visible');
    cy.get('.swh-content')
      .should('have.length', files.length)
      .and('be.visible');
  });

  it('should display sizes for files', function() {
    cy.get('.swh-content')
      .parent('tr')
      .then((rows) => {
        for (let row of rows) {
          let text = $(row).children('td').eq(2).text();
          expect(text.trim()).to.not.be.empty;
        }
      });
  });

  it('should display readme when it is present', function() {
    cy.get('#readme-panel > .card-body')
      .should('be.visible')
      .and('have.class', 'swh-showdown')
      .and('not.be.empty')
      .and('not.contain', 'Readme bytes are not available');
  });

  it('should open subdirectory when clicked', function() {
    cy.get('.swh-directory')
      .first()
      .children('a')
      .click();

    cy.url()
      .should('include', url + dirs[0]['name']);

    cy.get('.swh-directory-table')
      .should('be.visible');
  });
});
