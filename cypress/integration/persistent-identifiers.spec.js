/**
 * Copyright (C) 2019-2020  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

let origin, originBadgeUrl, originBrowseUrl;
let url, urlPrefix;
let cntSWHID, cntSWHIDWithContext;
let dirSWHID, dirSWHIDWithContext;
let relSWHID, relSWHIDWithContext;
let revSWHID, revSWHIDWithContext;
let snpSWHID, snpSWHIDWithContext;
let testsData;
const firstSelLine = 6;
const lastSelLine = 12;

describe('Persistent Identifiers Tests', function() {

  before(function() {
    origin = this.origin[1];
    url = `${this.Urls.browse_origin_content()}?origin_url=${origin.url}&path=${origin.content[0].path}`;
    url = `${url}&release=${origin.release}#L${firstSelLine}-L${lastSelLine}`;
    originBadgeUrl = this.Urls.swh_badge('origin', origin.url);
    originBrowseUrl = `${this.Urls.browse_origin()}?origin_url=${origin.url}`;
    cy.visit(url).window().then(win => {
      urlPrefix = `${win.location.protocol}//${win.location.hostname}`;
      if (win.location.port) {
        urlPrefix += `:${win.location.port}`;
      }
      const swhids = win.swh.webapp.getSwhIdsContext();
      cntSWHID = swhids.content.swhid;
      cntSWHIDWithContext = swhids.content.swhid_with_context;
      cntSWHIDWithContext += `;lines=${firstSelLine}-${lastSelLine}`;
      dirSWHID = swhids.directory.swhid;
      dirSWHIDWithContext = swhids.directory.swhid_with_context;
      revSWHID = swhids.revision.swhid;
      revSWHIDWithContext = swhids.revision.swhid_with_context;
      relSWHID = swhids.release.swhid;
      relSWHIDWithContext = swhids.release.swhid_with_context;
      snpSWHID = swhids.snapshot.swhid;
      snpSWHIDWithContext = swhids.snapshot.swhid_with_context;

      testsData = [
        {
          'objectType': 'content',
          'objectPids': [cntSWHIDWithContext, cntSWHID],
          'badgeUrl': this.Urls.swh_badge('content', swhids.content.object_id),
          'badgePidUrl': this.Urls.swh_badge_pid(cntSWHID),
          'browseUrl': this.Urls.browse_swh_id(cntSWHIDWithContext)
        },
        {
          'objectType': 'directory',
          'objectPids': [dirSWHIDWithContext, dirSWHID],
          'badgeUrl': this.Urls.swh_badge('directory', swhids.directory.object_id),
          'badgePidUrl': this.Urls.swh_badge_pid(dirSWHID),
          'browseUrl': this.Urls.browse_swh_id(dirSWHIDWithContext)
        },
        {
          'objectType': 'release',
          'objectPids': [relSWHIDWithContext, relSWHID],
          'badgeUrl': this.Urls.swh_badge('release', swhids.release.object_id),
          'badgePidUrl': this.Urls.swh_badge_pid(relSWHID),
          'browseUrl': this.Urls.browse_swh_id(relSWHIDWithContext)
        },
        {
          'objectType': 'revision',
          'objectPids': [revSWHIDWithContext, revSWHID],
          'badgeUrl': this.Urls.swh_badge('revision', swhids.revision.object_id),
          'badgePidUrl': this.Urls.swh_badge_pid(revSWHID),
          'browseUrl': this.Urls.browse_swh_id(revSWHIDWithContext)
        },
        {
          'objectType': 'snapshot',
          'objectPids': [snpSWHIDWithContext, snpSWHID],
          'badgeUrl': this.Urls.swh_badge('snapshot', swhids.snapshot.object_id),
          'badgePidUrl': this.Urls.swh_badge_pid(snpSWHID),
          'browseUrl': this.Urls.browse_swh_id(snpSWHIDWithContext)
        }
      ];

    });
  });

  beforeEach(function() {
    cy.visit(url);
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

    for (let td of testsData) {
      cy.get(`a[href="#swh-id-tab-${td.objectType}"]`)
        .click();

      cy.get(`#swh-id-tab-${td.objectType}`)
        .should('be.visible');

      cy.get(`#swh-id-tab-${td.objectType} .swh-id`)
        .contains(td.objectPids[0])
        .should('have.attr', 'href', this.Urls.browse_swh_id(td.objectPids[0]));

    }

  });

  it('should update other object identifiers contextual info when toggling context checkbox', function() {
    cy.get('.ui-slideouttab-handle')
      .click();

    for (let td of testsData) {

      cy.get(`a[href="#swh-id-tab-${td.objectType}"]`)
        .click();

      cy.get(`#swh-id-tab-${td.objectType} .swh-id`)
        .contains(td.objectPids[0])
        .should('have.attr', 'href', this.Urls.browse_swh_id(td.objectPids[0]));

      cy.get(`#swh-id-tab-${td.objectType} .swh-id-option`)
        .click();

      cy.get(`#swh-id-tab-${td.objectType} .swh-id`)
        .contains(td.objectPids[1])
        .should('have.attr', 'href', this.Urls.browse_swh_id(td.objectPids[1]));

      cy.get(`#swh-id-tab-${td.objectType} .swh-id-option`)
        .click();

      cy.get(`#swh-id-tab-${td.objectType} .swh-id`)
        .contains(td.objectPids[0])
        .should('have.attr', 'href', this.Urls.browse_swh_id(td.objectPids[0]));
    }

  });

  it('should display swh badges in identifiers tab for browsed objects', function() {
    cy.get('.ui-slideouttab-handle')
      .click();

    const originBadgeUrl = this.Urls.swh_badge('origin', origin.url);

    for (let td of testsData) {
      cy.get(`a[href="#swh-id-tab-${td.objectType}"]`)
        .click();

      cy.get(`#swh-id-tab-${td.objectType} .swh-badge-origin`)
        .should('have.attr', 'src', originBadgeUrl);

      cy.get(`#swh-id-tab-${td.objectType} .swh-badge-${td.objectType}`)
        .should('have.attr', 'src', td.badgeUrl);

    }

  });

  it('should display badge integration info when clicking on it', function() {

    cy.get('.ui-slideouttab-handle')
      .click();

    for (let td of testsData) {
      cy.get(`a[href="#swh-id-tab-${td.objectType}"]`)
        .click();

      cy.get(`#swh-id-tab-${td.objectType} .swh-badge-origin`)
        .click()
        .wait(500);

      for (let badgeType of ['html', 'md', 'rst']) {
        cy.get(`.modal .swh-badge-${badgeType}`)
          .contains(`${urlPrefix}${originBrowseUrl}`)
          .contains(`${urlPrefix}${originBadgeUrl}`);
      }

      cy.get('.modal.show .close')
        .click()
        .wait(500);

      cy.get(`#swh-id-tab-${td.objectType} .swh-badge-${td.objectType}`)
        .click()
        .wait(500);

      for (let badgeType of ['html', 'md', 'rst']) {
        cy.get(`.modal .swh-badge-${badgeType}`)
          .contains(`${urlPrefix}${td.browseUrl}`)
          .contains(`${urlPrefix}${td.badgePidUrl}`);
      }

      cy.get('.modal.show .close')
        .click()
        .wait(500);

    }
  });

  it('should be possible to retrieve SWHIDs context from JavaScript', function() {
    cy.window().then(win => {
      const swhIdsContext = win.swh.webapp.getSwhIdsContext();
      for (let testData of testsData) {
        assert.isTrue(swhIdsContext.hasOwnProperty(testData.objectType));
        assert.equal(swhIdsContext[testData.objectType].swhid,
                     testData.objectPids.slice(-1)[0]);
      }
    });
  });

});
