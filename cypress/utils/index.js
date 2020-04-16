/**
 * Copyright (C) 2019  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import axios from 'axios';

export async function httpGetJson(url) {
  const response = await axios.get(url);
  return response.data;
}

/**
 * Converts string with Time information
 * to an object with Time information
 */
export function getTime(text) {
  const date = new Date(text);

  function pad(n) {
    return n < 10 ? '0' + n : n;
  }

  const time = {
    date: date.getUTCDate(),
    month: date.getUTCMonth(),
    monthName: date.toLocaleString('en', {month: 'long'}),
    year: date.getUTCFullYear(),
    hours: pad(date.getUTCHours()),
    minutes: pad(date.getUTCMinutes())
  };

  return time;
}

export function checkLanguageHighlighting(language) {
  cy.get('code')
    .should('be.visible')
    .and('have.class', 'hljs')
    .and('have.class', language)
    .and('not.be.empty')
    .find('table.hljs-ln')
    .should('be.visible')
    .and('not.be.empty');
}

export function random(start, end) {
  const range = end - start;
  return Math.floor(Math.random() * range) + start;
}

export const describeSlowTests = Cypress.env('SKIP_SLOW_TESTS') === 1 ? describe.skip : describe;
