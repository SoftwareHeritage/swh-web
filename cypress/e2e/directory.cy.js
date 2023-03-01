/**
 * Copyright (C) 2019-2023  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

const $ = Cypress.$;

let origin;

let url;
const dirs = [];
const files = [];

describe('Directory Tests', function() {
  before(function() {
    origin = this.origin[0];

    url = `${this.Urls.browse_origin_directory()}?origin_url=${origin.url}`;

    for (const entry of origin.dirContent) {
      if (entry.type === 'file') {
        files.push(entry);
      } else {
        dirs.push(entry);
      }
    }
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
        for (const row of rows) {
          const text = $(row).children('td').eq(2).text();
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
      .should('include', `${url}&path=${dirs[0]['name']}`);

    cy.get('.swh-directory-table')
      .should('be.visible');
  });

  it('should have metadata available from javascript', function() {
    cy.window().then(win => {
      const metadata = win.swh.webapp.getBrowsedSwhObjectMetadata();
      expect(metadata).to.not.be.empty;
      expect(metadata).to.have.any.keys('directory');
    });
  });

  it('should fix internal links in markdown readme', function() {
    const mainReadme = `
# README

## Section

[link to file in repository](files/foo)

### Sub-section

[link to directory in repository](files)
`;

    const barReadme = `
# README

## Section

[link to files/foo file](../files/foo)

### Sub-section

[link to repository root directory](../)
`;

    const originUrl = 'https://git.example.org/md-readme-internal-links-fix';
    const contents = [{'path': 'README.md', 'data': mainReadme},
                      {'path': 'files/foo', 'data': 'foo'},
                      {'path': 'bar/README.md', 'data': barReadme}];

    cy.request('POST',
               `${this.Urls.tests_add_origin_with_contents()}?origin_url=${originUrl}`,
               contents)
      .then((resp) => {
        expect(resp.status).to.eq(200);
        let url = `${this.Urls.browse_origin_directory()}?origin_url=${originUrl}`;
        cy.visit(url);
        cy.get('#readme-panel > .card-body')
          .should('be.visible');
        let contentUrl = this.Urls.browse_origin_directory() +
          `?origin_url=${encodeURIComponent(originUrl)}` +
          `&path=${encodeURIComponent('files/foo')}`;
        cy.get('#section + p a')
          .should('have.attr', 'href', contentUrl);
        let directoryUrl = this.Urls.browse_origin_directory() +
          `?origin_url=${encodeURIComponent(originUrl)}&path=files`;
        cy.get('#subsection + p a')
          .should('have.attr', 'href', directoryUrl);

        url = `${this.Urls.browse_origin_directory()}?origin_url=${originUrl}&path=bar`;
        cy.visit(url);
        cy.get('#readme-panel > .card-body')
          .should('be.visible');
        contentUrl = this.Urls.browse_origin_directory() +
          `?origin_url=${encodeURIComponent(originUrl)}` +
          `&path=${encodeURIComponent('files/foo')}`;
        cy.get('#section + p a')
          .should('have.attr', 'href', contentUrl);
        directoryUrl = this.Urls.browse_origin_directory() +
          `?origin_url=${encodeURIComponent(originUrl)}`;
        cy.get('#subsection + p a')
          .should('have.attr', 'href', directoryUrl);
      });
  });

});
