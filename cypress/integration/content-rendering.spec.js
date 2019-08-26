/**
 * Copyright (C) 2019  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import {checkLanguageHighlighting, describeSlowTests} from '../utils';

describeSlowTests('Code highlighting tests', function() {

  const extensions = require('../fixtures/source-file-extensions.json');

  extensions.forEach(ext => {
    it(`should highlight source files with extension ${ext}`, function() {
      cy.request(this.Urls.tests_content_code_extension(ext)).then(response => {
        const data = response.body;
        cy.visit(`${this.Urls.browse_content(data.sha1)}?path=file.${ext}`);
        checkLanguageHighlighting(data.language);
      });
    });
  });

  const filenames = require('../fixtures/source-file-names.json');

  filenames.forEach(filename => {
    it(`should highlight source files with filenames ${filename}`, function() {
      cy.request(this.Urls.tests_content_code_filename(filename)).then(response => {
        const data = response.body;
        cy.visit(`${this.Urls.browse_content(data.sha1)}?path=${filename}`);
        checkLanguageHighlighting(data.language);
      });
    });
  });

});

describe('Image rendering tests', function() {
  const imgExtensions = ['gif', 'jpeg', 'png', 'webp'];

  imgExtensions.forEach(ext => {
    it(`should render image with extension ${ext}`, function() {
      cy.request(this.Urls.tests_content_other_extension(ext)).then(response => {
        const data = response.body;
        cy.visit(`${this.Urls.browse_content(data.sha1)}?path=file.${ext}`);
        cy.get('.swh-content img')
          .should('be.visible');
      });
    });
  });

});

describe('PDF rendering test', function() {

  function sum(previousValue, currentValue) {
    return previousValue + currentValue;
  }

  it(`should render a PDF file`, function() {
    cy.request(this.Urls.tests_content_other_extension('pdf')).then(response => {
      const data = response.body;
      cy.visit(`${this.Urls.browse_content(data.sha1)}?path=file.pdf`);
      cy.get('.swh-content canvas')
        .wait(2000)
        .then(canvas => {
          let width = canvas[0].width;
          let height = canvas[0].height;
          let context = canvas[0].getContext('2d');
          let imgData = context.getImageData(0, 0, width, height);
          assert.notEqual(imgData.data.reduce(sum), 0);
        });
    });
  });

});

describe('Jupyter notebook rendering test', function() {

  it(`should render a notebook file to HTML`, function() {
    cy.request(this.Urls.tests_content_other_extension('ipynb')).then(response => {
      const data = response.body;
      cy.visit(`${this.Urls.browse_content(data.sha1)}?path=file.ipynb`);
      cy.get('.nb-notebook')
        .should('be.visible')
        .and('not.be.empty');
      cy.get('.nb-cell.nb-markdown-cell')
        .should('be.visible')
        .and('not.be.empty');
      cy.get('.nb-cell.nb-code-cell')
        .should('be.visible')
        .and('not.be.empty');
      cy.get('.MathJax')
        .should('be.visible')
        .and('not.be.empty');
    });
  });

});
