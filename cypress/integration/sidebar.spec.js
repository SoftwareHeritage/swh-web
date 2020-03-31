/**
 * Copyright (C) 2019  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

const url = '/';

describe('Sidebar tests On Large Screen', function() {
  beforeEach(function() {
    cy.visit(url, {
      onBeforeLoad: (win) => {
        win.localStorage.clear();
      }
    });
  });

  it('should toggle sidebar when swh-push-menu is clicked', function() {
    cy.get('.swh-push-menu')
      .click();
    cy.get('body')
      .should('have.class', 'sidebar-collapse')
      .get('.nav-link > p')
      .should('not.be.visible');

    cy.get('.swh-push-menu')
      .click();
    cy.get('body')
      .should('not.have.class', 'sidebar-collapse')
      .get('.nav-link > p')
      .should('be.visible');
  });

  it('should have less width when collapsed compared to open', function() {
    let collapseWidth;
    cy.get('.swh-push-menu')
      .click()
      .get('.swh-sidebar-collapsed')
      .invoke('width')
      .then((width) => {
        collapseWidth = width;
      })
      .get('.swh-push-menu')
      .click()
      .get('.swh-sidebar-expanded')
      .invoke('width')
      .then(openWidth => {
        assert.isBelow(collapseWidth, openWidth);
      });
  });
});

describe('Sidebar Tests on small screens', function() {
  beforeEach(function() {
    cy.viewport('iphone-6');
    cy.visit(url);
  });

  it('should be collapsed by default', function() {
    cy.get('.swh-sidebar')
      .should('not.be.visible');
  });

  it('should toggle sidebar when swh-push-menu is clicked', function() {
    cy.get('.swh-push-menu')
      .click()
      .get('.swh-sidebar')
      .should('be.visible')
      .get('#sidebar-overlay')
      .click({force: true})
      .get('.swh-sidebar')
      .should('not.be.visible');
  });
});
