/**
 * Copyright (C) 2019  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

const origin = 'https://github.com/memononen/libtess2';
const contentPath = 'Source/tess.h';
const lineStart = 32;
const lineEnd = 42;

const $ = Cypress.$;

let url;

describe('Code highlighting tests', function() {

  before(function() {
    cy.visit('/').window().then(win => {
      url = win.Urls.browse_origin_content(origin, contentPath);
    });
  });

  it('should highlight source code and add line numbers', function() {
    cy.visit(url);
    cy.get('.hljs-ln-numbers').then(lnNumbers => {
      cy.get('.hljs-ln-code').then(lnCode => {
        assert.equal(lnNumbers.length, lnCode.length);
      });
    });
  });

  it('should emphasize source code lines based on url fragment', function() {

    cy.visit(`${url}/#L${lineStart}-L${lineEnd}`);
    cy.get('.hljs-ln-line').then(lines => {
      for (let line of lines) {
        let lineNumber = parseInt($(line).data('line-number'));
        if (lineNumber >= lineStart && lineNumber <= lineEnd) {
          assert.notEqual($(line).css('background-color'), 'rgba(0, 0, 0, 0)');
        } else {
          assert.equal($(line).css('background-color'), 'rgba(0, 0, 0, 0)');
        }
      }
    });
  });

  it('should emphasize a line by clicking on its number', function() {
    cy.visit(url);
    cy.get('.hljs-ln-numbers').then(lnNumbers => {
      let lnNumber = lnNumbers[Math.floor(Math.random() * lnNumbers.length)];
      assert.equal($(lnNumber).css('background-color'), 'rgba(0, 0, 0, 0)');
      let line = parseInt($(lnNumber).data('line-number'));
      cy.get(`.hljs-ln-numbers[data-line-number="${line}"]`)
        .scrollIntoView()
        .click()
        .then(() => {
          assert.notEqual($(lnNumber).css('background-color'), 'rgba(0, 0, 0, 0)');
        });
    });
  });

  it('should emphasize a range of lines by clicking on two line numbers and holding shift', function() {
    cy.visit(url);

    cy.get(`.hljs-ln-numbers[data-line-number="${lineStart}"]`)
      .scrollIntoView()
      .click()
      .get(`body`)
      .type(`{shift}`, { release: false })
      .get(`.hljs-ln-numbers[data-line-number="${lineEnd}"]`)
      .scrollIntoView()
      .click()
      .get('.hljs-ln-line')
      .then(lines => {
        for (let line of lines) {
          let lineNumber = parseInt($(line).data('line-number'));
          if (lineNumber >= lineStart && lineNumber <= lineEnd) {
            assert.notEqual($(line).css('background-color'), 'rgba(0, 0, 0, 0)');
          } else {
            assert.equal($(line).css('background-color'), 'rgba(0, 0, 0, 0)');
          }
        }
      });
  });

  it('should remove emphasized lines when clicking anywhere in code', function() {
    cy.visit(`${url}/#L${lineStart}-L${lineEnd}`);

    cy.get(`.hljs-ln-code[data-line-number="1"]`)
      .scrollIntoView()
      .click()
      .get('.hljs-ln-line')
      .then(lines => {
        for (let line of lines) {
          assert.equal($(line).css('background-color'), 'rgba(0, 0, 0, 0)');
        }
      });
  });

});
