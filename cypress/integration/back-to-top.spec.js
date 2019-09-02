/**
 * Copyright (C) 2019  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

const url = 'api/';

describe('Back-to-top button tests', function() {
  beforeEach(function() {
    cy.visit(url);
  });

  it('should be hidden when on top', function() {
    cy.get('#back-to-top').should('not.be.visible');
  });

  it('should be visible when scrolled down', function() {
    cy.scrollTo('bottom')
      .get('#back-to-top')
      .should('be.visible');
  });

  it('should scroll to top when clicked', function() {
    cy.scrollTo('bottom')
      .get('#back-to-top')
      .click()
      .window()
      .then(win => {
        assert.equal(win.scrollY, 0);
      });
  });
});
