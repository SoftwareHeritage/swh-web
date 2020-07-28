/**
 * Copyright (C) 2019  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

const $ = Cypress.$;

const defaultRedirect = '/admin/origin/save/';

let url;

function logout() {
  cy.contains('a', 'logout')
    .click();
}

describe('Test Admin Login/logout', function() {
  before(function() {
    url = this.Urls.admin();
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

    logout();
  });

  it('should display admin-origin-save and deposit in sidebar', function() {
    cy.adminLogin();
    cy.visit(url);

    cy.get(`.sidebar a[href="${this.Urls.admin_origin_save()}"]`)
      .should('be.visible');

    cy.get(`.sidebar a[href="${this.Urls.admin_deposit()}"]`)
      .should('be.visible');

    logout();
  });

  it('should display username on top-right', function() {
    cy.adminLogin();
    cy.visit(url);

    cy.get('.swh-position-right')
      .should('contain', 'admin');

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
    // mock calls to deposit list api to avoid possible errors
    // while running the test
    cy.server();
    cy.route({
      method: 'GET',
      url: `${this.Urls.admin_deposit_list()}**`,
      response: {
        data: [],
        recordsTotal: 0,
        recordsFiltered: 0,
        draw: 1
      }
    });

    cy.visit(this.Urls.admin_deposit())
      .location('search')
      .should('contain', `next=${this.Urls.admin_deposit()}`);

    cy.adminLogin();
    cy.visit(this.Urls.admin_deposit());

    cy.location('pathname')
      .should('be.equal', this.Urls.admin_deposit());

    logout();
  });
});

const existingRowToSelect = 'https://bitbucket.org/';

const originUrlListTestData = [
  {
    listType: 'authorized',
    originToAdd: 'git://git.archlinux.org/',
    originToRemove: 'https://github.com/'
  },
  {
    listType: 'unauthorized',
    originToAdd: 'https://random.org',
    originToRemove: 'https://gitlab.com'
  }
];

const capitalize = s => s.charAt(0).toUpperCase() + s.slice(1);

describe('Test Admin Origin Save Urls Filtering', function() {

  beforeEach(function() {
    cy.adminLogin();
    cy.visit(this.Urls.admin_origin_save());

    cy.contains('a', 'Origin urls filtering')
      .click()
      .wait(500);
  });

  it(`should select or unselect a table row by clicking on it`, function() {
    cy.contains(`#swh-authorized-origin-urls tr`, existingRowToSelect)
      .click()
      .should('have.class', 'selected')
      .click()
      .should('not.have.class', 'selected');
  });

  originUrlListTestData.forEach(testData => {

    it(`should add a new origin url prefix in the ${testData.listType} list`, function() {

      const tabName = capitalize(testData.listType) + ' urls';

      cy.contains('a', tabName)
        .click()
        .wait(500);

      cy.get(`#swh-${testData.listType}-origin-urls tr`).each(elt => {
        if ($(elt).text() === testData.originToAdd) {
          cy.get(elt).click();
          cy.get(`#swh-remove-${testData.listType}-origin-url`).click();
        }
      });

      cy.get(`#swh-${testData.listType}-url-prefix`)
        .type(testData.originToAdd);

      cy.get(`#swh-add-${testData.listType}-origin-url`)
        .click();

      cy.contains(`#swh-${testData.listType}-origin-urls tr`, testData.originToAdd)
        .should('be.visible');

      cy.contains('.alert-success', `The origin url prefix has been successfully added in the ${testData.listType} list.`)
        .should('be.visible');

      cy.get(`#swh-add-${testData.listType}-origin-url`)
        .click();

      cy.contains('.alert-warning', `The provided origin url prefix is already registered in the ${testData.listType} list.`)
        .should('be.visible');

    });

    it(`should remove an origin url prefix from the ${testData.listType} list`, function() {

      const tabName = capitalize(testData.listType) + ' urls';

      cy.contains('a', tabName)
        .click();

      let originUrlMissing = true;
      cy.get(`#swh-${testData.listType}-origin-urls tr`).each(elt => {
        if ($(elt).text() === testData.originToRemove) {
          originUrlMissing = false;
        }
      });

      if (originUrlMissing) {
        cy.get(`#swh-${testData.listType}-url-prefix`)
          .type(testData.originToRemove);

        cy.get(`#swh-add-${testData.listType}-origin-url`)
          .click();

        cy.get('.alert-dismissible button').click();
      }

      cy.contains(`#swh-${testData.listType}-origin-urls tr`, testData.originToRemove)
        .click();

      cy.get(`#swh-remove-${testData.listType}-origin-url`).click();

      cy.contains(`#swh-${testData.listType}-origin-urls tr`, testData.originToRemove)
        .should('not.exist');

    });
  });

});
