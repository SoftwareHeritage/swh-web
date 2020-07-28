/**
 * Copyright (C) 2019  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

const url = '/browse/help/';

describe('Test top-bar', function() {
  beforeEach(function() {
    cy.clearLocalStorage();
    cy.visit(url);
  });
  it('should should contain all navigation links', function() {
    cy.get('.swh-top-bar a')
      .should('have.length.of.at.least', 4)
      .and('be.visible')
      .and('have.attr', 'href');
  });

  it('should show donate button on lg screen', function() {
    cy.get('.swh-donate-link')
      .should('be.visible');
  });
  it('should hide donate button on sm screen', function() {
    cy.viewport(600, 800);
    cy.get('.swh-donate-link')
      .should('not.be.visible');
  });
  it('should hide full width switch on small screens', function() {
    cy.viewport(360, 740);
    cy.get('#swh-full-width-switch-container')
      .should('not.be.visible');

    cy.viewport(600, 800);
    cy.get('#swh-full-width-switch-container')
      .should('not.be.visible');

    cy.viewport(800, 600);
    cy.get('#swh-full-width-switch-container')
      .should('not.be.visible');
  });
  it('should show full width switch on large screens', function() {
    cy.viewport(1024, 768);
    cy.get('#swh-full-width-switch-container')
      .should('be.visible');

    cy.viewport(1920, 1080);
    cy.get('#swh-full-width-switch-container')
      .should('be.visible');
  });
  it('should change container width when toggling Full width switch', function() {
    cy.get('#swh-web-content')
      .should('have.class', 'container')
      .should('not.have.class', 'container-fluid');

    cy.should(() => {
      expect(JSON.parse(localStorage.getItem('swh-web-full-width'))).to.be.null;
    });

    cy.get('#swh-full-width-switch')
      .click({force: true});

    cy.get('#swh-web-content')
      .should('not.have.class', 'container')
      .should('have.class', 'container-fluid');

    cy.should(() => {
      expect(JSON.parse(localStorage.getItem('swh-web-full-width'))).to.be.true;
    });

    cy.get('#swh-full-width-switch')
      .click({force: true});

    cy.get('#swh-web-content')
      .should('have.class', 'container')
      .should('not.have.class', 'container-fluid');

    cy.should(() => {
      expect(JSON.parse(localStorage.getItem('swh-web-full-width'))).to.be.false;
    });
  });
  it('should restore container width when loading page again', function() {
    cy.visit(url)
      .get('#swh-web-content')
      .should('have.class', 'container')
      .should('not.have.class', 'container-fluid');

    cy.get('#swh-full-width-switch')
      .click({force: true});

    cy.visit(url)
      .get('#swh-web-content')
      .should('not.have.class', 'container')
      .should('have.class', 'container-fluid');

    cy.get('#swh-full-width-switch')
      .click({force: true});

    cy.visit(url)
      .get('#swh-web-content')
      .should('have.class', 'container')
      .should('not.have.class', 'container-fluid');
  });
});

describe('Test navbar', function() {
  it('should redirect to search page when submitting search form in navbar', function() {
    const keyword = 'python';
    cy.get('#swh-origins-search-top-input')
      .type(keyword);

    cy.get('.swh-search-navbar')
      .submit();

    cy.url()
      .should('include', `${this.Urls.browse_search()}?q=${keyword}`);
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
