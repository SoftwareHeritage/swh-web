/**
 * Copyright (C) 2019  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

const unarchivedRepo = {
  url: 'https://github.com/SoftwareHeritage/swh-web',
  revision: '7bf1b2f489f16253527807baead7957ca9e8adde',
  snapshot: 'd9829223095de4bb529790de8ba4e4813e38672d',
  rootDirectory: '7d887d96c0047a77e2e8c4ee9bb1528463677663',
  readmeSha1git: 'b203ec39300e5b7e97b6e20986183cbd0b797859'
};

const archivedRepo = {
  url: 'https://github.com/memononen/libtess2',
  readme: {
    path: 'README.md'
  }
};

const nonExistentText = 'NoMatchExists';

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
    url = this.Urls.browse_search();

    cy.visit(this.Urls.browse_origin_content(archivedRepo.url, archivedRepo.readme.path));
    cy.window().then(win => {
      const metadata = win.swh.webapp.getBrowsedSwhObjectMetadata();

      archivedRepo.revision = metadata.revision;
      archivedRepo.snapshot = metadata.snapshot;
      archivedRepo.readme.directory = metadata.directory;
      archivedRepo.readme.sha1git = metadata.sha1_git;
    });
  });

  beforeEach(function() {
    cy.visit(url);
  });

  it('should show in result for any url substring', function() {
    // Randomly select substring of origin url
    const startIndex = Math.floor(Math.random() * archivedRepo.url.length);
    const length = Math.floor(Math.random() * (archivedRepo.url.length - startIndex - 1)) + 1;
    const originSubstring = archivedRepo.url.substr(startIndex, length);

    cy.get('#origins-url-patterns')
      .type(originSubstring);
    cy.get('.swh-search-icon')
      .click();

    cy.get('#origin-search-results')
      .should('be.visible');
    cy.contains('tr', archivedRepo.url)
      .should('be.visible')
      .children('#visit-status-origin-2')
      .children('i')
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
      const redirectUrl = this.Urls.browse_directory(archivedRepo.readme.directory);
      const persistentId = `swh:1:dir:${archivedRepo.readme.directory}`;

      searchShouldRedirect(persistentId, redirectUrl);
    });

    it('should resolve revision', function() {
      const redirectUrl = this.Urls.browse_revision(archivedRepo.revision);
      const persistentId = `swh:1:rev:${archivedRepo.revision}`;

      searchShouldRedirect(persistentId, redirectUrl);
    });

    it('should resolve snapshot', function() {
      const redirectUrl = this.Urls.browse_snapshot_directory(archivedRepo.snapshot);
      const persistentId = `swh:1:snp:${archivedRepo.snapshot}`;

      searchShouldRedirect(persistentId, redirectUrl);
    });

    it('should resolve content', function() {
      const redirectUrl = this.Urls.browse_content(`sha1_git:${archivedRepo.readme.sha1git}`);
      const persistentId = `swh:1:cnt:${archivedRepo.readme.sha1git}`;

      searchShouldRedirect(persistentId, redirectUrl);
    });
  });

  context('Test invalid persistent ids', function() {
    it('should show not found for directory', function() {
      const persistentId = `swh:1:dir:${unarchivedRepo.rootDirectory}`;
      const msg = `Directory with sha1_git ${unarchivedRepo.rootDirectory} not found`;

      searchShouldShowNotFound(persistentId, msg);
    });

    it('should show not found for snapshot', function() {
      const persistentId = `swh:1:snp:${unarchivedRepo.snapshot}`;
      const msg = `Snapshot with id ${unarchivedRepo.snapshot} not found!`;

      searchShouldShowNotFound(persistentId, msg);
    });

    it('should show not found for revision', function() {
      const persistentId = `swh:1:rev:${unarchivedRepo.revision}`;
      const msg = `Revision with sha1_git ${unarchivedRepo.revision} not found.`;

      searchShouldShowNotFound(persistentId, msg);
    });

    it('should show not found for content', function() {
      const persistentId = `swh:1:cnt:${unarchivedRepo.readmeSha1git}`;
      const msg = `Content with sha1_git checksum equals to ${unarchivedRepo.readmeSha1git} not found!`;

      searchShouldShowNotFound(persistentId, msg);
    });
  });

});
