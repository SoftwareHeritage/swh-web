/**
 * Copyright (C) 2022  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

const $ = Cypress.$;

function fillFormAndSubmitMailmap(fromEmail, displayName, activated) {
  if (fromEmail) {
    cy.get('#swh-mailmap-from-email')
      .clear()
      .type(fromEmail);
  }

  if (displayName) {
    cy.get('#swh-mailmap-display-name')
      .clear()
      .type(displayName);
  }

  if (activated) {
    cy.get('#swh-mailmap-display-name-activated')
      .check({force: true});
  } else {
    cy.get('#swh-mailmap-display-name-activated')
      .uncheck({force: true});
  }

  cy.get('#swh-mailmap-form-submit')
    .click();
}

function addNewMailmap(fromEmail, displayName, activated) {
  cy.get('#swh-add-new-mailmap')
    .click();

  fillFormAndSubmitMailmap(fromEmail, displayName, activated);
}

function updateMailmap(fromEmail, displayName, activated) {
  cy.contains('Edit')
    .click();

  fillFormAndSubmitMailmap(fromEmail, displayName, activated);
}

function checkMailmapRow(fromEmail, displayName, activated,
                         processed = false, row = 1, nbRows = 1) {
  cy.get('tbody tr').then(rows => {
    assert.equal(rows.length, 1);
    const cells = rows[0].cells;
    assert.equal($(cells[0]).text(), fromEmail);
    assert.include($(cells[1]).html(), 'mdi-check-bold');
    assert.equal($(cells[2]).text(), displayName);
    assert.include($(cells[3]).html(), activated ? 'mdi-check-bold' : 'mdi-close-thick');
    assert.notEqual($(cells[4]).text(), '');
    assert.include($(cells[5]).html(), processed ? 'mdi-check-bold' : 'mdi-close-thick');
  });
}

describe('Test mailmap administration', function() {

  before(function() {
    this.url = this.Urls.admin_mailmap();
  });

  beforeEach(function() {
    cy.task('db:user_mailmap:delete');
    cy.intercept('POST', this.Urls.profile_mailmap_add())
      .as('mailmapAdd');
    cy.intercept('POST', this.Urls.profile_mailmap_update())
      .as('mailmapUpdate');
    cy.intercept(`${this.Urls.profile_mailmap_list_datatables()}**`)
      .as('mailmapList');
  });

  it('should not display mailmap admin link in sidebar when anonymous', function() {
    cy.visit(this.url);
    cy.get('.swh-mailmap-admin-item')
      .should('not.exist');
  });

  it('should not display mailmap admin link when connected as unprivileged user', function() {
    cy.userLogin();
    cy.visit(this.url);

    cy.get('.swh-mailmap-admin-item')
      .should('not.exist');

  });

  it('should display mailmap admin link in sidebar when connected as privileged user', function() {
    cy.mailmapAdminLogin();
    cy.visit(this.url);

    cy.get('.swh-mailmap-admin-item')
      .should('exist')
      .should('have.class', 'active');

  });

  it('should not create a new mailmap when input data are empty', function() {
    cy.mailmapAdminLogin();
    cy.visit(this.url);

    addNewMailmap('', '', true);

    cy.get('#swh-mailmap-form :invalid').should('exist');

    cy.get('#swh-mailmap-form')
      .should('be.visible');

  });

  it('should not create a new mailmap when from email is invalid', function() {
    cy.mailmapAdminLogin();
    cy.visit(this.url);

    addNewMailmap('invalid_email', 'display name', true);

    cy.get('#swh-mailmap-form :invalid').should('exist');

    cy.get('#swh-mailmap-form')
      .should('be.visible');
  });

  it('should create a new mailmap when input data are valid', function() {
    cy.mailmapAdminLogin();
    cy.visit(this.url);

    const fromEmail = 'user@example.org';
    const displayName = 'New user display name';
    addNewMailmap(fromEmail, displayName, true);
    cy.wait('@mailmapAdd');

    cy.get('#swh-mailmap-form :invalid').should('not.exist');

    // ensure table redraw before next check
    cy.contains(fromEmail).should('be.visible');

    cy.get('#swh-mailmap-form')
      .should('not.be.visible');

    checkMailmapRow(fromEmail, displayName, true);

  });

  it('should not create a new mailmap for an email already mapped', function() {
    cy.mailmapAdminLogin();
    cy.visit(this.url);

    const fromEmail = 'user@example.org';
    const displayName = 'New user display name';
    addNewMailmap(fromEmail, displayName, true);
    cy.wait('@mailmapAdd');

    addNewMailmap(fromEmail, displayName, true);
    cy.wait('@mailmapAdd');

    cy.get('#swh-mailmap-form')
      .should('not.be.visible');

    cy.contains('Error')
      .should('be.visible');

    checkMailmapRow(fromEmail, displayName, true);

  });

  it('should update a mailmap', function() {
    cy.mailmapAdminLogin();
    cy.visit(this.url);

    const fromEmail = 'user@example.org';
    const displayName = 'New display name';
    addNewMailmap(fromEmail, displayName, false);
    cy.wait('@mailmapAdd');

    cy.get('#swh-mailmap-form :invalid').should('not.exist');

    // ensure table redraw before next check
    cy.contains(fromEmail).should('be.visible');

    cy.get('#swh-mailmap-form')
      .should('not.be.visible');

    checkMailmapRow(fromEmail, displayName, false);

    const newDisplayName = 'Updated display name';
    updateMailmap('', newDisplayName, true);
    cy.wait('@mailmapUpdate');

    cy.get('#swh-mailmap-form :invalid').should('not.exist');

    // ensure table redraw before next check
    cy.contains(fromEmail).should('be.visible');

    cy.get('#swh-mailmap-form')
      .should('not.be.visible');

    checkMailmapRow(fromEmail, newDisplayName, true);

  });

  it('should indicate when a mailmap has been processed', function() {
    cy.mailmapAdminLogin();
    cy.visit(this.url);

    const fromEmail = 'user@example.org';
    const displayName = 'New user display name';
    addNewMailmap(fromEmail, displayName, true);
    cy.wait('@mailmapAdd');

    // ensure table redraw before next check
    cy.contains(fromEmail).should('be.visible');

    checkMailmapRow(fromEmail, displayName, true, false);

    cy.task('db:user_mailmap:mark_processed');

    cy.visit(this.url);
    // ensure table redraw before next check
    cy.contains(fromEmail).should('be.visible');

    checkMailmapRow(fromEmail, displayName, true, true);

  });

});
