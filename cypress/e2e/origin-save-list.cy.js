/**
 * Copyright (C) 2026  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

let url;

const search = 'maphys';

describe('Origin Save List Tests', function() {

  before(function() {
    url = this.Urls.origin_save_list();
  });

  beforeEach(function() {
    cy.fixture('origin-save').as('fullJSON').then(() => {
      const searchedJSON = {...this.fullJSON};
      searchedJSON.data = searchedJSON.data.filter(o => o.origin_url.includes(search));
      cy.wrap(searchedJSON).as('searchedJSON');
    });
  });

  it('should use URL parameter in search', function() {
    cy.intercept('/save/requests/list/**', this.searchedJSON).as('saveRequestsList');

    cy.visit(url, {qs: {search: search}});

    cy.wait('@saveRequestsList');

    cy.get('tbody tr').should('have.length', this.searchedJSON.data.length);

    cy.get('#dt-search-0').should('have.value', search);

    cy.get('table').should((el) => {
      expect(el.DataTable().search()).to.eq(search);
    });

  });

  it('should store search to URL parameter and restore on back button', function() {

    cy.intercept('/save/requests/list/**', this.fullJSON)
      .as('saveRequestsList');

    cy.visit(url);

    cy.wait('@saveRequestsList');

    cy.get('tbody tr').should('have.length', this.fullJSON.data.length);

    cy.location('search').should('be.empty');

    cy.get('table').should((el) => {
      expect(el.DataTable().search()).to.be.empty;
    });

    const searchResponse = {...this.searchedJSON, draw: 2};

    cy.intercept('/save/requests/list/**', searchResponse).as('saveRequestsList');

    cy.get('#dt-search-0').type(search);

    cy.wait('@saveRequestsList');

    cy.get('tbody tr').should('have.length', searchResponse.data.length);

    cy.url().should((url) => {
      expect((new URL(url)).searchParams.get('search')).to.eq(search);
    });

    cy.get('table').should((el) => {
      expect(el.DataTable().search()).to.eq(search);
    });

    const fullResponse = {...this.fullJSON, draw: 3};

    cy.intercept('/save/requests/list/**', fullResponse).as('saveRequestsList');

    cy.go('back');

    cy.wait('@saveRequestsList');

    cy.get('tbody tr').should('have.length', fullResponse.data.length);

    cy.location('search').should('be.empty');

    cy.get('table').should((el) => {
      expect(el.DataTable().search()).to.be.empty;
    });

  });

});
