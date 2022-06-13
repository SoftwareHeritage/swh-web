/**
 * Copyright (C) 2021  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

describe('Guided Tour Tests', function() {

  // utility function to traverse all guided tour steps in a page
  const clickNextStepButtons = (stopAtTitle = null) => {
    cy.get('.introjs-nextbutton').then($button => {
      const buttonText = $button.text();
      const headerText = $button.parent().siblings('.introjs-tooltip-header').text();
      if (buttonText === 'Next' && headerText.slice(0, -1) !== stopAtTitle) {
        cy.get('.introjs-nextbutton')
          .click({force: true})
          .then(() => {
            cy.get('.introjs-tooltip').should('be.visible');
            clickNextStepButtons(stopAtTitle);
          });
      }
    });
  };

  it('should start UI guided tour when clicking on help button', function() {
    cy.visit('/');
    cy.get('.swh-help-link')
      .click();

    cy.get('.introjs-tooltip')
      .should('exist');
  });

  it('should change guided tour page after current page steps', function() {
    cy.visit('/');

    cy.get('.swh-help-link')
      .click();

    cy.url().then(url => {
      clickNextStepButtons();
      cy.get('.introjs-nextbutton')
        .should('have.text', 'Next page')
        .click();
      cy.url().should('not.eq', url);
    });

  });

  it('should automatically open SWHIDs tab on second page of the guided tour', function() {
    const guidedTourPageIndex = 1;
    cy.visit('/').window().then(win => {
      const guidedTour = win.swh.guided_tour.getGuidedTour();
      // jump to third guided tour page
      cy.visit(guidedTour[guidedTourPageIndex].url);
      cy.window().then(win => {
        // SWHIDs tab should be closed when tour begins
        cy.get('.ui-slideouttab-open').should('not.exist');
        // init guided tour on the page
        win.swh.guided_tour.initGuidedTour(guidedTourPageIndex);
        clickNextStepButtons();
        // SWHIDs tab should be opened when tour begins
        cy.get('.ui-slideouttab-open').should('exist');
      });
    });
  });

  it('should stay at step while line numbers not clicked on content view tour', function() {
    const guidedTourPageIndex = 2;
    // jump to third guided tour page
    cy.visit('/').window().then(win => {
      const guidedTour = win.swh.guided_tour.getGuidedTour();
      cy.visit(guidedTour[guidedTourPageIndex].url);
      cy.window().then(win => {
        // init guided tour on the page
        win.swh.guided_tour.initGuidedTour(guidedTourPageIndex);

        clickNextStepButtons('Highlight a source code line');

        cy.get('.introjs-tooltip-header').then($header => {
          const headerText = $header.text();
          // user did not click yet on line numbers and should stay
          // blocked on first step of the tour
          cy.get('.introjs-nextbutton')
            .click();
          cy.get('.introjs-tooltip-header')
            .should('have.text', headerText);
          // click on line numbers
          cy.get('.hljs-ln-numbers[data-line-number="11"]')
            .click();
          // check move to next step is allowed
          cy.get('.introjs-nextbutton')
            .click();
          cy.get('.introjs-tooltip-header')
            .should('not.have.text', headerText);
        });

        cy.get('.introjs-tooltip-header').then($header => {
          const headerText = $header.text();
          // user did not click yet on line numbers and should stay
          // blocked on first step of the tour
          cy.get('.introjs-nextbutton')
            .click();
          cy.get('.introjs-tooltip-header')
            .should('have.text', headerText);
          // click on line numbers
          cy.get('.hljs-ln-numbers[data-line-number="17"]')
            .click({shiftKey: true});
          // check move to next step is allowed
          cy.get('.introjs-nextbutton')
            .click();
          cy.get('.introjs-tooltip-header')
            .should('not.have.text', headerText);
        });
      });
    });
  });
});
