/**
 * Copyright (C) 2019-2022  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

const $ = Cypress.$;

const defaultRedirect = '/admin/origin/save/requests/';

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

    cy.get(`.sidebar a[href="${this.Urls.admin_origin_save_requests()}"]`)
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

  it('should get info about a user logged in from javascript', function() {
    cy.window().then(win => {
      expect(win.swh.webapp.isUserLoggedIn()).to.be.false;
    });
    cy.adminLogin();
    cy.visit(url);
    cy.window().then(win => {
      expect(win.swh.webapp.isUserLoggedIn()).to.be.true;
    });
    logout();
    cy.visit(url);
    cy.window().then(win => {
      expect(win.swh.webapp.isUserLoggedIn()).to.be.false;
    });
  });

  it('should prevent unauthorized access after logout', function() {
    cy.visit(this.Urls.admin_origin_save_requests())
      .location('pathname')
      .should('be.equal', '/admin/login/');
    cy.visit(this.Urls.admin_deposit())
      .location('pathname')
      .should('be.equal', '/admin/login/');
  });

  it('should redirect to correct page after login', function() {
    // mock calls to deposit list api to avoid possible errors
    // while running the test
    cy.intercept(`${this.Urls.admin_deposit_list()}**`, {
      body: {
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
    cy.visit(this.Urls.admin_origin_save_requests());

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

describe('Test Admin Origin Save', function() {

  it(`should reject a save code now request with note`, function() {
    const originUrl = `https://example.org/${Date.now()}`;
    const rejectionNote = 'The provided URL does not target a git repository.';

    // anonymous user creates a request put in pending state
    cy.visit(this.Urls.origin_save());

    cy.get('#swh-input-origin-url')
      .type(originUrl);

    cy.get('#swh-input-origin-save-submit')
      .click();

    // admin user logs in and visits save code now admin page
    cy.adminLogin();
    cy.visit(this.Urls.admin_origin_save_requests());

    // admin rejects the save request and adds a rejection note
    cy.contains('#swh-origin-save-pending-requests', originUrl)
      .click();

    cy.get('#swh-reject-save-origin-request')
      .click();

    cy.get('#swh-rejection-text')
      .then(textarea => {
        textarea.val(rejectionNote);
      });

    cy.get('#swh-rejection-submit')
      .click();

    cy.get('#swh-web-modal-confirm-ok-btn')
      .click();

    // checks rejection note has been saved to swh-web database
    cy.request(this.Urls.api_1_save_origin('git', originUrl))
      .then(response => {
        expect(response.body[0]['note']).to.equal(rejectionNote);
      });

    // check rejection note is displayed by clicking on the info icon
    // in requests table from public save code now page
    cy.visit(this.Urls.origin_save());
    cy.get('#swh-origin-save-requests-list-tab')
      .click();

    cy.contains('#swh-origin-save-requests tr', originUrl);
    cy.get('.swh-save-request-info')
      .eq(0)
      .click();

    cy.get('.popover-body')
      .should('have.text', rejectionNote);

    // remove rejected request from swh-web database to avoid side effects
    // in tests located in origin-save.spec.js
    cy.visit(this.Urls.admin_origin_save_requests());
    cy.get('#swh-save-requests-rejected-tab')
      .click();

    cy.contains('#swh-origin-save-rejected-requests', originUrl)
      .click();

    cy.get('#swh-remove-rejected-save-origin-request')
      .click();

    cy.get('#swh-web-modal-confirm-ok-btn')
      .click();
  });
});
