/**
 * Copyright (C) 2019-2020  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import {random} from '../utils';

const $ = Cypress.$;

let origin;
const lineStart = 32;
const lineEnd = 42;

let url;

describe('Code highlighting tests', function() {
  before(function() {
    origin = this.origin[0];
    url = `${this.Urls.browse_origin_content()}?origin_url=${origin.url}&path=${origin.content[0].path}`;
  });

  it('should highlight source code and add line numbers', function() {
    cy.visit(url);
    cy.get('.hljs-ln-numbers').then(lnNumbers => {
      cy.get('.hljs-ln-code')
        .should('have.length', lnNumbers.length);
    });
  });

  it('should emphasize source code lines based on url fragment', function() {
    cy.visit(`${url}/#L${lineStart}-L${lineEnd}`);
    cy.get('.hljs-ln-line').then(lines => {
      for (let line of lines) {
        const lineElt = $(line);
        const lineNumber = parseInt(lineElt.data('line-number'));
        if (lineNumber >= lineStart && lineNumber <= lineEnd) {
          assert.notEqual(lineElt.css('background-color'), 'rgba(0, 0, 0, 0)');
        } else {
          assert.equal(lineElt.css('background-color'), 'rgba(0, 0, 0, 0)');
        }
      }
    });
  });

  it('should emphasize a line by clicking on its number', function() {
    cy.visit(url);
    cy.get('.hljs-ln-numbers').then(lnNumbers => {
      const lnNumber = lnNumbers[random(0, lnNumbers.length)];
      const lnNumberElt = $(lnNumber);
      assert.equal(lnNumberElt.css('background-color'), 'rgba(0, 0, 0, 0)');
      const line = parseInt(lnNumberElt.data('line-number'));
      cy.get(`.hljs-ln-numbers[data-line-number="${line}"]`)
        .click()
        .then(() => {
          assert.notEqual(lnNumberElt.css('background-color'), 'rgba(0, 0, 0, 0)');
        });
    });
  });

  it('should emphasize a range of lines by clicking on two line numbers and holding shift', function() {
    cy.visit(url);

    cy.get(`.hljs-ln-numbers[data-line-number="${lineStart}"]`)
      .click()
      .get(`.hljs-ln-numbers[data-line-number="${lineEnd}"]`)
      .click({shiftKey: true})
      .get('.hljs-ln-line')
      .then(lines => {
        for (let line of lines) {
          const lineElt = $(line);
          const lineNumber = parseInt(lineElt.data('line-number'));
          if (lineNumber >= lineStart && lineNumber <= lineEnd) {
            assert.notEqual(lineElt.css('background-color'), 'rgba(0, 0, 0, 0)');
          } else {
            assert.equal(lineElt.css('background-color'), 'rgba(0, 0, 0, 0)');
          }
        }
      });
  });

  it('should remove emphasized lines when clicking anywhere in code', function() {
    cy.visit(`${url}/#L${lineStart}-L${lineEnd}`);

    cy.get(`.hljs-ln-code[data-line-number="1"]`)
      .click()
      .get('.hljs-ln-line')
      .should('have.css', 'background-color', 'rgba(0, 0, 0, 0)');
  });

});
