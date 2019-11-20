/**
 * Copyright (C) 2019  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

let origin;
let url;
let browsedObjectMetadata;
let cntPid, cntPidWithOrigin, cntPidWithOriginAndLines;
let dirPid, dirPidWithOrigin;
let relPid, relPidWithOrigin;
let revPid, revPidWithOrigin;
let snpPid, snpPidWithOrigin;
const firstSelLine = 6;
const lastSelLine = 12;

describe('Persistent Identifiers Tests', function() {

  before(function() {
    origin = this.origin[1];
    url = this.Urls.browse_origin_content(origin.url, origin.content[0].path);
    url = `${url}?release=${origin.release}#L${firstSelLine}-L${lastSelLine}`;
  });

  beforeEach(function() {
    cy.visit(url).window().then(win => {
      browsedObjectMetadata = win.swh.webapp.getBrowsedSwhObjectMetadata();
      cntPid = `swh:1:cnt:${browsedObjectMetadata.sha1_git}`;
      cntPidWithOrigin = `${cntPid};origin=${origin.url}`;
      cntPidWithOriginAndLines = `${cntPidWithOrigin};lines=${firstSelLine}-${lastSelLine}`;
      dirPid = `swh:1:dir:${browsedObjectMetadata.directory}`;
      dirPidWithOrigin = `${dirPid};origin=${origin.url}`;
      revPid = `swh:1:rev:${browsedObjectMetadata.revision}`;
      revPidWithOrigin = `${revPid};origin=${origin.url}`;
      relPid = `swh:1:rel:${browsedObjectMetadata.release}`;
      relPidWithOrigin = `${relPid};origin=${origin.url}`;
      snpPid = `swh:1:snp:${browsedObjectMetadata.snapshot}`;
      snpPidWithOrigin = `${snpPid};origin=${origin.url}`;
    });
  });

  it('should open and close identifiers tab when clicking on handle', function() {
    cy.get('#swh-identifiers')
      .should('have.class', 'ui-slideouttab-ready');

    cy.get('.ui-slideouttab-handle')
      .click();

    cy.get('#swh-identifiers')
      .should('have.class', 'ui-slideouttab-open');

    cy.get('.ui-slideouttab-handle')
      .click();

    cy.get('#swh-identifiers')
      .should('not.have.class', 'ui-slideouttab-open');

  });

  it('should display identifiers with permalinks for browsed objects', function() {
    cy.get('.ui-slideouttab-handle')
      .click();

    const testData = [
      {
        'objectType': 'content',
        'objectPid': cntPidWithOriginAndLines
      },
      {
        'objectType': 'directory',
        'objectPid': dirPidWithOrigin
      },
      {
        'objectType': 'release',
        'objectPid': relPidWithOrigin
      },
      {
        'objectType': 'revision',
        'objectPid': revPidWithOrigin
      },
      {
        'objectType': 'snapshot',
        'objectPid': snpPidWithOrigin
      }
    ];

    for (let td of testData) {
      cy.get(`a[href="#swh-id-tab-${td.objectType}"]`)
        .click();

      cy.get(`#swh-id-tab-${td.objectType}`)
        .should('be.visible');

      cy.get(`#swh-id-tab-${td.objectType} .swh-id`)
        .contains(td.objectPid)
        .should('have.attr', 'href', this.Urls.browse_swh_id(td.objectPid));

    }

  });

  it('should update content identifier metadata when toggling option checkboxes', function() {
    cy.get('.ui-slideouttab-handle')
      .click();

    cy.get(`#swh-id-tab-content .swh-id`)
      .contains(cntPidWithOriginAndLines)
      .should('have.attr', 'href', this.Urls.browse_swh_id(cntPidWithOriginAndLines));

    cy.get('#swh-id-tab-content .swh-id-option-lines')
      .click();

    cy.get(`#swh-id-tab-content .swh-id`)
      .contains(cntPidWithOrigin)
      .should('have.attr', 'href', this.Urls.browse_swh_id(cntPidWithOrigin));

    cy.get('#swh-id-tab-content .swh-id-option-origin')
      .click();

    cy.get(`#swh-id-tab-content .swh-id`)
      .contains(cntPid)
      .should('have.attr', 'href', this.Urls.browse_swh_id(cntPid));

    cy.get('#swh-id-tab-content .swh-id-option-origin')
      .click();

    cy.get(`#swh-id-tab-content .swh-id`)
      .contains(cntPidWithOrigin)
      .should('have.attr', 'href', this.Urls.browse_swh_id(cntPidWithOrigin));

    cy.get('#swh-id-tab-content .swh-id-option-lines')
      .click();

    cy.get(`#swh-id-tab-content .swh-id`)
      .contains(cntPidWithOriginAndLines)
      .should('have.attr', 'href', this.Urls.browse_swh_id(cntPidWithOriginAndLines));

  });

  it('should update other object identifiers metadata when toggling option checkboxes', function() {
    cy.get('.ui-slideouttab-handle')
      .click();

    const testData = [
      {
        'objectType': 'directory',
        'objectPids': [dirPidWithOrigin, dirPid]
      },
      {
        'objectType': 'release',
        'objectPids': [relPidWithOrigin, relPid]
      },
      {
        'objectType': 'revision',
        'objectPids': [revPidWithOrigin, revPid]
      },
      {
        'objectType': 'snapshot',
        'objectPids': [snpPidWithOrigin, snpPid]
      }
    ];

    for (let td of testData) {
      cy.get(`a[href="#swh-id-tab-${td.objectType}"]`)
        .click();

      cy.get(`#swh-id-tab-${td.objectType} .swh-id`)
        .contains(td.objectPids[0])
        .should('have.attr', 'href', this.Urls.browse_swh_id(td.objectPids[0]));

      cy.get(`#swh-id-tab-${td.objectType} .swh-id-option-origin`)
        .click();

      cy.get(`#swh-id-tab-${td.objectType} .swh-id`)
        .contains(td.objectPids[1])
        .should('have.attr', 'href', this.Urls.browse_swh_id(td.objectPids[1]));

      cy.get(`#swh-id-tab-${td.objectType} .swh-id-option-origin`)
        .click();

      cy.get(`#swh-id-tab-${td.objectType} .swh-id`)
        .contains(td.objectPids[0])
        .should('have.attr', 'href', this.Urls.browse_swh_id(td.objectPids[0]));
    }

  });

});
