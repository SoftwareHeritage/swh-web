/**
 * Copyright (C) 2019-2025  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

const $ = Cypress.$;
const nonExistentText = 'NoMatchExists';

let origin;
let url;

function doSearch(searchText, searchInputElt = '#swh-origins-url-patterns') {
  if (searchText.startsWith('swh:')) {
    cy.intercept('**/api/1/resolve/**')
      .as('swhidResolve');
  } else {
    cy.intercept('**/visit/latest/**')
      .as('checkOriginVisits');
  }
  cy.get(searchInputElt)
    // to avoid sending too much SWHID validation requests
    // as cypress insert character one by one when using type
    .invoke('val', searchText.slice(0, -1))
    .type(searchText.slice(-1))
    .get('.swh-search-icon')
    .click({force: true});
  if (searchText.startsWith('swh:')) {
    cy.wait('@swhidResolve');
  } else if (searchText.startsWith('http')) {
    cy.wait('@checkOriginVisits');
  }
}

function searchShouldRedirect(searchText, redirectUrl) {
  doSearch(searchText);
  cy.location('pathname')
    .should('equal', redirectUrl);
}

function searchShouldShowNotFound(searchText, msg) {
  doSearch(searchText);
  if (searchText.startsWith('swh:')) {
    cy.get('.invalid-feedback')
      .should('be.visible')
      .and('contain', msg);
  }
}

function stubOriginVisitLatestRequests(status = 200, response = {type: 'tar'}, aliasSuffix = '') {
  cy.intercept({url: '**/visit/latest/**'}, {
    body: response,
    statusCode: status
  }).as(`originVisitLatest${aliasSuffix}`);
}

describe('Test origin-search', function() {
  before(function() {
    origin = this.origin[0];
    url = this.Urls.browse_search();
  });

  beforeEach(function() {
    cy.visit(url);
  });

  it('should have focus on search form after page load', function() {
    cy.get('#swh-origins-url-patterns')
      .should('have.attr', 'autofocus');
    // for some reason, autofocus is not honored when running cypress tests
    // while it is in non controlled browsers
    // .should('have.focus');
  });

  it('should redirect to browse when archived URL is searched', function() {
    cy.get('#swh-origins-url-patterns')
      .type(origin.url);
    cy.get('.swh-search-icon')
      .click();

    cy.location('pathname')
      .should('eq', this.Urls.browse_origin_directory());
    cy.location('search')
      .should('eq', `?origin_url=${origin.url}`);
  });

  it('should not redirect for non valid URL', function() {
    cy.get('#swh-origins-url-patterns')
      .type('www.example'); // Invalid URL
    cy.get('.swh-search-icon')
      .click();

    cy.location('pathname')
      .should('eq', this.Urls.browse_search()); // Stay in the current page
  });

  it('should not redirect for valid non archived URL', function() {
    cy.get('#swh-origins-url-patterns')
      .type('http://eaxmple.com/test/'); // Valid URL, but not archived
    cy.get('.swh-search-icon')
      .click();

    cy.location('pathname')
      .should('eq', this.Urls.browse_search()); // Stay in the current page
  });

  it('should not redirect for an origin without any snapshots', function() {
    cy.get('#swh-origins-url-patterns')
      // valid origin URL but with null snapshot
      .type('https://example.org/project/with/null/snapshot');
    cy.get('.swh-search-icon')
      .click();

    cy.location('pathname')
      .should('eq', this.Urls.browse_search()); // Stay in the current page
  });

  it('should remove origin URL with no archived content', function() {
    stubOriginVisitLatestRequests(404);

    // Using a non full origin URL here
    // This is because T3354 redirects to the origin in case of a valid, archived URL
    cy.get('#swh-origins-url-patterns')
      .type(origin.url.slice(0, -1));
    cy.get('.swh-search-icon')
      .click();

    cy.wait('@originVisitLatest');

    cy.get('#origin-search-results')
      .should('be.visible')
      .find('tbody tr').should('have.length', 0);
  });

  it('should filter origins by visit type', function() {
    cy.intercept('**/visit/latest/**').as('checkOriginVisits');
    cy.get('#swh-origins-url-patterns')
      .type('http');

    for (const visitType of ['git', 'tar']) {
      cy.get('#swh-search-visit-type')
        .select(visitType);

      cy.get('.swh-search-icon')
        .click();

      cy.wait('@checkOriginVisits');

      cy.get('#origin-search-results')
        .should('be.visible');

      cy.wait('@checkOriginVisits');

      cy.get('tbody tr td.swh-origin-visit-type').then(elts => {
        for (const elt of elts) {
          cy.get(elt).should('have.text', visitType);
        }
      });
    }
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
        const searchText = origin.url.slice(0, -1);
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

  it('should search in origin intrinsic metadata', function() {
    cy.intercept('GET', '**/origin/metadata-search/**').as(
      'originMetadataSearch'
    );
    cy.get('#swh-search-origins-with-visit')
      .check({force: true})
      .get('#swh-filter-empty-visits')
      .check({force: true})
      .get('#swh-search-origin-metadata')
      .check({force: true})
      .then(() => {
        const searchText = 'plugin';
        doSearch(searchText);
        cy.wait('@originMetadataSearch').then((req) => {
          expect(req.response.body).to.deep.equal(
            [
              {
                'url': 'https://github.com/wcoder/highlightjs-line-numbers.js',
                'visit_types': ['git']
              }
            ]
            // origins are defined in _TEST_ORIGINS variable in swh/web/tests/data.py
          );
        });
      });
  });

  it('should not send request to the resolve endpoint', function() {
    cy.intercept(`${this.Urls.api_1_resolve_swhid('').slice(0, -1)}**`)
      .as('resolveSWHID');

    cy.intercept(`${this.Urls.api_1_origin_search(origin.url.slice(0, -1))}**`)
      .as('searchOrigin');

    cy.get('#swh-origins-url-patterns')
      .type(origin.url.slice(0, -1));

    cy.get('.swh-search-icon')
      .click();

    cy.wait('@searchOrigin');

    cy.xhrShouldBeCalled('resolveSWHID', 0);
    cy.xhrShouldBeCalled('searchOrigin', 1);
  });

  it('should add query language support for staff users', function() {
    cy.get('#swh-search-use-ql')
      .should('not.exist');

    cy.adminLogin();
    cy.visit(url);

    cy.get('#swh-search-use-ql')
      .should('exist');
  });

  it('should show error messages when using the query language', function() {
    cy.adminLogin();
    cy.visit(url);

    cy.intercept('GET', `${this.Urls.api_1_origin_search('**')}**`,
                 {
                   body: {
                     'exception': 'BadInputExc',
                     'reason': 'Syntax error in search query: Invalid query'
                   },
                   statusCode: 400
                 })
      .as('searchOrigin');

    cy.get('#swh-search-use-ql')
      .should('exist')
      .click({force: true}); // Covered by label

    cy.get('#swh-origins-url-patterns')
      .type('this is not a valid query')
      .type('{enter}');

    cy.wait('@searchOrigin').then((xhr) => {
      cy.get('#swh-no-result')
        .should('contain', 'Syntax error in search query');
    });

  });

  function checkSearchHasResults() {
    cy.get('.swh-search-icon')
        .click();

    cy.wait('@checkOriginVisits');

    cy.get('#origin-search-results')
        .should('be.visible');

    cy.get('tbody tr td.swh-origin-visit-type')
      .should('exist');

    cy.get('#swh-origin-search-total-results')
      .invoke('text')
      .should('match', /[0-9,]+ origins found/);
  }

  it('should search all origins when no pattern is provided', function() {
    cy.intercept('**/visit/latest/**').as('checkOriginVisits');

    // with default filters
    checkSearchHasResults();

    // remove filters
    cy.get('#swh-search-origins-with-visit')
      .uncheck({force: true})
      .get('#swh-filter-empty-visits')
      .uncheck({force: true});
    checkSearchHasResults();

  });

  it('should search all origins for a visit type', function() {
    cy.intercept('**/visit/latest/**').as('checkOriginVisits');

    for (const visitType of ['git', 'tar']) {
      cy.get('#swh-search-visit-type')
        .select(visitType);

      checkSearchHasResults();

      cy.get('tbody tr td.swh-origin-visit-type').then(elts => {
        for (const elt of elts) {
          cy.get(elt).should('have.text', visitType);
        }
      });
    }
  });

  it('should display all visit types for an origin when visit type filter is disabled', function() {
    const searchPattern = 'project/multiple/visit/types';
    cy.intercept('**/visit/latest/**').as('checkOriginVisits');
    cy.get('#swh-origins-url-patterns')
      .type(searchPattern);
    cy.get('.swh-search-icon')
      .click();

    checkSearchHasResults();
    // ensure datatable update
    cy.wait(100);

    // should have two results, one by visit type
    cy.get('tbody tr').should('have.length', 2);
    cy.get('tbody tr').then(elts => {
      for (const elt of elts) {
        const visitType = $(elt.cells[0]).text();
        const originUrl = $(elt.cells[1]).text();
        const browseUrl = $(elt.cells[1].innerHTML).attr('href');
        assert.include(originUrl, searchPattern);
        assert.include(browseUrl, `&visit_type=${visitType}`);
      }
    });
  });

  it('should redirect to browse origin with selected visit type when search pattern is equal to origin URL', function() {
    const searchPattern = 'https://example.org/project/multiple/visit/types';
    for (const visitType of ['git', 'git-checkout']) {
      cy.get('#swh-origins-url-patterns')
        .type(searchPattern);
      cy.get('#swh-search-visit-type')
        .select(visitType);
      cy.get('.swh-search-icon')
        .click();
      cy.url().should('include', `/browse/origin/directory/?origin_url=${searchPattern}&visit_type=${visitType}`);
      cy.get('#swh-origin-visit-type').should('have.value', visitType);
      cy.visit(url);
    }
  });

  it('should encode ? in origin URL provided as argument in latest visit URL queried by XHR', function() {
    // origin added in tests data by Python
    const originUrl = 'https://example.org/project/download.php?version=2.0';
    cy.intercept(`**/api/1/origin/${originUrl.replace('?', '%3F')}/visit/latest/**`)
      .as('checkOriginVisit');

    doSearch(originUrl);

    cy.wait('@checkOriginVisit');

    cy.get('.swh-search-result-entry')
            .should('have.length', 1);

    cy.get('.swh-search-result-entry#origin-0 .swh-origin-visit-type')
            .should('have.text', 'tar');

    cy.get('.swh-search-result-entry#origin-0 td a')
            .should('have.text', originUrl);

    cy.get('.swh-search-result-entry#origin-0 .swh-visit-status')
      .should('have.text', 'Archived');

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
      const swhid = `swh:1:rev:${origin.revisions[0]}`;

      cy.intercept(this.Urls.api_1_resolve_swhid(swhid))
        .as('resolveSWHID');

      cy.intercept(`${this.Urls.api_1_origin_search('').slice(0, -1)}**`)
        .as('searchOrigin');

      cy.get('#swh-origins-url-patterns')
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

    function checkInvalidSWHIDReport(url, searchInputElt, swhidInput, validationMessagePattern = '') {
      cy.visit(url);
      doSearch(swhidInput, searchInputElt);
      cy.get(searchInputElt)
        .then($el => $el[0].checkValidity()).should('be.false');
      cy.get(searchInputElt)
        .invoke('prop', 'validationMessage')
        .should('not.equal', '')
        .should('contain', validationMessagePattern);
    }

    it('should report invalid SWHID in search page input', function() {
      const swhidInput =
        `swh:1:cnt:${this.unarchivedRepo.content[0].sha1git};lines=45-60/`;
      checkInvalidSWHIDReport(this.Urls.browse_search(), '#swh-origins-url-patterns', swhidInput);
      cy.get('.invalid-feedback')
        .should('be.visible');
    });

    it('should report invalid SWHID in top right search input', function() {
      const swhidInput =
        `swh:1:cnt:${this.unarchivedRepo.content[0].sha1git};lines=45-60/`;
      checkInvalidSWHIDReport(this.Urls.browse_help(), '#swh-origins-search-top-input', swhidInput);
    });

    it('should report SWHID with uppercase chars in search page input', function() {
      const swhidInput =
        `swh:1:cnt:${this.unarchivedRepo.content[0].sha1git}`.toUpperCase();
      checkInvalidSWHIDReport(this.Urls.browse_search(), '#swh-origins-url-patterns', swhidInput, swhidInput.toLowerCase());
      cy.get('.invalid-feedback')
        .should('be.visible');
    });

    it('should report SWHID with uppercase chars in top right search input', function() {
      let swhidInput =
        `swh:1:cnt:${this.unarchivedRepo.content[0].sha1git}`.toUpperCase();
      swhidInput += ';lines=45-60/';
      checkInvalidSWHIDReport(this.Urls.browse_help(), '#swh-origins-search-top-input', swhidInput.toLowerCase());
    });

  });

});
