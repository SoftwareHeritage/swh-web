/**
 * Copyright (C) 2019  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

const username = 'admin';
const password = 'admin';
const defaultRedirect = '/admin/origin/save/';

let url;

function login(username, password) {
  cy.get('input[name="username"]')
    .type(username)
    .get('input[name="password"]')
    .type(password)
    .get('form')
    .submit();
}

function logout() {
  cy.contains('a', 'logout')
    .click();
}

describe('Test Admin Features', function() {
  before(function() {
    url = this.Urls.admin();
  });

  it('should redirect to default page', function() {
    cy.visit(url);
    login(username, password);

    cy.location('pathname')
      .should('be.equal', defaultRedirect);

    logout();
  });

  it('should display admin-origin-save and deposit in sidebar', function() {
    cy.visit(url);
    login(username, password);

    cy.get(`.sidebar a[href="${this.Urls.admin_origin_save()}"]`)
      .should('be.visible');

    cy.get(`.sidebar a[href="${this.Urls.admin_deposit()}"]`)
      .should('be.visible');

    logout();
  });

  it('should display username on top-right', function() {
    cy.visit(url);
    login(username, password);

    cy.get('.swh-position-right')
      .should('contain', username);

    logout();
  });

  it('should prevent unauthorized access after logout', function() {
    cy.visit(this.Urls.admin_origin_save())
      .location('pathname')
      .should('be.equal', '/admin/login/');
    cy.visit(this.Urls.admin_deposit())
      .location('pathname')
      .should('be.equal', '/admin/login/');
  });

  it('should redirect to correct page after login', function() {
    cy.visit(this.Urls.admin_deposit())
      .location('search')
      .should('contain', `next=${this.Urls.admin_deposit()}`);

    login(username, password);

    cy.location('pathname')
      .should('be.equal', this.Urls.admin_deposit());

    logout();
  });
});
