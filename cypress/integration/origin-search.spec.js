/**
 * Copyright (C) 2019  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

const nonExistentText = 'NoMatchExists';

let origin;
let url;

function doSearch(searchText) {
  cy.get('#origins-url-patterns')
    .type(searchText)
    .get('.swh-search-icon')
    .click();
}

function searchShouldRedirect(searchText, redirectUrl) {
  doSearch(searchText);
  cy.location('pathname')
    .should('equal', redirectUrl);
}

function searchShouldShowNotFound(searchText, msg) {
  doSearch(searchText);
  cy.get('#swh-no-result')
    .should('be.visible')
    .and('contain', msg);
}

describe('Test origin-search', function() {
  before(function() {
    origin = this.origin[0];
    url = this.Urls.browse_search();
  });

  beforeEach(function() {
    cy.visit(url);
  });

  it('should show in result when url is searched', function() {
    cy.get('#origins-url-patterns')
      .type(origin.url);
    cy.get('.swh-search-icon')
      .click();

    cy.get('#origin-search-results')
      .should('be.visible');
    cy.contains('tr', origin.url)
      .should('be.visible')
      .find('.swh-visit-status')
      .find('i')
      .should('have.class', 'fa-check')
      .and('have.attr', 'title',
           'Origin has at least one full visit by Software Heritage');
  });

  it('should show not found message when no repo matches', function() {
    searchShouldShowNotFound(nonExistentText,
                             'No origins matching the search criteria were found.');
  });

  it('should add appropriate URL parameters', function() {
    // Check all three checkboxes and check if
    // correct url params are added
    cy.get('#swh-search-origins-with-visit')
      .check()
      .get('#swh-filter-empty-visits')
      .check()
      .get('#swh-search-origin-metadata')
      .check()
      .then(() => {
        const searchText = origin.url;
        doSearch(searchText);
        cy.location('search').then(locationSearch => {
          const urlParams = new URLSearchParams(locationSearch);
          const query = urlParams.get('q');
          const withVisit = urlParams.has('with_visit');
          const withContent = urlParams.has('with_content');
          const searchMetadata = urlParams.has('search_metadata');

          assert.strictEqual(query, searchText);
          assert.strictEqual(withVisit, true);
          assert.strictEqual(withContent, true);
          assert.strictEqual(searchMetadata, true);
        });
      });
  });

  context('Test valid persistent ids', function() {
    it('should resolve directory', function() {
      const redirectUrl = this.Urls.browse_directory(origin.content[0].directory);
      const persistentId = `swh:1:dir:${origin.content[0].directory}`;

      searchShouldRedirect(persistentId, redirectUrl);
    });

    it('should resolve revision', function() {
      const redirectUrl = this.Urls.browse_revision(origin.revisions[0]);
      const persistentId = `swh:1:rev:${origin.revisions[0]}`;

      searchShouldRedirect(persistentId, redirectUrl);
    });

    it('should resolve snapshot', function() {
      const redirectUrl = this.Urls.browse_snapshot_directory(origin.snapshot);
      const persistentId = `swh:1:snp:${origin.snapshot}`;

      searchShouldRedirect(persistentId, redirectUrl);
    });

    it('should resolve content', function() {
      const redirectUrl = this.Urls.browse_content(`sha1_git:${origin.content[0].sha1git}`);
      const persistentId = `swh:1:cnt:${origin.content[0].sha1git}`;

      searchShouldRedirect(persistentId, redirectUrl);
    });
  });

  context('Test invalid persistent ids', function() {
    it('should show not found for directory', function() {
      const persistentId = `swh:1:dir:${this.unarchivedRepo.rootDirectory}`;
      const msg = `Directory with sha1_git ${this.unarchivedRepo.rootDirectory} not found`;

      searchShouldShowNotFound(persistentId, msg);
    });

    it('should show not found for snapshot', function() {
      const persistentId = `swh:1:snp:${this.unarchivedRepo.snapshot}`;
      const msg = `Snapshot with id ${this.unarchivedRepo.snapshot} not found!`;

      searchShouldShowNotFound(persistentId, msg);
    });

    it('should show not found for revision', function() {
      const persistentId = `swh:1:rev:${this.unarchivedRepo.revision}`;
      const msg = `Revision with sha1_git ${this.unarchivedRepo.revision} not found.`;

      searchShouldShowNotFound(persistentId, msg);
    });

    it('should show not found for content', function() {
      const persistentId = `swh:1:cnt:${this.unarchivedRepo.content[0].sha1git}`;
      const msg = `Content with sha1_git checksum equals to ${this.unarchivedRepo.content[0].sha1git} not found!`;

      searchShouldShowNotFound(persistentId, msg);
    });
  });

});
