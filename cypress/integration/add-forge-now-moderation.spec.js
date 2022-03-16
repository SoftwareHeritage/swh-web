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
    cy.visit(url)
      .location('pathname')
      .should('be.equal', '/admin/login/');

    cy.adminLogin();
    cy.visit(url)
      .location('pathname')
      .should('be.equal', url);

    logout();
  });

  it('should not display moderation link in sidebar when anonymous', function() {
    cy.visit(url);
    cy.get(`.sidebar a[href="${url}"]`)
      .should('not.exist');
  });

  it('should not display moderation link when connected as unprivileged user', function() {
    cy.userLogin();
    cy.visit(url);

    cy.get(`.sidebar a[href="${url}"]`)
      .should('not.exist');

  });

  it('should display moderation link in sidebar when connected as staff member', function() {
    cy.adminLogin();
    cy.visit(url);

    cy.get(`.sidebar a[href="${url}"]`)
      .should('exist');
  });

  it('should display moderation link in sidebar when connected as privileged user', function() {
    cy.moderatorLogin();
    cy.visit(url);

    cy.get(`.sidebar a[href="${url}"]`)
      .should('exist');
  });

});
