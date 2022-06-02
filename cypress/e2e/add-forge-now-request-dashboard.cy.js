/**
 * Copyright (C) 2022  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

let requestId;
let requestForgeDomain;
let requestInboundEmailAddress;

const requestData = {
  forge_type: 'bitbucket',
  forge_url: 'test.example.com',
  forge_contact_email: 'test@example.com',
  forge_contact_name: 'test user',
  submitter_forward_username: true,
  forge_contact_comment: 'test comment'
};

function createDummyRequest(urls) {
  cy.task('db:add_forge_now:delete');
  cy.userLogin();

  return cy.getCookie('csrftoken').its('value').then((token) => {
    cy.request({
      method: 'POST',
      url: urls.api_1_add_forge_request_create(),
      body: requestData,
      headers: {
        'X-CSRFToken': token
      }
    }).then((response) => {
      // setting requestId and forgeDomain from response
      requestId = response.body.id;
      requestForgeDomain = response.body.forge_domain;
      requestInboundEmailAddress = response.body.inbound_email_address;
      // logout the user
      cy.visit(urls.swh_web_homepage());
      cy.contains('a', 'logout').click();
    });
  });
}

function genEmailSrc() {
  return `Message-ID: <d5c43e75-2a11-250a-43e3-37034ae3904b@example.com>
Date: Tue, 19 Apr 2022 14:00:56 +0200
MIME-Version: 1.0
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101
 Thunderbird/91.8.0
To: ${requestData.forge_contact_email}
Cc: ${requestInboundEmailAddress}
Reply-To: ${requestInboundEmailAddress}
Subject: Software Heritage archival request for test.example.com
Content-Language: en-US
From: Test Admin <admin@example.com>
Content-Type: text/plain; charset=UTF-8; format=flowed
Content-Transfer-Encoding: 7bit

Dear forge administrator,

The mission of Software Heritage is to collect, preserve and share all the
publicly available source code (see https://www.softwareheritage.org for more
information).

We just received a request to add the forge hosted at https://test.example.com to the
list of software origins that are archived, and it is our understanding that you
are the contact person for this forge.

In order to archive the forge contents, we will have to periodically pull the
public repositories it contains and clone them into the
Software Heritage archive.

Would you be so kind as to reply to this message to acknowledge the reception
of this email and let us know if there are any special steps we should take in
order to properly archive the public repositories hosted on your infrastructure?

Thank you in advance for your help.

Kind regards,
The Software Heritage team
`;
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
      .and('include', `Software Heritage archival request for ${requestForgeDomain}`);
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

describe('Test add forge now request update', function() {

  beforeEach(function() {
    createDummyRequest(this.Urls).then(() => {

      this.url = this.Urls.add_forge_now_request_dashboard(requestId);
      cy.adminLogin();
      // intercept GET API on page load
      cy.intercept(`${this.Urls.api_1_add_forge_request_get(requestId)}**`).as('forgeRequestGet');
      // intercept update POST API
      cy.intercept('POST', `${this.Urls.api_1_add_forge_request_update(requestId)}**`).as('forgeRequestUpdate');
      cy.visit(this.url).then(() => {
        cy.wait('@forgeRequestGet');
      });
    });
  });

  it('should submit correct details', function() {
    populateAndSubmitForm();

    // Making sure posting the right data
    cy.wait('@forgeRequestUpdate').its('request.body')
      .should('include', 'new_status')
      .should('include', 'text')
      .should('include', 'WAITING_FOR_FEEDBACK');
  });

  it('should show success message', function() {
    populateAndSubmitForm();

    // Making sure showing the success message
    cy.wait('@forgeRequestUpdate');
    cy.get('#userMessage')
      .should('contain', 'The request status has been updated')
      .should('not.have.class', 'badge-danger')
      .should('have.class', 'badge-success');
  });

  it('should update the dashboard after submit', function() {
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

  it('should update the dashboard after receiving email', function() {
    const emailSrc = genEmailSrc();
    cy.task('processAddForgeNowInboundEmail', emailSrc);

    // Refresh page and wait for the async request to complete
    cy.visit(this.url);
    cy.wait('@forgeRequestGet');

    cy.get('#requestHistory')
      .children()
      .should('have.length', 2);

    cy.get('#historyItem1')
      .click()
      .should('contain', 'New status: Waiting for feedback');

    cy.get('#historyItemBody1')
      .find('a')
      .should('contain', 'Open original message in email client')
      .should('have.prop', 'href').and('contain', '/message-source/').then(function(href) {
        cy.request(href).then((response) => {
          expect(response.headers['content-type'])
            .to.equal('text/email');

          expect(response.headers['content-disposition'])
            .to.match(/filename="add-forge-now-test.example.com-message\d+.eml"/);

          expect(response.body)
            .to.equal(emailSrc);
        });
      });
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
