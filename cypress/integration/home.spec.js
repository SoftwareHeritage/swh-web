/**
 * Copyright (C) 2019-2021  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

const $ = Cypress.$;

const url = '/';

describe('Home Page Tests', function() {

  it('should have focus on search form after page load', function() {
    cy.visit(url);

    cy.get('#swh-origins-url-patterns')
      .should('have.attr', 'autofocus');
    // for some reason, autofocus is not honored when running cypress tests
    // while it is in non controlled browsers
    // .should('have.focus');
  });

  it('should display positive stats for each category', function() {

    cy.intercept(this.Urls.stat_counters())
      .as('getStatCounters');

    cy.visit(url)
      .wait('@getStatCounters')
      .wait(500)
      .get('.swh-counter:visible')
      .then((counters) => {
        for (let counter of counters) {
          let innerText = $(counter).text();
          const value = parseInt(innerText.replace(/,/g, ''));
          assert.isAbove(value, 0);
        }
      });
  });

  it('should display null counters and hide history graphs when storage is empty', function() {

    cy.intercept(this.Urls.stat_counters(), {
      body: {
        'stat_counters': {},
        'stat_counters_history': {}
      }
    }).as('getStatCounters');

    cy.visit(url)
      .wait('@getStatCounters')
      .wait(500)
      .get('.swh-counter:visible')
      .then((counters) => {
        for (let counter of counters) {
          const value = parseInt($(counter).text());
          assert.equal(value, 0);
        }
      });

    cy.get('.swh-counter-history')
      .should('not.be.visible');
  });

  it('should hide counters when data is missing', function() {

    cy.intercept(this.Urls.stat_counters(), {
      body: {
        'stat_counters': {
          'content': 150,
          'directory': 45,
          'revision': 78
        },
        'stat_counters_history': {}
      }
    }).as('getStatCounters');

    cy.visit(url)
      .wait('@getStatCounters')
      .wait(500);

    cy.get('#swh-content-count, #swh-directory-count, #swh-revision-count')
      .should('be.visible');

    cy.get('#swh-release-count, #swh-person-count, #swh-origin-count')
      .should('not.be.visible');

    cy.get('.swh-counter-history')
      .should('not.be.visible');
  });

  it('should redirect to search page when submitting search form', function() {
    const searchText = 'git';
    cy.get('#swh-origins-url-patterns')
      .type(searchText)
      .get('.swh-search-icon')
      .click();

    cy.location('pathname')
      .should('equal', this.Urls.browse_search());

    cy.location('search')
      .should('equal', `?q=${searchText}&with_visit=true&with_content=true`);

  });

});
