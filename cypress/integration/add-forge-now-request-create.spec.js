/**
 * Copyright (C) 2022  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

function populateForm(type, url, contact, email, consent, comment) {
  cy.get('#swh-input-forge-type').select(type);
  cy.get('#swh-input-forge-url').type(url);
  cy.get('#swh-input-forge-contact-name').type(contact);
  cy.get('#swh-input-forge-contact-email').type(email);
  cy.get('#swh-input-forge-comment').type(comment);
}

describe('Test add-forge-request creation', function() {
  beforeEach(function() {
    this.addForgeNowUrl = this.Urls.forge_add();
  });

  it('should show both tabs for every user', function() {
    cy.visit(this.addForgeNowUrl);

    cy.get('#swh-add-forge-tab')
      .should('have.class', 'nav-link');

    cy.get('#swh-add-forge-requests-list-tab')
      .should('have.class', 'nav-link');
  });

  it('should show create forge tab by default', function() {
    cy.visit(this.addForgeNowUrl);

    cy.get('#swh-add-forge-tab')
      .should('have.class', 'active');

    cy.get('#swh-add-forge-requests-list-tab')
      .should('not.have.class', 'active');
  });

  it('should show login link for anonymous user', function() {
    cy.visit(this.addForgeNowUrl);

    cy.get('#loginLink')
      .should('be.visible')
      .should('contain', 'log in');
  });

  it('should bring back after login', function() {
    cy.visit(this.addForgeNowUrl);

    cy.get('#loginLink')
      .should('have.attr', 'href')
      .and('include', `${this.Urls.login()}?next=${this.Urls.forge_add()}`);
  });

  it('should change tabs on click', function() {
    cy.visit(this.addForgeNowUrl);

    cy.get('#swh-add-forge-requests-list-tab').click();
    cy.get('#swh-add-forge-tab')
      .should('not.have.class', 'active');

    cy.get('#swh-add-forge-requests-list-tab')
      .should('have.class', 'active');

    cy.get('#swh-add-forge-tab').click();
    cy.get('#swh-add-forge-tab')
      .should('have.class', 'active');

    cy.get('#swh-add-forge-requests-list-tab')
      .should('not.have.class', 'active');
  });

  it('should show create form elements to authenticated user', function() {
    cy.userLogin();
    cy.visit(this.addForgeNowUrl);

    cy.get('#swh-input-forge-type')
      .should('be.visible');

    cy.get('#swh-input-forge-url')
      .should('be.visible');

    cy.get('#swh-input-forge-contact-name')
      .should('be.visible');

    cy.get('#swh-input-consent-check')
      .should('be.visible');

    cy.get('#swh-input-forge-comment')
      .should('be.visible');

    cy.get('#swh-input-form-submit')
      .should('be.visible');
  });

  it('should show browse requests table for every user', function() {
    // testing only for anonymous
    cy.visit(this.addForgeNowUrl);

    cy.get('#swh-add-forge-requests-list-tab').click();
    cy.get('#add-forge-request-browse')
      .should('be.visible');

    cy.get('#loginLink')
      .should('not.be.visible');
  });

  it('should update browse list on successful submission', function() {
    cy.userLogin();
    cy.visit(this.addForgeNowUrl);
    populateForm('bitbucket', 'gitlab.com', 'test', 'test@example.com', 'on', 'test comment');
    cy.get('#requestCreateForm').submit();

    cy.visit(this.addForgeNowUrl);
    cy.get('#swh-add-forge-requests-list-tab').click();
    cy.get('#add-forge-request-browse')
      .should('be.visible')
      .should('contain', 'gitlab.com');

    cy.get('#add-forge-request-browse')
      .should('be.visible')
      .should('contain', 'PENDING');
  });

  it('should show error message on conflict', function() {
    cy.userLogin();
    cy.visit(this.addForgeNowUrl);
    populateForm('bitbucket', 'gitlab.com', 'test', 'test@example.com', 'on', 'test comment');
    cy.get('#requestCreateForm').submit();

    cy.get('#requestCreateForm').submit(); // Submitting the same data again

    cy.get('#userMessage')
      .should('have.class', 'badge-danger')
      .should('contain', 'Sorry; an error occurred');
  });
});
