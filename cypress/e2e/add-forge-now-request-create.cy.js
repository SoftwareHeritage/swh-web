/**
 * Copyright (C) 2022  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

function populateForm(type, url, contact, email, consent, comment) {
  cy.get('#swh-input-forge-type').select(type);
  if (url) {
    cy.get('#swh-input-forge-url').clear().type(url);
  }
  cy.get('#swh-input-forge-contact-name').clear().type(contact);
  cy.get('#swh-input-forge-contact-email').clear().type(email);
  if (comment) {
    cy.get('#swh-input-forge-comment').clear().type(comment);
  }
  cy.get('#swh-input-consent-check').click({force: consent === 'on'});
}

function submitForm() {
  cy.get('#requestCreateForm input[type=submit]').click();
  cy.get('#requestCreateForm').then($form => {
    if ($form[0].checkValidity()) {
      cy.wait('@addForgeRequestCreate');
    }
  });
}

function initTest(testEnv) {
  testEnv.addForgeNowUrl = testEnv.Urls.forge_add_create();
  testEnv.addForgeNowRequestCreateUrl = testEnv.Urls.api_1_add_forge_request_create();
  testEnv.listAddForgeRequestsUrl = testEnv.Urls.add_forge_request_list_datatables();
  cy.intercept('POST', testEnv.addForgeNowRequestCreateUrl + '**')
      .as('addForgeRequestCreate');
  cy.intercept(testEnv.listAddForgeRequestsUrl + '**')
      .as('addForgeRequestsList');
}

describe('Browse requests list tests', function() {
  beforeEach(function() {
    initTest(this);
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
    populateForm('gitlab', 'https://gitlab.org', 'admin', 'admin@example.org', 'on', '');
    submitForm();

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

    populateForm('gitea', 'https://gitea.org', 'admin', 'admin@example.org', 'on', '');
    submitForm();
    populateForm('cgit', 'https://cgit.org', 'admin', 'admin@example.org', 'on', '');
    submitForm();

    // user requests filter checkbox should be in the DOM
    cy.get('#swh-add-forge-requests-list-tab').click();
    cy.get('#swh-add-forge-user-filter').should('exist').should('be.checked');

    cy.wait('@addForgeRequestsList');
    // ensure datatable got rendered
    cy.wait(100);

    // check unfiltered user requests
    cy.get('tbody tr').then(rows => {
      expect(rows.length).to.eq(2);
    });

    cy.get('#swh-add-forge-user-filter')
      .uncheck({force: true});

    cy.wait('@addForgeRequestsList');
    // ensure datatable got rendered
    cy.wait(100);

    // Users now sees everything
    cy.get('tbody tr').then(rows => {
      expect(rows.length).to.eq(2 + 1);
    });
  });

  it('should display search link when first forge origin has been loaded', function() {
    const forgeUrl = 'https://cgit.example.org';
    cy.intercept(this.listAddForgeRequestsUrl + '**', {body: {
      'recordsTotal': 1,
      'draw': 1,
      'recordsFiltered': 1,
      'data': [
        {
          'id': 1,
          'inbound_email_address': 'add-forge-now+15.yPalKD34nGJ-FYHwKXdmPQVkQ2c@example.org',
          'status': 'FIRST_ORIGIN_LOADED',
          'submission_date': '2022-09-22T05:31:47.566000Z',
          'submitter_name': 'johndoe',
          'submitter_email': 'johndoe@example.org',
          'submitter_forward_username': true,
          'forge_type': 'cgit',
          'forge_url': forgeUrl,
          'forge_contact_email': 'admin@example.org',
          'forge_contact_name': 'Admin',
          'last_modified_date': '2022-09-22T05:31:47.576000Z'
        }
      ]
    }}).as('addForgeRequestsList');

    cy.visit(this.addForgeNowUrl);

    cy.get('#swh-add-forge-requests-list-tab').click();

    cy.wait('@addForgeRequestsList');

    let originsSearchUrl = `${this.Urls.browse_search()}?q=${encodeURIComponent(forgeUrl)}`;
    originsSearchUrl += '&with_visit=true&with_content=true';

    cy.get('.swh-search-forge-origins')
      .should('have.attr', 'href', originsSearchUrl);

  });

});

describe('Test add-forge-request creation', function() {
  beforeEach(function() {
    initTest(this);
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
    cy.get('.swh-add-forge-now-item')
      .should('have.class', 'active');

    cy.get('#swh-add-forge-requests-help-tab').click();
    cy.get('#swh-add-forge-tab')
      .should('not.have.class', 'active');
    cy.get('#swh-add-forge-requests-list-tab')
      .should('not.have.class', 'active');
    cy.get('#swh-add-forge-requests-help-tab')
      .should('have.class', 'active');
    cy.url()
      .should('include', `${this.Urls.forge_add_help()}`);
    cy.get('.swh-add-forge-now-item')
      .should('have.class', 'active');

    cy.get('#swh-add-forge-tab').click();
    cy.get('#swh-add-forge-tab')
      .should('have.class', 'active');
    cy.get('#swh-add-forge-requests-list-tab')
      .should('not.have.class', 'active');
    cy.get('#swh-add-forge-requests-help-tab')
      .should('not.have.class', 'active');
    cy.url()
      .should('include', `${this.Urls.forge_add_create()}`);
    cy.get('.swh-add-forge-now-item')
      .should('have.class', 'active');
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
    populateForm('bitbucket', 'https://gitlab.com', 'test', 'test@example.com', 'on', 'test comment');
    submitForm();

    cy.visit(this.addForgeNowUrl);
    cy.get('#swh-add-forge-requests-list-tab').click();

    cy.wait('@addForgeRequestsList');

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
    populateForm('bitbucket', 'https://gitlab.com', 'test', 'test@example.com', 'on', 'test comment');
    submitForm();

    submitForm(); // Submitting the same data again

    cy.get('#userMessage')
      .should('have.class', 'badge-danger')
      .should('contain', 'already exists');
  });

  it('should show error message', function() {
    cy.userLogin();

    cy.visit(this.addForgeNowUrl);

    populateForm(
      'bitbucket', '', 'test', 'test@example.com', 'off', 'comment'
    );
    submitForm();

    cy.get('#requestCreateForm').then(
      $form => expect($form[0].checkValidity()).to.be.false
    );

  });

  it('should not validate form when forge URL is invalid', function() {
    cy.userLogin();
    cy.visit(this.addForgeNowUrl);
    populateForm('bitbucket', 'bitbucket.org', 'test', 'test@example.com', 'on', 'test comment');
    submitForm();

    cy.get('#swh-input-forge-url')
      .then(input => {
        assert.isFalse(input[0].checkValidity());
      });
  });

});
