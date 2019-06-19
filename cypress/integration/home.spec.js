/**
 * Copyright (C) 2019  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

const url = '/';

const $ = Cypress.$;

describe('Home Page Tests', function() {
  it('should display positive stats for each category', function() {
    cy.visit(url);
    cy.get('.swh-counter')
      .then((counters) => {
        for(let counter of counters) {
          let innerText = $(counter).text();
          const value = parseInt(innerText.replace(/,/g, ''));
          assert.isAbove(value, 0);
        }
      });
  })
})
