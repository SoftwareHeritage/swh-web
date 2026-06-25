/**
 * Copyright (C) 2026  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

describe('Coverage page tests', function() {

  beforeEach(function() {
    cy.intercept('/coverage', (req) => {
      req.continue(); // re-enable request
    });
    cy.visit('/coverage/');
  });

  /*
    The coverage search features aren't testable in cypress
    because it doesn't expose find-in-page features,
    so we just check the needed things exist.
  */

  it('should have visually-hidden span for zenodo', function() {
    cy.contains('zenodo')
      .should('have.prop', 'tagName', 'SPAN')
      .and('have.class', 'visually-hidden')
      .and('have.attr', 'aria-hidden', 'true');
  });

  it('should have collapse with hidden until-found', function() {
    cy.get('.collapse')
      .should('have.length.greaterThan', 0)
      .each(($el) => {
        cy.wrap($el)
          .should('have.attr', 'role', 'region')
          .invoke('attr', 'hidden')
          .should('equal', 'until-found');
      });
  });

});
