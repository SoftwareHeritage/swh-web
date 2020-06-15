/**
 * Copyright (C) 2019  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

const url = '/';

describe('Test top-bar', function() {
  it('should should contain all navigation links', function() {
    cy.visit(url);
    cy.get('.swh-top-bar a')
      .should('have.length.of.at.least', 4)
      .and('be.visible')
      .and('have.attr', 'href');
  });

  it('should show donate button on lg screen', function() {
    cy.visit(url);
    cy.get('.swh-donate-link')
      .should('be.visible');
  });

  it('should hide donate button on sm screen', function() {
    cy.viewport(600, 800);
    cy.visit(url);
    cy.get('.swh-donate-link')
      .should('not.be.visible');
  });
});

describe('Test footer', function() {
  beforeEach(function() {
    cy.visit(url);
  });

  it('should be visible', function() {
    cy.get('footer')
      .should('be.visible');
  });

  it('should have correct copyright years', function() {
    const currentYear = new Date().getFullYear();
    const copyrightText = '(C) 2015–' + currentYear.toString();
    cy.get('footer')
      .should('contain', copyrightText);
  });

  it('should contain link to Web API', function() {
    cy.get('footer')
      .get(`a[href="${this.Urls.api_1_homepage()}"]`)
      .should('contain', 'Web API');
  });
});
