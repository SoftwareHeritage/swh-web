/**
 * Copyright (C) 2022  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

function populateForm(type, url, contact, email, consent, comment) {
  cy.get('#swh-input-forge-type').select(type);
  cy.get('#swh-input-forge-url').clear().type(url, {delay: 0, force: true});
  cy.get('#swh-input-forge-contact-name').clear().type(contact, {delay: 0, force: true});
  cy.get('#swh-input-forge-contact-email').clear().type(email, {delay: 0, force: true});
  if (comment) {
    cy.get('#swh-input-forge-comment').clear().type(comment, {delay: 0, force: true});
  }
  cy.get('#swh-input-consent-check').click({force: consent === 'on'});
}

describe('Browse requests list tests', function() {
  beforeEach(function() {
    this.addForgeNowUrl = this.Urls.forge_add_create();
    this.listAddForgeRequestsUrl = this.Urls.add_forge_request_list_datatables();
  });

  it('should not show user requests filter checkbox for anonymous users', function() {
    cy.visit(this.addForgeNowUrl);
    cy.get('#swh-add-forge-requests-list-tab').click();
    cy.get('#swh-add-forge-user-filter').should('not.exist');
  });

  it('should show user requests filter checkbox for authenticated users', function() {
    cy.userLogin();
    cy.visit(this.addForgeNowUrl);
    cy.get('#swh-add-forge-requests-list-tab').click();
    cy.get('#swh-add-forge-user-filter').should('exist').should('be.checked');
  });

  it('should only display user requests when filter is activated', function() {
    // Clean up previous state
    cy.task('db:add_forge_now:delete');
    // 'user2' logs in and create requests
    cy.user2Login();
    cy.visit(this.addForgeNowUrl);

    // create requests for the user 'user'
    populateForm('gitlab', 'gitlab.org', 'admin', 'admin@example.org', 'on', '');
    cy.get('#requestCreateForm').submit();

    // user requests filter checkbox should be in the DOM
    cy.get('#swh-add-forge-requests-list-tab').click();
    cy.get('#swh-add-forge-user-filter').should('exist').should('be.checked');

    // check unfiltered user requests
    cy.get('tbody tr').then(rows => {
      expect(rows.length).to.eq(1);
    });

    // user1 logout
    cy.contains('a', 'logout').click();

    // user logs in
    cy.userLogin();
    cy.visit(this.addForgeNowUrl);

    populateForm('gitea', 'gitea.org', 'admin', 'admin@example.org', 'on', '');
    cy.get('#requestCreateForm').submit();
    populateForm('cgit', 'cgit.org', 'admin', 'admin@example.org', 'on', '');
    cy.get('#requestCreateForm').submit();

    // user requests filter checkbox should be in the DOM
    cy.get('#swh-add-forge-requests-list-tab').click();
    cy.get('#swh-add-forge-user-filter').should('exist').should('be.checked');

    // check unfiltered user requests
    cy.get('tbody tr').then(rows => {
      expect(rows.length).to.eq(2);
    });

    cy.get('#swh-add-forge-user-filter')
      .uncheck({force: true});

    // Users now sees everything
    cy.get('tbody tr').then(rows => {
      expect(rows.length).to.eq(2 + 1);
    });
  });
});

describe('Test add-forge-request creation', function() {
  beforeEach(function() {
    this.addForgeNowUrl = this.Urls.forge_add_create();
  });

  it('should show all the tabs for every user', function() {
    cy.visit(this.addForgeNowUrl);

    cy.get('#swh-add-forge-tab')
      .should('have.class', 'nav-link');

    cy.get('#swh-add-forge-requests-list-tab')
      .should('have.class', 'nav-link');

    cy.get('#swh-add-forge-requests-help-tab')
      .should('have.class', 'nav-link');
  });

  it('should show create forge tab by default', function() {
    cy.visit(this.addForgeNowUrl);

    cy.get('#swh-add-forge-tab')
      .should('have.class', 'active');

    cy.get('#swh-add-forge-requests-list-tab')
      .should('not.have.class', 'active');
  });

  it('should show login link for anonymous user', function() {
    cy.visit(this.addForgeNowUrl);

    cy.get('#loginLink')
      .should('be.visible')
      .should('contain', 'log in');
  });

  it('should bring back after login', function() {
    cy.visit(this.addForgeNowUrl);

    cy.get('#loginLink')
      .should('have.attr', 'href')
      .and('include', `${this.Urls.login()}?next=${this.Urls.forge_add_create()}`);
  });

  it('should change tabs on click', function() {
    cy.visit(this.addForgeNowUrl);

    cy.get('#swh-add-forge-requests-list-tab').click();
    cy.get('#swh-add-forge-tab')
      .should('not.have.class', 'active');
    cy.get('#swh-add-forge-requests-list-tab')
      .should('have.class', 'active');
    cy.get('#swh-add-forge-requests-help-tab')
      .should('not.have.class', 'active');
    cy.url()
      .should('include', `${this.Urls.forge_add_list()}`);

    cy.get('#swh-add-forge-requests-help-tab').click();
    cy.get('#swh-add-forge-tab')
      .should('not.have.class', 'active');
    cy.get('#swh-add-forge-requests-list-tab')
      .should('not.have.class', 'active');
    cy.get('#swh-add-forge-requests-help-tab')
      .should('have.class', 'active');
    cy.url()
      .should('include', `${this.Urls.forge_add_help()}`);

    cy.get('#swh-add-forge-tab').click();
    cy.get('#swh-add-forge-tab')
      .should('have.class', 'active');
    cy.get('#swh-add-forge-requests-list-tab')
      .should('not.have.class', 'active');
    cy.get('#swh-add-forge-requests-help-tab')
      .should('not.have.class', 'active');
    cy.url()
      .should('include', `${this.Urls.forge_add_create()}`);
  });

  it('should show create form elements to authenticated user', function() {
    cy.userLogin();
    cy.visit(this.addForgeNowUrl);

    cy.get('#swh-input-forge-type')
      .should('be.visible');

    cy.get('#swh-input-forge-url')
      .should('be.visible');

    cy.get('#swh-input-forge-contact-name')
      .should('be.visible');

    cy.get('#swh-input-consent-check')
      .should('be.visible');

    cy.get('#swh-input-forge-comment')
      .should('be.visible');

    cy.get('#swh-input-form-submit')
      .should('be.visible');
  });

  it('should show browse requests table for every user', function() {
    // testing only for anonymous
    cy.visit(this.addForgeNowUrl);

    cy.get('#swh-add-forge-requests-list-tab').click();
    cy.get('#add-forge-request-browse')
      .should('be.visible');

    cy.get('#loginLink')
      .should('not.exist');
  });

  it('should update browse list on successful submission', function() {
    cy.userLogin();
    cy.visit(this.addForgeNowUrl);
    populateForm('bitbucket', 'gitlab.com', 'test', 'test@example.com', 'on', 'test comment');
    cy.get('#requestCreateForm').submit();

    cy.visit(this.addForgeNowUrl);
    cy.get('#swh-add-forge-requests-list-tab').click();
    cy.get('#add-forge-request-browse')
      .should('be.visible')
      .should('contain', 'gitlab.com');

    cy.get('#add-forge-request-browse')
      .should('be.visible')
      .should('contain', 'Pending');
  });

  it('should show error message on conflict', function() {
    cy.userLogin();
    cy.visit(this.addForgeNowUrl);
    populateForm('bitbucket', 'gitlab.com', 'test', 'test@example.com', 'on', 'test comment');
    cy.get('#requestCreateForm').submit();

    cy.get('#requestCreateForm').submit(); // Submitting the same data again

    cy.get('#userMessage')
      .should('have.class', 'badge-danger')
      .should('contain', 'already exists');
  });

  it('should show error message', function() {
    cy.userLogin();

    cy.intercept('POST', `${this.Urls.api_1_add_forge_request_create()}**`,
                 {
                   body: {
                     'exception': 'BadInputExc',
                     'reason': '{"add-forge-comment": ["This field is required"]}'
                   },
                   statusCode: 400
                 }).as('errorRequest');

    cy.visit(this.addForgeNowUrl);

    populateForm(
      'bitbucket', 'gitlab.com', 'test', 'test@example.com', 'off', 'comment'
    );
    cy.get('#requestCreateForm').submit();

    cy.wait('@errorRequest').then((xhr) => {
      cy.get('#userMessage')
        .should('have.class', 'badge-danger')
        .should('contain', 'field is required');
    });
  });

});
