/**
 * Copyright (C) 2019  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

const nonExistentText = 'NoMatchExists';

let origin;
let url;

function searchShouldRedirect(searchText, redirectUrl) {
  cy.get('#origins-url-patterns')
    .type(searchText);
  cy.get('.swh-search-icon')
    .click();
  cy.location('pathname')
    .should('equal', redirectUrl);
}

function searchShouldShowNotFound(searchText, msg) {
  cy.get('#origins-url-patterns')
    .type(searchText);
  cy.get('.swh-search-icon')
    .click();
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

  it('should show in result for any url substring', function() {
    // Randomly select substring of origin url
    const startIndex = Math.floor(Math.random() * origin.url.length);
    const length = Math.floor(Math.random() * (origin.url.length - startIndex - 1)) + 1;
    const originSubstring = origin.url.substr(startIndex, length);

    cy.get('#origins-url-patterns')
      .type(originSubstring);
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

  context('Test valid persistent ids', function() {
    it('should resolve directory', function() {
      const redirectUrl = this.Urls.browse_directory(origin.content[0].directory);
      const persistentId = `swh:1:dir:${origin.content[0].directory}`;

      searchShouldRedirect(persistentId, redirectUrl);
    });

    it('should resolve revision', function() {
      const redirectUrl = this.Urls.browse_revision(origin.revision);
      const persistentId = `swh:1:rev:${origin.revision}`;

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
