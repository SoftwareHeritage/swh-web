/**
 * Copyright (C) 2019-2026  The Software Heritage developers
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

    cy.visit(url)
      .get('.swh-counter:visible')
      .then((counters) => {
        for (const counter of counters) {
          const innerText = $(counter).text();
          const value = parseInt(innerText.replace(/,/g, ''));
          assert.isAbove(value, 0);
        }
      });
  });

  it('should redirect to search page when submitting search form', function() {
    cy.visit(url);
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

  it('should have anchors to headings', function() {
    cy.visit(url);
    cy.get('.swh-heading-anchor').should('exist');
  });

});
