/**
 * Copyright (C) 2022-2024  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

function logout() {
  cy.contains('logout')
    .click();
}

describe('Test "Add Forge Now" moderation Login/logout', function() {
  beforeEach(function() {
    this.addForgeModerationUrl = this.Urls.add_forge_now_requests_moderation();
  });

  it('should redirect to default page', function() {
    cy.visit(this.addForgeModerationUrl)
      .get('input[name="username"]')
      .type('admin')
      .get('input[name="password"]')
      .type('admin')
      .get('.container form #login-submit')
      .click();

    cy.location('pathname')
      .should('be.equal', this.addForgeModerationUrl);
  });

  it('should redirect to correct page after login', function() {
    cy.visit(this.addForgeModerationUrl)
      .location('pathname')
      .should('be.equal', this.Urls.login());

    cy.adminLogin();
    cy.visit(this.addForgeModerationUrl)
      .location('pathname')
      .should('be.equal', this.addForgeModerationUrl);

    logout();
  });

  it('should not display moderation link in sidebar when anonymous', function() {
    cy.visit(this.addForgeModerationUrl);
    cy.get(`.app-sidebar a[href="${this.addForgeModerationUrl}"]`)
      .should('not.exist');
  });

  it('should not display moderation link when connected as unprivileged user', function() {
    cy.userLogin();
    cy.visit(this.addForgeModerationUrl);

    cy.get(`.app-sidebar a[href="${this.addForgeModerationUrl}"]`)
      .should('not.exist');

  });

  it('should display moderation link in sidebar when connected as privileged user', function() {
    cy.addForgeModeratorLogin();
    cy.visit(this.addForgeModerationUrl);

    cy.get(`.app-sidebar a[href="${this.addForgeModerationUrl}"]`)
      .should('exist');
  });

  it('should display moderation link in sidebar when connected as staff member', function() {
    cy.adminLogin();
    cy.visit(this.addForgeModerationUrl);

    cy.get(`.app-sidebar a[href="${this.addForgeModerationUrl}"]`)
      .should('exist');
  });
});

describe('Test "Add Forge Now" moderation listing', function() {
  beforeEach(function() {
    this.addForgeModerationUrl = this.Urls.add_forge_now_requests_moderation();
    this.listAddForgeRequestsUrl = this.Urls.add_forge_request_list_datatables();
  });

  it('should list add-forge-now requests', function() {
    cy.intercept(`${this.listAddForgeRequestsUrl}**`, {fixture: 'add-forge-now-requests'}).as('listRequests');

    let expectedRequests;
    cy.readFile('cypress/fixtures/add-forge-now-requests.json').then((result) => {
      expectedRequests = result['data'];
    });

    cy.addForgeModeratorLogin();
    cy.visit(this.addForgeModerationUrl);

    cy.get('.swh-add-forge-now-moderation-item')
      .should('have.class', 'active');

    cy.wait('@listRequests').then((xhr) => {
      cy.log('response:', xhr.response);
      cy.log(xhr.response.body);
      const requests = xhr.response.body.data;
      cy.log('Requests: ', requests);
      expect(requests.length).to.equal(expectedRequests.length);

      cy.get('#swh-add-forge-now-moderation-list').find('tbody > tr').as('rows');

      // only 2 entries
      cy.get('@rows').each((row, idx, collection) => {
        const request = requests[idx];
        const expectedRequest = expectedRequests[idx];
        assert.isNotNull(request);
        assert.isNotNull(expectedRequest);
        expect(request.id).to.be.equal(expectedRequest['id']);
        expect(request.status).to.be.equal(expectedRequest['status']);
        expect(request.submission_date).to.be.equal(expectedRequest['submission_date']);
        expect(request.forge_type).to.be.equal(expectedRequest['forge_type']);
        expect(request.forge_url).to.be.equal(expectedRequest['forge_url']);
      });
    });
  });

  it('should display useful links in requests table', function() {
    const forgeUrl = 'https://cgit.example.org';
    const requestId = 1;
    cy.intercept(this.listAddForgeRequestsUrl + '**', {body: {
      'recordsTotal': 1,
      'draw': 1,
      'recordsFiltered': 1,
      'data': [
        {
          'id': requestId,
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
          'last_modified_date': '2022-09-22T05:31:47.576000Z',
          'last_moderator': 'foo@softwareheritage.org'
        }
      ]
    }}).as('addForgeRequestsList');

    cy.addForgeModeratorLogin();
    cy.visit(this.addForgeModerationUrl);

    cy.wait('@addForgeRequestsList');

    let originsSearchUrl = `${this.Urls.browse_search()}?q=${encodeURIComponent(forgeUrl)}`;
    originsSearchUrl += '&with_visit=true&with_content=true';

    cy.get('.swh-forge-request-dashboard-link')
      .should('have.attr', 'href', this.Urls.add_forge_now_request_dashboard(requestId));

    cy.get('.swh-search-forge-origins')
      .should('have.attr', 'href', originsSearchUrl);
  });

});
