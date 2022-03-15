/**
 * Copyright (C) 2022  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

const defaultRedirect = '/admin/login/';

let url;

function logout() {
  cy.contains('a', 'logout')
    .click();
}

describe('Test moderation Login/logout', function() {
  before(function() {
    url = this.Urls.moderation_forge_add();
  });

  it('should redirect to default page', function() {
    cy.visit(url)
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
    // mock calls to deposit list api to avoid possible errors
    // while running the test
    cy.intercept(`${this.Urls.api_1_add_forge_request_list()}**`, {
      body: {
        data: [],
        recordsTotal: 0,
        recordsFiltered: 0,
        draw: 1
      }
    });

    cy.adminLogin();
    cy.visit(this.Urls.moderation_forge_add())
      .location('pathname')
      .should('be.equal', this.Urls.moderation_forge_add());

    logout();
  });

  it('should not display moderation link in sidebar when not connected', function() {
    cy.get(`.sidebar a[href="${this.Urls.moderation_forge_add()}"]`)
      .should('not.be.visible');
  });

  it('should not display moderation link in sidebar when connected as user', function() {
    cy.userLogin();

    cy.get(`.sidebar a[href="${this.Urls.moderation_forge_add()}"]`)
      .should('not.be.visible');

    logout();
  });

  it('should display moderation link in sidebar when connected as admin', function() {
    cy.adminLogin();

    cy.get(`.sidebar a[href="${this.Urls.moderation_forge_add()}"]`)
      .should('be.visible');

    logout();
  });

  it('should display moderation link in sidebar when connected as moderator', function() {
    cy.moderatorLogin();

    cy.get(`.sidebar a[href="${this.Urls.moderation_forge_add()}"]`)
      .should('be.visible');

    logout();
  });

  it('should prevent unauthorized access after logout', function() {
    cy.visit(this.Urls.moderation_forge_add())
      .location('pathname')
      .should('be.equal', '/admin/login/');
  });
});
