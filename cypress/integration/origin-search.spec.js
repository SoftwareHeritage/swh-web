/**
 * Copyright (C) 2019-2020  The Software Heritage developers
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

function stubOriginVisitLatestRequests() {
  cy.server();
  cy.route({
    method: 'GET',
    url: '**/visit/latest/**',
    response: {
      type: 'tar'
    }
  }).as('originVisitLatest');
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
      .should('have.class', 'mdi-check-bold')
      .and('have.attr', 'title',
           'Software origin has been archived by Software Heritage');

    const browseOriginUrl = `${this.Urls.browse_origin()}?origin_url=${encodeURIComponent(origin.url)}`;
    cy.get('tr a')
      .should('have.attr', 'href', browseOriginUrl);
  });

  it('should show not found message when no repo matches', function() {
    searchShouldShowNotFound(nonExistentText,
                             'No origins matching the search criteria were found.');
  });

  it('should add appropriate URL parameters', function() {
    // Check all three checkboxes and check if
    // correct url params are added
    cy.get('#swh-search-origins-with-visit')
      .check({force: true})
      .get('#swh-filter-empty-visits')
      .check({force: true})
      .get('#swh-search-origin-metadata')
      .check({force: true})
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

  it('should not send request to the resolve endpoint', function() {
    cy.server();

    cy.route({
      method: 'GET',
      url: `${this.Urls.api_1_resolve_swhid('').slice(0, -1)}**`
    }).as('resolveSWHID');

    cy.route({
      method: 'GET',
      url: `${this.Urls.api_1_origin_search(origin.url)}**`
    }).as('searchOrigin');

    cy.get('#origins-url-patterns')
      .type(origin.url);
    cy.get('.swh-search-icon')
      .click();

    cy.wait('@searchOrigin');

    cy.xhrShouldBeCalled('resolveSWHID', 0);
    cy.xhrShouldBeCalled('searchOrigin', 1);
  });

  context('Test pagination', function() {
    it('should not paginate if there are not many results', function() {
      // Setup search
      cy.get('#swh-search-origins-with-visit')
        .uncheck({force: true})
        .get('#swh-filter-empty-visits')
        .uncheck({force: true})
        .then(() => {
          const searchText = 'libtess';

          // Get first page of results
          doSearch(searchText);

          cy.get('.swh-search-result-entry')
            .should('have.length', 1);

          cy.get('.swh-search-result-entry#origin-0 td a')
            .should('have.text', 'https://github.com/memononen/libtess2');

          cy.get('#origins-prev-results-button')
            .should('have.class', 'disabled');
          cy.get('#origins-next-results-button')
            .should('have.class', 'disabled');
        });
    });

    it('should paginate forward when there are many results', function() {
      stubOriginVisitLatestRequests();
      // Setup search
      cy.get('#swh-search-origins-with-visit')
        .uncheck({force: true})
        .get('#swh-filter-empty-visits')
        .uncheck({force: true})
        .then(() => {
          const searchText = 'many.origins';

          // Get first page of results
          doSearch(searchText);
          cy.wait('@originVisitLatest');

          cy.get('.swh-search-result-entry')
            .should('have.length', 100);

          cy.get('.swh-search-result-entry#origin-0 td a')
            .should('have.text', 'https://many.origins/1');
          cy.get('.swh-search-result-entry#origin-99 td a')
            .should('have.text', 'https://many.origins/100');

          cy.get('#origins-prev-results-button')
            .should('have.class', 'disabled');
          cy.get('#origins-next-results-button')
            .should('not.have.class', 'disabled');

          // Get second page of results
          cy.get('#origins-next-results-button a')
            .click();
          cy.wait('@originVisitLatest');

          cy.get('.swh-search-result-entry')
            .should('have.length', 100);

          cy.get('.swh-search-result-entry#origin-0 td a')
            .should('have.text', 'https://many.origins/101');
          cy.get('.swh-search-result-entry#origin-99 td a')
            .should('have.text', 'https://many.origins/200');

          cy.get('#origins-prev-results-button')
            .should('not.have.class', 'disabled');
          cy.get('#origins-next-results-button')
            .should('not.have.class', 'disabled');

          // Get third (and last) page of results
          cy.get('#origins-next-results-button a')
            .click();
          cy.wait('@originVisitLatest');

          cy.get('.swh-search-result-entry')
            .should('have.length', 50);

          cy.get('.swh-search-result-entry#origin-0 td a')
            .should('have.text', 'https://many.origins/201');
          cy.get('.swh-search-result-entry#origin-49 td a')
            .should('have.text', 'https://many.origins/250');

          cy.get('#origins-prev-results-button')
            .should('not.have.class', 'disabled');
          cy.get('#origins-next-results-button')
            .should('have.class', 'disabled');
        });
    });

    it('should paginate backward from a middle page', function() {
      stubOriginVisitLatestRequests();
      // Setup search
      cy.get('#swh-search-origins-with-visit')
        .uncheck({force: true})
        .get('#swh-filter-empty-visits')
        .uncheck({force: true})
        .then(() => {
          const searchText = 'many.origins';

          // Get first page of results
          doSearch(searchText);
          cy.wait('@originVisitLatest');

          cy.get('#origins-prev-results-button')
            .should('have.class', 'disabled');
          cy.get('#origins-next-results-button')
            .should('not.have.class', 'disabled');

          // Get second page of results
          cy.get('#origins-next-results-button a')
            .click();
          cy.wait('@originVisitLatest');

          cy.get('#origins-prev-results-button')
            .should('not.have.class', 'disabled');
          cy.get('#origins-next-results-button')
            .should('not.have.class', 'disabled');

          // Get first page of results again
          cy.get('#origins-prev-results-button a')
            .click();
          cy.wait('@originVisitLatest');

          cy.get('.swh-search-result-entry')
            .should('have.length', 100);

          cy.get('.swh-search-result-entry#origin-0 td a')
            .should('have.text', 'https://many.origins/1');
          cy.get('.swh-search-result-entry#origin-99 td a')
            .should('have.text', 'https://many.origins/100');

          cy.get('#origins-prev-results-button')
            .should('have.class', 'disabled');
          cy.get('#origins-next-results-button')
            .should('not.have.class', 'disabled');
        });
    });

    it('should paginate backward from the last page', function() {
      stubOriginVisitLatestRequests();
      // Setup search
      cy.get('#swh-search-origins-with-visit')
        .uncheck({force: true})
        .get('#swh-filter-empty-visits')
        .uncheck({force: true})
        .then(() => {
          const searchText = 'many.origins';

          // Get first page of results
          doSearch(searchText);
          cy.wait('@originVisitLatest');

          cy.get('#origins-prev-results-button')
            .should('have.class', 'disabled');
          cy.get('#origins-next-results-button')
            .should('not.have.class', 'disabled');

          // Get second page of results
          cy.get('#origins-next-results-button a')
            .click();
          cy.wait('@originVisitLatest');

          cy.get('#origins-prev-results-button')
            .should('not.have.class', 'disabled');
          cy.get('#origins-next-results-button')
            .should('not.have.class', 'disabled');

          // Get third (and last) page of results
          cy.get('#origins-next-results-button a')
            .click();

          cy.get('#origins-prev-results-button')
            .should('not.have.class', 'disabled');
          cy.get('#origins-next-results-button')
            .should('have.class', 'disabled');

          // Get second page of results again
          cy.get('#origins-prev-results-button a')
            .click();
          cy.wait('@originVisitLatest');

          cy.get('.swh-search-result-entry')
            .should('have.length', 100);

          cy.get('.swh-search-result-entry#origin-0 td a')
            .should('have.text', 'https://many.origins/101');
          cy.get('.swh-search-result-entry#origin-99 td a')
            .should('have.text', 'https://many.origins/200');

          cy.get('#origins-prev-results-button')
            .should('not.have.class', 'disabled');
          cy.get('#origins-next-results-button')
            .should('not.have.class', 'disabled');

          // Get first page of results again
          cy.get('#origins-prev-results-button a')
            .click();
          cy.wait('@originVisitLatest');

          cy.get('.swh-search-result-entry')
            .should('have.length', 100);

          cy.get('.swh-search-result-entry#origin-0 td a')
            .should('have.text', 'https://many.origins/1');
          cy.get('.swh-search-result-entry#origin-99 td a')
            .should('have.text', 'https://many.origins/100');

          cy.get('#origins-prev-results-button')
            .should('have.class', 'disabled');
          cy.get('#origins-next-results-button')
            .should('not.have.class', 'disabled');
        });
    });
  });

  context('Test valid SWHIDs', function() {
    it('should resolve directory', function() {
      const redirectUrl = this.Urls.browse_directory(origin.content[0].directory);
      const swhid = `swh:1:dir:${origin.content[0].directory}`;

      searchShouldRedirect(swhid, redirectUrl);
    });

    it('should resolve revision', function() {
      const redirectUrl = this.Urls.browse_revision(origin.revisions[0]);
      const swhid = `swh:1:rev:${origin.revisions[0]}`;

      searchShouldRedirect(swhid, redirectUrl);
    });

    it('should resolve snapshot', function() {
      const redirectUrl = this.Urls.browse_snapshot_directory(origin.snapshot);
      const swhid = `swh:1:snp:${origin.snapshot}`;

      searchShouldRedirect(swhid, redirectUrl);
    });

    it('should resolve content', function() {
      const redirectUrl = this.Urls.browse_content(`sha1_git:${origin.content[0].sha1git}`);
      const swhid = `swh:1:cnt:${origin.content[0].sha1git}`;

      searchShouldRedirect(swhid, redirectUrl);
    });

    it('should not send request to the search endpoint', function() {
      cy.server();
      const swhid = `swh:1:rev:${origin.revisions[0]}`;

      cy.route({
        method: 'GET',
        url: this.Urls.api_1_resolve_swhid(swhid)
      }).as('resolveSWHID');

      cy.route({
        method: 'GET',
        url: `${this.Urls.api_1_origin_search('').slice(0, -1)}**`
      }).as('searchOrigin');

      cy.get('#origins-url-patterns')
        .type(swhid);
      cy.get('.swh-search-icon')
        .click();

      cy.wait('@resolveSWHID');

      cy.xhrShouldBeCalled('resolveSWHID', 1);
      cy.xhrShouldBeCalled('searchOrigin', 0);
    });
  });

  context('Test invalid SWHIDs', function() {
    it('should show not found for directory', function() {
      const swhid = `swh:1:dir:${this.unarchivedRepo.rootDirectory}`;
      const msg = `Directory with sha1_git ${this.unarchivedRepo.rootDirectory} not found`;

      searchShouldShowNotFound(swhid, msg);
    });

    it('should show not found for snapshot', function() {
      const swhid = `swh:1:snp:${this.unarchivedRepo.snapshot}`;
      const msg = `Snapshot with id ${this.unarchivedRepo.snapshot} not found!`;

      searchShouldShowNotFound(swhid, msg);
    });

    it('should show not found for revision', function() {
      const swhid = `swh:1:rev:${this.unarchivedRepo.revision}`;
      const msg = `Revision with sha1_git ${this.unarchivedRepo.revision} not found.`;

      searchShouldShowNotFound(swhid, msg);
    });

    it('should show not found for content', function() {
      const swhid = `swh:1:cnt:${this.unarchivedRepo.content[0].sha1git}`;
      const msg = `Content with sha1_git checksum equals to ${this.unarchivedRepo.content[0].sha1git} not found!`;

      searchShouldShowNotFound(swhid, msg);
    });
  });

});
