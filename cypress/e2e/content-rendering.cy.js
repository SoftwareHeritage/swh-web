/**
 * Copyright (C) 2019-2025  The Software Heritage developers
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

describe('HTML rendering tests', function() {
  beforeEach(function() {
    cy.fixture('swh-logo', 'base64').as('swhLogoBase64');
  });

  function checkHtmlRendering(Urls, originUrl, html, logo, css = '') {
    const contents = [{'path': 'index.html', 'data': html},
                      {'path': 'img/swh-logo.png', 'data': `base64:${logo}`},
                      {'path': 'css/style.css', 'data': css}];

    cy.request('POST',
               `${Urls.tests_add_origin_with_contents()}?origin_url=${originUrl}`,
               contents)
      .then((resp) => {
        expect(resp.status).to.eq(200);
        const url = `${Urls.browse_origin_directory()}?origin_url=${originUrl}&path=index.html`;
        if (css) {
          cy.intercept(/.*\/browse\/directory\/content\/.*\/path\/css\/style.css/)
            .as('loadCssFile');
        }
        cy.intercept(/.*\/browse\/directory\/content\/.*\/path\/img\/swh-logo.png/)
          .as('loadSwhLogo');
        cy.visit(url);

        // code view by default
        cy.get('#code-switch')
          .should('be.checked');
        cy.get('#preview-switch')
          .should('not.be.checked');
        cy.url().should('not.include', 'show_preview=true');
        cy.get('.highlightjs').should('be.visible');
        cy.get('.swh-preview-content').should('not.be.visible');

        // request html preview
        cy.get('#preview-switch-label')
          .click();

        if (css) {
          // check loading of CSS file from the archive
          cy.wait('@loadCssFile')
            .its('response.statusCode')
            .should('eq', 200);
        }

        // check loading of image file from the archive
        cy.wait('@loadSwhLogo')
          .its('response.statusCode')
          .should('eq', 200);

        // check HTML content was fully loaded
        cy.frameLoaded('.swh-html-content');

        // all script tags should have been removed except those injected by SWH
        cy.iframe('.swh-html-content')
          .find('script')
          .should('have.length', 3)
          .and('have.class', 'swh-iframe-script');

        // check CSS have been successfully applied
        cy.iframe('.swh-html-content')
          .find('#swh-title')
          .should('have.css', 'color', 'rgb(255, 0, 0)');
        cy.iframe('.swh-html-content')
          .find('#swh-logo')
          .should('have.css', 'width', '100px');

        // check UI state
        cy.get('#code-switch')
          .should('not.be.checked');
        cy.get('#preview-switch')
          .should('be.checked');
        cy.url().should('include', 'show_preview=true');
        cy.get('.highlightjs').should('not.be.visible');
        cy.get('.swh-preview-content').should('be.visible');
      });
  }

  it(`should render an HTML page with inline style and image`, function() {

    const indexHtml = `
<html>
  <head>
    <script src="js/app.js">
    <script>
      alert(1);
    </script>
    <style>
      #swh-title {
        color: red;
      }
      #swh-logo {
        width: 100px;
        height: 100px;
      }
    </style>
  </head>
  <body>
    <h1 id="swh-title">Software Heritage logo</h1>
    <img id="swh-logo" src="img/swh-logo.png" />
  </body>
</html>
`;

    const originUrl = 'https://git.example.org/html-page';
    checkHtmlRendering(this.Urls, originUrl, indexHtml, this.swhLogoBase64);
  });

  it(`should render an HTML page with inline style and background image`, function() {

    const indexHtml = `
<html>
  <head>
    <script src="js/app.js">
    <script>
      alert(1);
    </script>
    <style>
      #swh-title {
        color: red;
      }
      #swh-logo {
        background-image: url("img/swh-logo.png");
        background-size: cover;
        background-repeat: no-repeat;
        background-position: center center;
        width: 100px;
        height: 100px;
      }
    </style>
  </head>
  <body>
    <h1 id="swh-title">Software Heritage logo</h1>
    <div id="swh-logo"></div>
  </body>
</html>
`;

    const originUrl = 'https://git.example.org/html-page-backround-image';
    checkHtmlRendering(this.Urls, originUrl, indexHtml, this.swhLogoBase64);
  });

  it(`should render an HTML page with style in CSS file and background image`, function() {

    const styleCss = `
#swh-title {
  color: red;
}
#swh-logo {
  background-image: url("../img/swh-logo.png");
  background-size: cover;
  background-repeat: no-repeat;
  background-position: center center;
  width: 100px;
  height: 100px;
}`;

    const indexHtml = `
<html>
  <head>
    <script src="js/app.js">
    <script>
      alert(1);
    </script>
    <link rel="stylesheet" type="text/css" href="css/style.css">
  </head>
  <body>
    <h1 id="swh-title">Software Heritage logo</h1>
    <div id="swh-logo"></div>
  </body>
</html>
`;

    const originUrl = 'https://git.example.org/html-page-css-file-backround-image';
    checkHtmlRendering(this.Urls, originUrl, indexHtml, this.swhLogoBase64, styleCss);
  });

});

describe('Image rendering tests', function() {
  const imgExtensions = ['gif', 'jpeg', 'png', 'webp'];

  imgExtensions.forEach(ext => {
    it(`should render image with extension ${ext}`, function() {
      cy.request(this.Urls.tests_content_other_extension(ext)).then(response => {
        const data = response.body;
        cy.visit(`${this.Urls.browse_content(data.sha1)}`);
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
      cy.visit(`${this.Urls.browse_content(data.sha1)}`);
      cy.get('.swh-content canvas')
        .wait(2000)
        .then(canvas => {
          const width = canvas[0].width;
          const height = canvas[0].height;
          const context = canvas[0].getContext('2d');
          const imgData = context.getImageData(0, 0, width, height);
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

describe('Markdown rendering tests', function() {
  it(`should render a markdown file with math`, function() {

    const markdown = `
# This is a matrix

\\begin{pmatrix}
  0 & 1 \\\\\\
  1 & 0
\\end{pmatrix}
`;

    const originUrl = 'https://git.example.org/markdown-math';
    cy.request('POST',
               `${this.Urls.tests_add_origin_with_contents()}?origin_url=${originUrl}`,
               [{path: 'math.md', data: markdown}])
      .then((resp) => {
        expect(resp.status).to.eq(200);
        const url = `${this.Urls.browse_origin_directory()}?origin_url=${originUrl}&path=math.md`;

        cy.intercept(/.*static\/js\/mathjax-library.*/)
          .as('loadMathjax');

        cy.visit(url);
        // request html preview
        cy.get('#preview-switch-label')
          .click();
        cy.wait('@loadMathjax');
        // check markdown rendering
        cy.iframe('.swh-html-content')
          .find('h1')
          .should('have.text', 'This is a matrix');
        // check math rendering
        cy.iframe('.swh-html-content')
          .find('mjx-math')
          .should('be.visible')
          .and('not.be.empty');
      });
  });
});
