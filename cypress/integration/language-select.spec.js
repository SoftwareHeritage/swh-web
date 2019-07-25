/**
 * Copyright (C) 2019  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import {random, checkLanguageHighlighting} from '../utils';

const origin = {
  url: 'https://github.com/memononen/libtess2',
  content: {
    path: 'premake4.lua'
  }
};

let contentWithLanguageInfo, contentWithoutLanguageInfo;

let languages = [];

const $ = Cypress.$;

describe('Test Content Language Select', function() {
  before(function() {
    contentWithLanguageInfo = this.Urls.browse_origin_content(origin.url, origin.content.path);

    cy.visit(contentWithLanguageInfo);
    cy.window().then(win => {
      const metadata = win.swh.webapp.getBrowsedSwhObjectMetadata();

      origin.content.name = metadata.filename;
      origin.content.sha1git = metadata.sha1_git;
      contentWithoutLanguageInfo = this.Urls.browse_content(`sha1_git:${origin.content.sha1git}`);
      $('.language-select option').each(function() {
        languages.push(this.value);
      });
    });
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

      let languageSelect = languages[random(0, languages.length)];

      cy.get('.chosen-container')
        .click()
        .get('.chosen-results > li')
        .contains(languageSelect)
        .click()
        .then(() => {
          assert.strictEqual($('.language-select').val(), languageSelect);
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
    const languageSelect = languages[random(0, languages.length)];
    cy.visit(`${contentWithLanguageInfo}?language=${languageSelect}`);
    checkLanguageHighlighting(languageSelect);
  });

});
