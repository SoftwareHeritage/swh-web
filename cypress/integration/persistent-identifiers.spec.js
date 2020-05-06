/**
 * Copyright (C) 2019-2020  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

let origin, originBadgeUrl, originBrowseUrl;
let url, urlPrefix;
let browsedObjectMetadata;
let cntPid, cntPidWithOrigin, cntPidWithOriginAndLines;
let dirPid, dirPidWithOrigin;
let relPid, relPidWithOrigin;
let revPid, revPidWithOrigin;
let snpPid, snpPidWithOrigin;
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

      testsData = [
        {
          'objectType': 'content',
          'objectPids': [cntPidWithOriginAndLines, cntPidWithOrigin, cntPid],
          'badgeUrl': this.Urls.swh_badge('content', browsedObjectMetadata.sha1_git),
          'badgePidUrl': this.Urls.swh_badge_pid(cntPidWithOriginAndLines),
          'browseUrl': this.Urls.browse_swh_id(cntPidWithOriginAndLines)
        },
        {
          'objectType': 'directory',
          'objectPids': [dirPidWithOrigin, dirPid],
          'badgeUrl': this.Urls.swh_badge('directory', browsedObjectMetadata.directory),
          'badgePidUrl': this.Urls.swh_badge_pid(dirPidWithOrigin),
          'browseUrl': this.Urls.browse_swh_id(dirPidWithOrigin)
        },
        {
          'objectType': 'release',
          'objectPids': [relPidWithOrigin, relPid],
          'badgeUrl': this.Urls.swh_badge('release', browsedObjectMetadata.release),
          'badgePidUrl': this.Urls.swh_badge_pid(relPidWithOrigin),
          'browseUrl': this.Urls.browse_swh_id(relPidWithOrigin)
        },
        {
          'objectType': 'revision',
          'objectPids': [revPidWithOrigin, revPid],
          'badgeUrl': this.Urls.swh_badge('revision', browsedObjectMetadata.revision),
          'badgePidUrl': this.Urls.swh_badge_pid(revPidWithOrigin),
          'browseUrl': this.Urls.browse_swh_id(revPidWithOrigin)
        },
        {
          'objectType': 'snapshot',
          'objectPids': [snpPidWithOrigin, snpPid],
          'badgeUrl': this.Urls.swh_badge('snapshot', browsedObjectMetadata.snapshot),
          'badgePidUrl': this.Urls.swh_badge_pid(snpPidWithOrigin),
          'browseUrl': this.Urls.browse_swh_id(snpPidWithOrigin)
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

    for (let td of testsData) {

      // already tested
      if (td.objectType === 'content') continue;

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
