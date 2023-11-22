/**
 * Copyright (C) 2019-2023  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import '@cypress/code-coverage/support';
import 'cypress-hmr-restarter';
import 'cypress-accessibility-checker';
import 'cypress-axe';

Cypress.Screenshot.defaults({
  screenshotOnRunFailure: false
});

Cypress.Commands.add('xhrShouldBeCalled', (alias, timesCalled) => {
  const testRoutes = cy.state('routes');
  const aliasRoute = Cypress._.find(testRoutes, {alias});
  expect(Object.keys(aliasRoute.requests || {})).to.have.length(timesCalled);
});

function loginUser(username, password) {
  const url = '/login/';
  return cy.request({
    url: url,
    method: 'GET'
  }).then(() => {
    cy.getCookie('sessionid').should('not.exist');
    cy.getCookie('csrftoken').its('value').then((token) => {
      cy.request({
        url: url,
        method: 'POST',
        form: true,
        followRedirect: false,
        body: {
          username: username,
          password: password,
          csrfmiddlewaretoken: token
        }
      }).then(() => {
        cy.getCookie('sessionid').should('exist');
        return cy.getCookie('csrftoken').its('value');
      });
    });
  });
}

Cypress.Commands.add('adminLogin', () => {
  return loginUser('admin', 'admin');
});

Cypress.Commands.add('userLogin', () => {
  return loginUser('user', 'user');
});

Cypress.Commands.add('user2Login', () => {
  return loginUser('user2', 'user2');
});

Cypress.Commands.add('ambassadorLogin', () => {
  return loginUser('ambassador', 'ambassador');
});

Cypress.Commands.add('depositLogin', () => {
  return loginUser('deposit', 'deposit');
});

Cypress.Commands.add('addForgeModeratorLogin', () => {
  return loginUser('add-forge-moderator', 'add-forge-moderator');
});

function mockCostlyRequests() {
  cy.intercept('https://status.softwareheritage.org/**', {
    body: {
      'result': {
        'status': [
          {
            'id': '5f7c4c567f50b304c1e7bd5f',
            'name': 'Save Code Now',
            'updated': '2020-11-30T13:51:21.151Z',
            'status': 'Operational',
            'status_code': 100
          }
        ]
      }
    }}).as('swhPlatformStatus');

  cy.intercept('/coverage', {
    body: ''
  }).as('swhCoverageWidget');
}
Cypress.Commands.add('mailmapAdminLogin', () => {
  return loginUser('mailmap-admin', 'mailmap-admin');
});

before(function() {

  mockCostlyRequests();

  cy.task('getSwhTestsData').then(testsData => {
    Object.assign(this, testsData);
  });

  cy.intercept('/jsreverse/').as('jsReverse');

  cy.visit('/');
  cy.wait('@jsReverse');
  cy.window().its('Urls').then(Urls => {
    this.Urls = Urls;
  });
});

beforeEach(function() {
  mockCostlyRequests();
});

Cypress.Commands.overwrite('type', (originalFn, subject, text, options = {}) => {
  options.delay = options.delay || 0;
  options.force = options.force || true;
  return originalFn(subject, text, options);
});
