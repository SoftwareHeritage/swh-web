/**
 * Copyright (C) 2019  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

const url = '/'

describe('Sidebar tests', function() {
  beforeEach(function () {
    cy.visit(url);
  })

  it('should toggle sidebar when swh-push-menu is clicked', function() {
    cy.get('.swh-push-menu')
      .click()
      .then(() => {
        cy.get('body')
          .should('have.class', 'sidebar-collapse')
          .get('.nav-link > p')
          .should('have.css', 'opacity', '0');
      })
      .get('.swh-push-menu')
      .click()
      .then(() => {
        cy.get('body')
          .should('have.class', 'sidebar-open')
          .get('.nav-link > p')
          .should('not.have.css', 'opacity', '0');
      })
  })

  it('should have less width when collapsed compared to open', function() {
    let collapsedWidth, expandedWidth;
    cy.get('.swh-push-menu')
      .click()
      .wait(250)
      .get('.swh-sidebar')
      .should('have.css', 'width')
      .then((width) => {
        collapsedWidth = parseInt(width);
      })
      .get('.swh-push-menu')
      .click()
      .wait(250)
      .get('.swh-sidebar')
      .should('have.css', 'width')
      .then((width) => {
        expandedWidth = parseInt(width);
      })
      .then(() => {
        assert.isBelow(collapsedWidth, expandedWidth);
      })
  })
})
