/**
 * Copyright (C) 2019  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

let origin;
let diffData;

describe('Test Diffs View', function() {
  before(function() {
    origin = this.origin[0];
    const url = this.Urls.browse_revision(origin.revisions[0]) + `?origin=${origin.url}`;

    cy.visit(url).window().then(win => {
      cy.request(win.diffRevUrl)
        .then(res => {
          diffData = res.body;
        });
    });
  });

  beforeEach(function() {
    const url = this.Urls.browse_revision(origin.revisions[0]) + `?origin=${origin.url}`;
    cy.visit(url);
    cy.get('a[data-toggle="tab"]')
      .contains('Changes')
      .click();
  });

  it('should list all files with changes', function() {
    let files = new Set([]);
    for (let change of diffData.changes) {
      files.add(change.from_path);
      files.add(change.to_path);
    }
    for (let file of files) {
      cy.get('#swh-revision-changes-list a')
        .contains(file)
        .should('be.visible');
    }
  });

  it('should load diffs when scrolled down', function() {
    cy.get('#swh-revision-changes-list a')
      .each($el => {
        cy.get($el.attr('href'))
          .scrollIntoView()
          .find('.swh-content')
          .should('be.visible');
      });
  });

  it('should compute all diffs when selected', function() {
    cy.get('#swh-compute-all-diffs')
      .click();
    cy.get('#swh-revision-changes-list a')
      .each($el => {
        cy.get($el.attr('href'))
          .find('.swh-content')
          .should('be.visible');
      });
  });

  it('should have correct links in diff file names', function() {
    for (let change of diffData.changes) {
      cy.get(`#swh-revision-changes-list a[href="#panel_${change.id}"`)
        .should('be.visible');
    }
  });

  it('should load unified diff by default', function() {
    cy.get('#swh-compute-all-diffs')
      .click();
    for (let change of diffData.changes) {
      cy.get(`#${change.id}-unified-diff`)
        .should('be.visible');
      cy.get(`#${change.id}-splitted-diff`)
        .should('not.be.visible');
    }
  });

  it('should switch between unified and side-by-side diff when selected', function() {
    // Test for first diff
    const id = diffData.changes[0].id;
    cy.get(`#panel_${id}`)
      .contains('label', 'Side-by-side')
      .click();
    cy.get(`#${id}-splitted-diff`)
      .should('be.visible')
      .get(`#${id}-unified-diff`)
      .should('not.be.visible');
  });
});
