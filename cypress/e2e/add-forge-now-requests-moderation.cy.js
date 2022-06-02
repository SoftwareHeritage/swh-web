/**
 * Copyright (C) 2022  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

const defaultRedirect = '/admin/login/';

let addForgeModerationUrl;
let listAddForgeRequestsUrl;

function logout() {
  cy.contains('a', 'logout')
    .click();
}

describe('Test "Add Forge Now" moderation Login/logout', function() {
  before(function() {
    addForgeModerationUrl = this.Urls.add_forge_now_requests_moderation();
  });

  it('should redirect to default page', function() {
    cy.visit(addForgeModerationUrl)
      .get('input[name="username"]')
      .type('admin')
      .get('input[name="password"]')
      .type('admin')
      .get('.container form')
      .submit();

    cy.location('pathname')
      .should('be.equal', addForgeModerationUrl);
  });

  it('should redirect to correct page after login', function() {
    cy.visit(addForgeModerationUrl)
      .location('pathname')
      .should('be.equal', defaultRedirect);

    cy.adminLogin();
    cy.visit(addForgeModerationUrl)
      .location('pathname')
      .should('be.equal', addForgeModerationUrl);

    logout();
  });

  it('should not display moderation link in sidebar when anonymous', function() {
    cy.visit(addForgeModerationUrl);
    cy.get(`.sidebar a[href="${addForgeModerationUrl}"]`)
      .should('not.exist');
  });

  it('should not display moderation link when connected as unprivileged user', function() {
    cy.userLogin();
    cy.visit(addForgeModerationUrl);

    cy.get(`.sidebar a[href="${addForgeModerationUrl}"]`)
      .should('not.exist');

  });

  it('should display moderation link in sidebar when connected as privileged user', function() {
    cy.addForgeModeratorLogin();
    cy.visit(addForgeModerationUrl);

    cy.get(`.sidebar a[href="${addForgeModerationUrl}"]`)
      .should('exist');
  });

  it('should display moderation link in sidebar when connected as staff member', function() {
    cy.adminLogin();
    cy.visit(addForgeModerationUrl);

    cy.get(`.sidebar a[href="${addForgeModerationUrl}"]`)
      .should('exist');
  });
});

describe('Test "Add Forge Now" moderation listing', function() {
  before(function() {
    addForgeModerationUrl = this.Urls.add_forge_now_requests_moderation();
    listAddForgeRequestsUrl = this.Urls.add_forge_request_list_datatables();
  });

  it('should list add-forge-now requests', function() {
    cy.intercept(`${listAddForgeRequestsUrl}**`, {fixture: 'add-forge-now-requests'}).as('listRequests');

    let expectedRequests;
    cy.readFile('cypress/fixtures/add-forge-now-requests.json').then((result) => {
      expectedRequests = result['data'];
    });

    cy.addForgeModeratorLogin();
    cy.visit(addForgeModerationUrl);

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

});
