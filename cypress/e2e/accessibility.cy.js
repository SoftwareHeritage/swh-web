/**
 * Copyright (C) 2023  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

const pagesToCheck = [
  {name: 'homepage', path: '/'},
  {name: 'coverage', path: '/coverage/'},
  {name: 'browse origin directory', path: '/browse/origin/directory/?origin_url=https://github.com/memononen/libtess2'},
  {name: 'browse origin content', path: '/browse/content/sha1_git:32a56bf4060402c477271380880ef01ba36ea5b1/?origin_url=https://github.com/memononen/libtess2&path=Source/sweep.c'}
];

describe('Accessibility compliance tests', function() {

  beforeEach(function() {
    cy.intercept('/coverage', (req) => {
      // override the previously-declared stub to just continue the request instead of stubbing
      req.continue();
    });
  });

  pagesToCheck.forEach(page => {
    it(`should pass IBM accessibility checks on page '${page.name}'`, function() {
      cy.visit(page.path);
      const label = page.name.replaceAll(' ', '_');
      cy.getCompliance(label).then(report => {
        const nbViolations = report.summary.counts.violation;
        let errMsg = '';
        for (const result of report.results) {
          if (result.level === 'violation') {
            errMsg += `\n- Message: ${result.message}
  XPath: ${result.path.dom}
  Snippet: ${result.snippet}
  Help: ${result.help}\n`;
          }
        }
        expect(nbViolations, errMsg).to.eq(0);
      });
    });

    it(`should pass Axe accessibility checks on page '${page.name}'`, function() {
      cy.visit(page.path);
      cy.injectAxe();
      cy.checkA11y(null, {includedImpacts: ['serious', 'critical']});
    });

  });

  it('should materialize skip navigation link when getting focused', function() {
    // homepage set focus on search input by default so we use another page for this test
    cy.visit('/save');
    // skip link not visible by default
    cy.get('.skipnav a').should('have.css', 'left', '-10000px');
    // skip link should be visible when it gains keyboard focus
    cy.get('.skipnav a').focus();
    cy.get('.skipnav a').should('have.css', 'left', '5px');
    // skip link should be no longer visible when it loses keyboard focus
    cy.get('.skipnav a').blur();
    cy.get('.skipnav a').should('have.css', 'left', '-10000px');
  });

});
