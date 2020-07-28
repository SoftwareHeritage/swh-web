/**
 * Copyright (C) 2020  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

describe('Test origin browse', function() {
  beforeEach(function() {
    const url = `${this.Urls.browse_origin()}?origin_url=${this.origin[1].url}`;
    cy.visit(url);
  });

  it('should have code tab active by default', function() {
    cy.get('#swh-browse-code-nav-link')
      .should('have.class', 'active');
  });

  it('should load branches view when clicking on the Branches tab', function() {
    cy.get('#swh-browse-snapshot-branches-nav-link')
      .click();

    cy.location('pathname')
      .should('eq', this.Urls.browse_origin_branches());

    cy.location('search')
      .should('eq', `?origin_url=${this.origin[1].url}`);

    cy.get('#swh-browse-snapshot-branches-nav-link')
      .should('have.class', 'active');
  });

  it('should load releases view when clicking on the Releases tab', function() {
    cy.get('#swh-browse-snapshot-releases-nav-link')
      .click();

    cy.location('pathname')
      .should('eq', this.Urls.browse_origin_releases());

    cy.location('search')
      .should('eq', `?origin_url=${this.origin[1].url}`);

    cy.get('#swh-browse-snapshot-releases-nav-link')
      .should('have.class', 'active');
  });

  it('should load visits view when clicking on the Visits tab', function() {
    cy.get('#swh-browse-origin-visits-nav-link')
      .click();

    cy.location('pathname')
      .should('eq', this.Urls.browse_origin_visits());

    cy.location('search')
      .should('eq', `?origin_url=${this.origin[1].url}`);

    cy.get('#swh-browse-origin-visits-nav-link')
      .should('have.class', 'active');
  });

  it('should load code view when clicking on the Code tab', function() {
    cy.get('#swh-browse-origin-visits-nav-link')
      .click();

    cy.get('#swh-browse-code-nav-link')
      .click();

    cy.location('pathname')
      .should('eq', this.Urls.browse_origin_directory());

    cy.location('search')
      .should('eq', `?origin_url=${this.origin[1].url}`);

    cy.get('#swh-browse-code-nav-link')
      .should('have.class', 'active');

  });

  it('should have Releases tab link disabled when there is no releases', function() {
    const url = `${this.Urls.browse_origin()}?origin_url=${this.origin[0].url}`;
    cy.visit(url);

    cy.get('#swh-browse-snapshot-releases-nav-link')
      .should('have.class', 'disabled');
  });

});
