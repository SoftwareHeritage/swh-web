/**
 * Copyright (C) 2019-2020  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import {getTime} from '../utils';

let origin;

function checkTimeLink(element) {
  expect(element.text()).not.to.be.empty;

  const urlParams = new URLSearchParams(element.attr('href').split('?')[1]);

  const timeStringLink = urlParams.get('timestamp');

  // time in link should be equal to that in text
  assert.deepEqual(getTime(timeStringLink), getTime(element.text()));
}

function searchInCalendar(date) {
  cy.contains('label', 'Show all visits')
    .click();
  cy.get(`.year${date.year}`)
    .click({force: true});
  cy.contains('.month', date.monthName)
    .find('.day-content')
    .eq(date.date - 1)
    .trigger('mouseenter')
    .get('.popover-body')
    .should('be.visible')
    .and('contain', `${date.hours}:${date.minutes} UTC`);
}

describe('Visits tests', function() {
  before(function() {
    origin = this.origin[1];
  });

  beforeEach(function() {
    cy.visit(`${this.Urls.browse_origin_visits()}?origin_url=${origin.url}`);
  });

  it('should display first full visit time', function() {
    cy.get('#swh-first-full-visit > .swh-visit-full')
      .then(($el) => {
        checkTimeLink($el);
        searchInCalendar(getTime($el.text()));
      });
  });

  it('should display last full visit time', function() {
    cy.get('#swh-last-full-visit > .swh-visit-full')
      .then(($el) => {
        checkTimeLink($el);
        searchInCalendar(getTime($el.text()));
      });
  });

  it('should display last visit time', function() {
    cy.get('#swh-last-visit > .swh-visit-full')
      .then(($el) => {
        checkTimeLink($el);
        searchInCalendar(getTime($el.text()));
      });
  });

  it('should display list of visits and mark them on calendar', function() {
    cy.get('.swh-visits-list-row .swh-visit-full')
      .should('be.visible')
      .each(($el) => {
        checkTimeLink($el);
        searchInCalendar(getTime($el.text()));
      });
  });

  it('should close calendar popover when leaving day', function() {
    cy.get('#swh-last-visit > .swh-visit-full')
      .then(($el) => {
        const date = getTime($el.text());
        searchInCalendar(date);
        cy.contains('.month', date.monthName)
          .find('.day-content')
          .eq(date.date - 1)
          .trigger('mouseout', {force: true});

        cy.get('.popover')
          .should('not.exist');
      });
  });

});
