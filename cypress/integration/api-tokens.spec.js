/**
 * Copyright (C) 2020  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

describe('Test API tokens UI', function() {

  it('should ask for user to login', function() {
    cy.visit(`${this.Urls.oidc_profile()}#tokens`, {failOnStatusCode: false});
    cy.location().should(loc => {
      expect(loc.pathname).to.eq(this.Urls.oidc_login());
    });
  });

  function initTokensPage(Urls, tokens) {
    cy.server();
    cy.route({
      method: 'GET',
      url: `${Urls.oidc_list_bearer_tokens()}/**`,
      response: {
        'recordsTotal': tokens.length,
        'draw': 2,
        'recordsFiltered': tokens.length,
        'data': tokens
      }
    });
    // the tested UI should not be accessible for standard Django users
    // but we need a user logged in for testing it
    cy.adminLogin();
    cy.visit(`${Urls.oidc_profile()}#tokens`);
  }

  it('should initiate token generation flow', function() {
    initTokensPage(this.Urls, []);

    cy.contains('Generate new token')
      .click();

    cy.get('.modal-dialog')
      .should('be.visible');

    cy.get('.modal-header')
      .should('contain', 'Bearer token generation');

    cy.get('#swh-token-form-submit')
      .click();

    cy.location().should(loc => {
      expect(loc.pathname).to.eq(this.Urls.oidc_generate_bearer_token());
    });
  });

  it('should report error when not logged in and visiting a token generation URL', function() {
    cy.visit(this.Urls.oidc_generate_bearer_token_complete(), {failOnStatusCode: false});
    cy.get('.swh-http-error')
      .should('be.visible');
    cy.get('.swh-http-error-code')
      .should('contain', 403);
    cy.get('.swh-http-error-desc')
      .should('contain', 'You are not allowed to generate bearer tokens');
  });

  function displayToken(Urls, status, tokenValue = '') {
    cy.route({
      method: 'POST',
      url: `${Urls.oidc_get_bearer_token()}/**`,
      response: tokenValue,
      status: status
    }).as('getTokenRequest');

    cy.contains('Display token')
      .click({force: true});

    cy.get('.modal-dialog')
      .should('be.visible');

    cy.get('.modal-header')
      .should('contain', 'Display bearer token');
  }

  it('should show a token when requested', function() {
    initTokensPage(this.Urls, [{id: 1, creation_date: new Date().toISOString()}]);
    const tokenValue = 'token-value';
    displayToken(this.Urls, 200, tokenValue);
    cy.get('#swh-bearer-token')
      .should('contain', tokenValue);
  });

  it('should report errors when token display failed', function() {
    initTokensPage(this.Urls, [{id: 1, creation_date: new Date().toISOString()}]);
    displayToken(this.Urls, 500);
    cy.get('.modal-body')
      .should('contain', 'Internal server error');
  });

  function revokeToken(Urls, status) {
    cy.route({
      method: 'POST',
      url: `${Urls.oidc_revoke_bearer_tokens()}/**`,
      response: '',
      status: status
    }).as('revokeTokenRequest');

    cy.contains('Revoke token')
      .click({force: true});

    cy.get('.modal-dialog')
      .should('be.visible');

    cy.get('.modal-header')
      .should('contain', 'Revoke bearer token');

    cy.get('#swh-token-form-submit')
      .click({force: true});

    cy.wait('@revokeTokenRequest');

    if (status === 200) {
      cy.get('#swh-token-form-submit')
        .should('be.disabled');
    }
  }

  it('should revoke a token when requested', function() {
    initTokensPage(this.Urls, [{id: 1, creation_date: new Date().toISOString()}]);
    revokeToken(this.Urls, 200);
    cy.get('#swh-token-form-message')
      .should('contain', 'Bearer token successfully revoked');
  });

  it('should report errors when token revoke failed', function() {
    initTokensPage(this.Urls, [{id: 1, creation_date: new Date().toISOString()}]);
    revokeToken(this.Urls, 500);
    cy.get('#swh-token-error-message')
      .should('contain', 'Internal server error');
  });

});
