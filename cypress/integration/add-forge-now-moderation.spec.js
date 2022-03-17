/**
 * Copyright (C) 2022  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

const defaultRedirect = '/admin/login/';

let moderationAddForgeUrl;
let listAddForgeRequestsUrl;

function logout() {
  cy.contains('a', 'logout')
    .click();
}

describe('Test moderation Login/logout', function() {
  before(function() {
    moderationAddForgeUrl = this.Urls.moderation_forge_add();
    listAddForgeRequestsUrl = this.Urls.add_forge_request_list_datatables();
  });

  it('should redirect to default page', function() {
    cy.visit(moderationAddForgeUrl)
      .get('input[name="username"]')
      .type('admin')
      .get('input[name="password"]')
      .type('admin')
      .get('.container form')
      .submit();

    cy.location('pathname')
      .should('be.equal', moderationAddForgeUrl);
  });

  it('should redirect to correct page after login', function() {
    cy.visit(moderationAddForgeUrl)
      .location('pathname')
      .should('be.equal', defaultRedirect);

    cy.adminLogin();
    cy.visit(moderationAddForgeUrl)
      .location('pathname')
      .should('be.equal', moderationAddForgeUrl);

    logout();
  });

  it('should not display moderation link in sidebar when anonymous', function() {
    cy.visit(moderationAddForgeUrl);
    cy.get(`.sidebar a[href="${moderationAddForgeUrl}"]`)
      .should('not.exist');
  });

  it('should not display moderation link when connected as unprivileged user', function() {
    cy.userLogin();
    cy.visit(moderationAddForgeUrl);

    cy.get(`.sidebar a[href="${moderationAddForgeUrl}"]`)
      .should('not.exist');

  });

  it('should display moderation link in sidebar when connected as staff member', function() {
    cy.adminLogin();
    cy.visit(moderationAddForgeUrl);

    cy.get(`.sidebar a[href="${moderationAddForgeUrl}"]`)
      .should('exist');
  });

  it('should display moderation link in sidebar when connected as privileged user', function() {
    cy.moderatorLogin();
    cy.visit(moderationAddForgeUrl);

    cy.get(`.sidebar a[href="${moderationAddForgeUrl}"]`)
      .should('exist');
  });

  it('should list add-forge-now requests', function() {
    cy.intercept(`${listAddForgeRequestsUrl}**`, {fixture: 'add-forge-now-requests'}).as('listRequests');
    cy.moderatorLogin();
    cy.visit(moderationAddForgeUrl);

    cy.wait('@listRequests');
    cy.get('tbody tr').then(rows => {
      expect(rows).to.have.length(6);
    });

  });

});
