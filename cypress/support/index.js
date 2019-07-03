/**
 * Copyright (C) 2019  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

Cypress.Screenshot.defaults({
  screenshotOnRunFailure: false
});

before(function() {
  cy.visit('/').window().then(win => {
    this.Urls = win.Urls;
  });
});
