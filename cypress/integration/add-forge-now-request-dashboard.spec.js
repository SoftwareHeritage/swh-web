/**
 * Copyright (C) 2022  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

const requestId = 1;

describe('Test add forge now request dashboard load', function() {

  beforeEach(function() {
    const url = this.Urls.add_forge_now_request_dashboard(requestId);
    cy.adminLogin();
    cy.intercept(`${this.Urls.api_1_add_forge_request_get(requestId)}**`,
                 {fixture: 'add-forge-now-request'}).as('forgeAddRequest');
    cy.visit(url);
  });

  it('should load add forge request details', function() {
    cy.wait('@forgeAddRequest');
    cy.get('#requestStatus')
      .should('contain', 'PENDING');

    cy.get('#requestType')
      .should('contain', 'bitbucket');

    cy.get('#requestURL')
      .should('contain', 'test.com');

    cy.get('#requestEmail')
      .should('contain', 'test@example.com');
  });

  it('should not show any error message', function() {
    cy.get('#fetchError')
      .should('have.class', 'd-none');
    cy.get('#requestDetails')
      .should('not.have.class', 'd-none');
  });

  it('should show error message for an api error', function() {
    const invalidRequestId = 2;
    const url = this.Urls.add_forge_now_request_dashboard(invalidRequestId);
    cy.visit(url);
    cy.get('#fetchError')
      .should('not.have.class', 'd-none');
    cy.get('#requestDetails')
      .should('have.class', 'd-none');
  });

  it('should load add forge request history', function() {
    cy.get('#requestHistory')
      .children()
      .should('have.length', 1);

    cy.get('#requestHistory')
      .children()
      .should('contain', 'New status: PENDING');
  });

  it('should load possible next status', function() {
    // 3 possible next status and the comment option
    cy.get('#decisionOptions')
      .children()
      .should('have.length', 4);
  });
});
