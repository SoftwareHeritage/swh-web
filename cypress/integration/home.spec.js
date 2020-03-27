/**
 * Copyright (C) 2019  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

const $ = Cypress.$;

const url = '/';

describe('Home Page Tests', function() {
  it('should display positive stats for each category', function() {

    cy.server();

    cy.route({
      method: 'GET',
      url: this.Urls.stat_counters()
    }).as('getStatCounters');

    cy.visit(url)
      .wait('@getStatCounters')
      .wait(500)
      .get('.swh-counter')
      .then((counters) => {
        for (let counter of counters) {
          let innerText = $(counter).text();
          const value = parseInt(innerText.replace(/,/g, ''));
          assert.isAbove(value, 0);
        }
      });
  });

  it('should display null counters when storage is empty', function() {

    cy.server();

    cy.route({
      method: 'GET',
      url: this.Urls.stat_counters(),
      response: {
        'stat_counters': {},
        'stat_counters_history': {}
      }
    }).as('getStatCounters');

    cy.visit(url)
      .wait('@getStatCounters')
      .wait(500)
      .get('.swh-counter')
      .then((counters) => {
        for (let counter of counters) {
          const value = parseInt($(counter).text());
          assert.equal(value, 0);
        }
      });
  });
});
