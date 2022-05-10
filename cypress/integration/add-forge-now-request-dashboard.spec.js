/**
 * Copyright (C) 2022  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

let requestId, forgeDomain;

function createDummyRequest(urls) {
  cy.task('db:add_forge_now:delete');
  cy.userLogin();

  cy.getCookie('csrftoken').its('value').then((token) => {
    cy.request({
      method: 'POST',
      url: urls.api_1_add_forge_request_create(),
      body: {
        forge_type: 'bitbucket',
        forge_url: 'test.example.com',
        forge_contact_email: 'test@example.com',
        forge_contact_name: 'test user',
        submitter_forward_username: true,
        forge_contact_comment: 'test comment'
      },
      headers: {
        'X-CSRFToken': token
      }
    }).then((response) => {
      // setting requestId and forgeDomain from response
      requestId = response.body.id;
      forgeDomain = response.body.forge_domain;
      // logout the user
      cy.visit(urls.swh_web_homepage());
      cy.contains('a', 'logout').click();
    });
  });
}

describe('Test add forge now request dashboard load', function() {

  before(function() {
    // Create an add-forge-request object in the DB
    createDummyRequest(this.Urls);
  });

  beforeEach(function() {
    const url = this.Urls.add_forge_now_request_dashboard(requestId);
    // request dashboard require admin permissions to view
    cy.adminLogin();
    cy.intercept(`${this.Urls.api_1_add_forge_request_get(requestId)}**`).as('forgeRequestGet');
    cy.visit(url);
  });

  it('should load add forge request details', function() {
    cy.wait('@forgeRequestGet');
    cy.get('#requestStatus')
      .should('contain', 'Pending');

    cy.get('#requestType')
      .should('contain', 'bitbucket');

    cy.get('#requestURL')
      .should('contain', 'test.example.com');

    cy.get('#requestContactEmail')
      .should('contain', 'test@example.com');

    cy.get('#requestContactName')
      .should('contain', 'test user');

    cy.get('#requestContactEmail')
      .should('contain', 'test@example.com');

    cy.get('#requestContactConsent')
      .should('contain', 'true');

    cy.get('#submitterMessage')
      .should('contain', 'test comment');
  });

  it('should show send message link', function() {
    cy.wait('@forgeRequestGet');

    cy.get('#contactForgeAdmin')
      .should('have.attr', 'emailto')
      .and('include', 'test@example.com');

    cy.get('#contactForgeAdmin')
      .should('have.attr', 'emailsubject')
      .and('include', `Software Heritage archival request for ${forgeDomain}`);
  });

  it('should not show any error message', function() {
    cy.wait('@forgeRequestGet');

    cy.get('#fetchError')
      .should('have.class', 'd-none');
    cy.get('#requestDetails')
      .should('not.have.class', 'd-none');
  });

  it('should show error message for an api error', function() {
    // requesting with a non existing request ID
    const invalidRequestId = requestId + 10;
    const url = this.Urls.add_forge_now_request_dashboard(invalidRequestId);

    cy.intercept(`${this.Urls.api_1_add_forge_request_get(invalidRequestId)}**`,
                 {statusCode: 400}).as('forgeAddInvalidRequest');

    cy.visit(url);
    cy.wait('@forgeAddInvalidRequest');
    cy.get('#fetchError')
      .should('not.have.class', 'd-none');
    cy.get('#requestDetails')
      .should('have.class', 'd-none');
  });

  it('should load add forge request history', function() {
    cy.wait('@forgeRequestGet');

    cy.get('#requestHistory')
      .children()
      .should('have.length', 1);

    cy.get('#requestHistory')
      .children()
      .should('contain', 'New status: Pending');

    cy.get('#requestHistory')
      .should('contain', 'From user (SUBMITTER)');
  });

  it('should load possible next status', function() {
    cy.wait('@forgeRequestGet');
    // 3 possible next status and the comment option
    cy.get('#decisionOptions')
      .children()
      .should('have.length', 4);
  });
});

function populateAndSubmitForm() {
  cy.get('#decisionOptions').select('WAITING_FOR_FEEDBACK');
  cy.get('#updateComment').type('This is an update comment');
  cy.get('#updateRequestForm').submit();
}

describe('Test forge now request update', function() {

  beforeEach(function() {
    createDummyRequest(this.Urls);

    const url = this.Urls.add_forge_now_request_dashboard(requestId);
    cy.adminLogin();
    // intercept GET API on page load
    cy.intercept(`${this.Urls.api_1_add_forge_request_get(requestId)}**`).as('forgeRequestGet');
    // intercept update POST API
    cy.intercept('POST', `${this.Urls.api_1_add_forge_request_update(requestId)}**`).as('forgeRequestUpdate');
    cy.visit(url);
  });

  it('should submit correct details', function() {
    cy.wait('@forgeRequestGet');
    populateAndSubmitForm();

    // Making sure posting the right data
    cy.wait('@forgeRequestUpdate').its('request.body')
      .should('include', 'new_status')
      .should('include', 'text')
      .should('include', 'WAITING_FOR_FEEDBACK');
  });

  it('should show success message', function() {
    cy.wait('@forgeRequestGet');
    populateAndSubmitForm();

    // Making sure showing the success message
    cy.wait('@forgeRequestUpdate');
    cy.get('#userMessage')
      .should('contain', 'The request status has been updated')
      .should('not.have.class', 'badge-danger')
      .should('have.class', 'badge-success');
  });

  it('should update the dashboard after submit', function() {
    cy.wait('@forgeRequestGet');
    populateAndSubmitForm();

    // Making sure the UI is updated after the submit
    cy.wait('@forgeRequestGet');
    cy.get('#requestStatus')
      .should('contain', 'Waiting for feedback');

    cy.get('#requestHistory')
      .children()
      .should('have.length', 2);

    cy.get('#requestHistory')
      .children()
      .should('contain', 'New status: Waiting for feedback');

    cy.get('#requestHistory')
      .children()
      .should('contain', 'This is an update comment');

    cy.get('#requestHistory')
      .children()
      .should('contain', 'Status changed to: Waiting for feedback');

    cy.get('#decisionOptions')
      .children()
      .should('have.length', 2);
  });

  it('should show an error on API failure', function() {
    cy.intercept('POST',
                 `${this.Urls.api_1_add_forge_request_update(requestId)}**`,
                 {forceNetworkError: true})
      .as('updateFailedRequest');
    cy.get('#updateComment').type('This is an update comment');
    cy.get('#updateRequestForm').submit();

    cy.wait('@updateFailedRequest');
    cy.get('#userMessage')
      .should('contain', 'Sorry; Updating the request failed')
      .should('have.class', 'badge-danger')
      .should('not.have.class', 'badge-success');
  });
});
