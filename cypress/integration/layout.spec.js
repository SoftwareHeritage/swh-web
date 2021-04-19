/**
 * Copyright (C) 2019-2021  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

const url = '/browse/help/';
const statusUrl = 'https://status.softwareheritage.org';

describe('Test top-bar', function() {
  beforeEach(function() {
    cy.clearLocalStorage();
    cy.visit(url);
  });
  it('should should contain all navigation links', function() {
    cy.get('.swh-top-bar a')
      .should('have.length.of.at.least', 4)
      .and('be.visible')
      .and('have.attr', 'href');
  });

  it('should show donate button on lg screen', function() {
    cy.get('.swh-donate-link')
      .should('be.visible');
  });
  it('should hide donate button on sm screen', function() {
    cy.viewport(600, 800);
    cy.get('.swh-donate-link')
      .should('not.be.visible');
  });
  it('should hide full width switch on small screens', function() {
    cy.viewport(360, 740);
    cy.get('#swh-full-width-switch-container')
      .should('not.be.visible');

    cy.viewport(600, 800);
    cy.get('#swh-full-width-switch-container')
      .should('not.be.visible');

    cy.viewport(800, 600);
    cy.get('#swh-full-width-switch-container')
      .should('not.be.visible');
  });
  it('should show full width switch on large screens', function() {
    cy.viewport(1024, 768);
    cy.get('#swh-full-width-switch-container')
      .should('be.visible');

    cy.viewport(1920, 1080);
    cy.get('#swh-full-width-switch-container')
      .should('be.visible');
  });
  it('should change container width when toggling Full width switch', function() {
    cy.get('#swh-web-content')
      .should('have.class', 'container')
      .should('not.have.class', 'container-fluid');

    cy.should(() => {
      expect(JSON.parse(localStorage.getItem('swh-web-full-width'))).to.be.null;
    });

    cy.get('#swh-full-width-switch')
      .click({force: true});

    cy.get('#swh-web-content')
      .should('not.have.class', 'container')
      .should('have.class', 'container-fluid');

    cy.should(() => {
      expect(JSON.parse(localStorage.getItem('swh-web-full-width'))).to.be.true;
    });

    cy.get('#swh-full-width-switch')
      .click({force: true});

    cy.get('#swh-web-content')
      .should('have.class', 'container')
      .should('not.have.class', 'container-fluid');

    cy.should(() => {
      expect(JSON.parse(localStorage.getItem('swh-web-full-width'))).to.be.false;
    });
  });
  it('should restore container width when loading page again', function() {
    cy.visit(url)
      .get('#swh-web-content')
      .should('have.class', 'container')
      .should('not.have.class', 'container-fluid');

    cy.get('#swh-full-width-switch')
      .click({force: true});

    cy.visit(url)
      .get('#swh-web-content')
      .should('not.have.class', 'container')
      .should('have.class', 'container-fluid');

    cy.get('#swh-full-width-switch')
      .click({force: true});

    cy.visit(url)
      .get('#swh-web-content')
      .should('have.class', 'container')
      .should('not.have.class', 'container-fluid');
  });

  function genStatusResponse(status, statusCode) {
    return {
      'result': {
        'status': [
          {
            'id': '5f7c4c567f50b304c1e7bd5f',
            'name': 'Save Code Now',
            'updated': '2020-11-30T13:51:21.151Z',
            'status': 'Operational',
            'status_code': 100
          },
          {
            'id': '5f7c4c6f8338bc04b7f476fe',
            'name': 'Source Code Crawlers',
            'updated': '2020-11-30T13:51:21.151Z',
            'status': status,
            'status_code': statusCode
          }
        ]
      }
    };
  }

  it('should display swh status widget when data are available', function() {
    const statusTestData = [
      {
        status: 'Operational',
        statusCode: 100,
        color: 'green'
      },
      {
        status: 'Scheduled Maintenance',
        statusCode: 200,
        color: 'blue'
      },
      {
        status: 'Degraded Performance',
        statusCode: 300,
        color: 'yellow'
      },
      {
        status: 'Partial Service Disruption',
        statusCode: 400,
        color: 'yellow'
      },
      {
        status: 'Service Disruption',
        statusCode: 500,
        color: 'red'
      },
      {
        status: 'Security Event',
        statusCode: 600,
        color: 'red'
      }
    ];

    const responses = [];
    for (let std of statusTestData) {
      responses.push(genStatusResponse(std.status, std.statusCode));
    }

    let i = 0;
    for (let std of statusTestData) {
      cy.visit(url);
      // trick to override the response of an intercepted request
      // https://github.com/cypress-io/cypress/issues/9302
      cy.intercept(`${statusUrl}/**`, req => req.reply(responses.shift()))
        .as(`getSwhStatusData${i}`);
      cy.wait(`@getSwhStatusData${i}`);
      cy.get('.swh-current-status-indicator').should('have.class', std.color);
      cy.get('#swh-current-status-description').should('have.text', std.status);
      ++i;
    }
  });

  it('should not display swh status widget when data are not available', function() {
    cy.intercept(`${statusUrl}/**`, {
      body: {}
    }).as('getSwhStatusData');
    cy.visit(url);
    cy.wait('@getSwhStatusData');
    cy.get('.swh-current-status').should('not.exist');
  });

});

describe('Test navbar', function() {
  it('should redirect to search page when submitting search form in navbar', function() {
    const keyword = 'python';
    cy.get('#swh-origins-search-top-input')
      .type(keyword);

    cy.get('.swh-search-navbar')
      .submit();

    cy.url()
      .should('include', `${this.Urls.browse_search()}?q=${keyword}`);
  });
});

describe('Test footer', function() {
  beforeEach(function() {
    cy.visit(url);
  });

  it('should be visible', function() {
    cy.get('footer')
      .should('be.visible');
  });

  it('should have correct copyright years', function() {
    const currentYear = new Date().getFullYear();
    const copyrightText = '(C) 2015–' + currentYear.toString();
    cy.get('footer')
      .should('contain', copyrightText);
  });

  it('should contain link to Web API', function() {
    cy.get('footer')
      .get(`a[href="${this.Urls.api_1_homepage()}"]`)
      .should('contain', 'Web API');
  });
});
