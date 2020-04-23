/**
 * Copyright (C) 2019-2020  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import {random, checkLanguageHighlighting} from '../utils';

const $ = Cypress.$;

let origin;

let contentWithLanguageInfo, contentWithoutLanguageInfo;
const languageSelect = 'python';

describe('Test Content Language Select', function() {
  before(function() {
    origin = this.origin[0];
    contentWithLanguageInfo = `${this.Urls.browse_origin_content()}?origin_url=${origin.url}&path=${origin.content[1].path}`;
    contentWithoutLanguageInfo = this.Urls.browse_content(`sha1_git:${origin.content[1].sha1git}`);
  });

  context('When Language is detected', function() {
    it('should display correct language in dropdown', function() {
      cy.visit(contentWithLanguageInfo)
        .then(() => {
          cy.get(`code.${$('.language-select').val()}`)
            .should('exist');
        });
    });
  });

  context('When Language is not detected', function() {
    it('should have no selected language in dropdown', function() {
      cy.visit(contentWithoutLanguageInfo).then(() => {
        assert.strictEqual($('.language-select').val(), null);
      });
    });
  });

  context('When language is switched from dropdown', function() {
    before(function() {
      cy.visit(contentWithLanguageInfo);

      cy.get('.chosen-container')
        .click()
        .get('.chosen-results > li')
        .its('length')
        .then(numOptions => {
          const languageIndex = random(0, numOptions);
          cy.get('.chosen-results > li')
            .eq(languageIndex)
            .click();
        });
    });

    it('should contain argument with language in url', function() {
      cy.location('search')
        .should('contain', `language=${$('.language-select').val()}`);
    });

    it('should highlight according to new language', function() {
      checkLanguageHighlighting($('.language-select').val());
    });
  });

  it('should highlight according to the language passed as argument in url', function() {
    cy.visit(`${contentWithLanguageInfo}&language=${languageSelect}`);
    checkLanguageHighlighting(languageSelect);
  });

});
