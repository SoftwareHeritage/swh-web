/**
 * Copyright (C) 2022  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

const defaultRedirect = '/admin/login/';

let moderationForgeAddUrl;
let listAddForgeRequestsUrl;

function logout() {
  cy.contains('a', 'logout')
    .click();
}

describe('Test moderation Login/logout', function() {
  before(function() {
    moderationForgeAddUrl = this.Urls.moderation_forge_add();
    listAddForgeRequestsUrl = this.Urls.add_forge_request_list_datatables();
  });

  it('should redirect to default page', function() {
    cy.visit(moderationForgeAddUrl)
      .get('input[name="username"]')
      .type('admin')
      .get('input[name="password"]')
      .type('admin')
      .get('.container form')
      .submit();

    cy.location('pathname')
      .should('be.equal', defaultRedirect);
  });

  it('should redirect to correct page after login', function() {
    cy.visit(moderationForgeAddUrl)
      .location('pathname')
      .should('be.equal', '/admin/login/');

    cy.adminLogin();
    cy.visit(moderationForgeAddUrl)
      .location('pathname')
      .should('be.equal', moderationForgeAddUrl);

    logout();
  });

  it('should not display moderation link in sidebar when anonymous', function() {
    cy.visit(moderationForgeAddUrl);
    cy.get(`.sidebar a[href="${moderationForgeAddUrl}"]`)
      .should('not.exist');
  });

  it('should not display moderation link when connected as unprivileged user', function() {
    cy.userLogin();
    cy.visit(moderationForgeAddUrl);

    cy.get(`.sidebar a[href="${moderationForgeAddUrl}"]`)
      .should('not.exist');

  });

  it('should display moderation link in sidebar when connected as staff member', function() {
    cy.adminLogin();
    cy.visit(moderationForgeAddUrl);

    cy.get(`.sidebar a[href="${moderationForgeAddUrl}"]`)
      .should('exist');
  });

  it('should display moderation link in sidebar when connected as privileged user', function() {
    cy.moderatorLogin();
    cy.visit(moderationForgeAddUrl);

    cy.get(`.sidebar a[href="${moderationForgeAddUrl}"]`)
      .should('exist');
  });

  it('should list add-forge-now requests', function() {
    cy.intercept(`${listAddForgeRequestsUrl}**`, {fixture: 'add-forge-now-requests'}).as('listRequests');
    cy.moderatorLogin();
    cy.visit(moderationForgeAddUrl);

    cy.wait('@listRequests');
    cy.get('tbody tr').then(rows => {
      expect(rows).to.have.length(6);
    });

  });

});
