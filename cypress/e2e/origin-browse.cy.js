/**
 * Copyright (C) 2020-2021  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

describe('Test origin browse', function() {
  beforeEach(function() {
    const url = `${this.Urls.browse_origin()}?origin_url=${this.origin[1].url}`;
    cy.visit(url);
  });

  it('should have code tab active by default', function() {
    cy.get('#swh-browse-code-nav-link')
      .should('have.class', 'active');
  });

  it('should load branches view when clicking on the Branches tab', function() {
    cy.get('#swh-browse-snapshot-branches-nav-link')
      .click();

    cy.location('pathname')
      .should('eq', this.Urls.browse_snapshot_branches(this.origin[1].snapshot));

    cy.location('search')
      .should('eq', `?origin_url=${this.origin[1].url}`);

    cy.get('#swh-browse-snapshot-branches-nav-link')
      .should('have.class', 'active');
  });

  it('should load releases view when clicking on the Releases tab', function() {
    cy.get('#swh-browse-snapshot-releases-nav-link')
      .click();

    cy.location('pathname')
      .should('eq', this.Urls.browse_snapshot_releases(this.origin[1].snapshot));

    cy.location('search')
      .should('eq', `?origin_url=${this.origin[1].url}`);

    cy.get('#swh-browse-snapshot-releases-nav-link')
      .should('have.class', 'active');
  });

  it('should load visits view when clicking on the Visits tab', function() {
    cy.get('#swh-browse-origin-visits-nav-link')
      .click();

    cy.location('pathname')
      .should('eq', this.Urls.browse_origin_visits());

    cy.location('search')
      .should('eq', `?origin_url=${this.origin[1].url}`);

    cy.get('#swh-browse-origin-visits-nav-link')
      .should('have.class', 'active');
  });

  it('should load code view when clicking on the Code tab', function() {
    cy.get('#swh-browse-origin-visits-nav-link')
      .click();

    cy.get('#swh-browse-code-nav-link')
      .click();

    cy.location('pathname')
      .should('eq', this.Urls.browse_origin_directory());

    cy.location('search')
      .should('eq', `?origin_url=${this.origin[1].url}`);

    cy.get('#swh-browse-code-nav-link')
      .should('have.class', 'active');

  });

  it('should have Releases tab link disabled when there is no releases', function() {
    const url = `${this.Urls.browse_origin()}?origin_url=${this.origin[0].url}`;
    cy.visit(url);

    cy.get('#swh-browse-snapshot-releases-nav-link')
      .should('have.class', 'disabled');
  });
});

describe('Test browse branches', function() {
  beforeEach(function() {
    const url = `${this.Urls.browse_origin_branches()}?origin_url=${this.origin[1].url}`;
    cy.visit(url);
  });

  it('should have the master branch in the list', function() {
    cy.get('table').contains('td', 'master').should('be.visible');
  });

  it('should search inside the branches', function() {
    cy.get('#swh-branch-search-string').type('mas');
    cy.get('#swh-branch-serach-button').click();

    cy.location('search')
      .should('include', 'name_include=mas');

    cy.get('table').contains('td', 'master').should('be.visible');

    cy.get('#swh-branch-search-string').should('have.value', 'mas');
  });

  it('should show all the branches for empty search', function() {
    cy.get('#swh-branch-search-string').clear();
    cy.get('#swh-branch-serach-button').click();

    cy.location('search')
      .should('include', 'name_include=');

    cy.get('table').contains('td', 'master').should('be.visible');

    cy.get('#swh-branch-search-string').should('have.value', '');
  });

  it('should show no branch exists message on failed search', function() {
    cy.get('#swh-branch-search-string').type('random{enter}');

    cy.get('table').contains('td', 'No branch names containing random have been found!').should('be.visible');
  });
});

describe('Test browse releases', function() {
  beforeEach(function() {
    const url = `${this.Urls.browse_origin_releases()}?origin_url=${this.origin[1].url}`;
    cy.visit(url);
  });

  it('should have the v2 release in the list', function() {
    cy.get('table').contains('td', 'v2.0').should('be.visible');
  });

  it('should search inside the releases', function() {
    cy.get('#swh-branch-search-string').type('v2.4');
    cy.get('#swh-branch-serach-button').click();

    cy.location('search')
      .should('include', 'name_include=v2.4');

    cy.get('table').contains('td', 'v2.4').should('be.visible');

    cy.get('#swh-branch-search-string').should('have.value', 'v2.4');
  });

  it('should show all the releases for empty search', function() {
    cy.get('#swh-branch-search-string').clear();
    cy.get('#swh-branch-serach-button').click();

    cy.location('search')
      .should('include', 'name_include=');

    cy.get('table').contains('td', 'v2.0').should('be.visible');

    cy.get('#swh-branch-search-string').should('have.value', '');
  });

  it('should show no release exists message on failed search', function() {
    cy.get('#swh-branch-search-string').type('random{enter}');

    cy.get('table').contains('td', 'No release names containing random have been found!').should('be.visible');
  });
});
