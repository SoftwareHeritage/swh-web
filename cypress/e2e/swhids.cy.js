/**
 * Copyright (C) 2019-2024  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

const $ = Cypress.$;

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

describe('SWHIDs Tests', function() {

  before(function() {
    origin = this.origin[1];
    url = `${this.Urls.browse_origin_content()}?origin_url=${origin.url}&path=${origin.content[0].path}`;
    url = `${url}&release=${origin.release.name}#L${firstSelLine}-L${lastSelLine}`;
    originBadgeUrl = this.Urls.swh_badge('origin', origin.url);
    originBrowseUrl = `${this.Urls.browse_origin()}?origin_url=${origin.url}`;
    cy.visit(url).window().then(win => {
      urlPrefix = `${win.location.protocol}//${win.location.hostname}`;
      if (win.location.port) {
        urlPrefix += `:${win.location.port}`;
      }
      // for some reasons, cypress hangs when visiting that URL in beforeEach callback
      // due to HTTP redirection, so get the redirected URL here to workaround that issue.
      url = win.location.href;
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
          'objectSWHIDs': [cntSWHIDWithContext, cntSWHID],
          'badgeUrl': this.Urls.swh_badge('content', swhids.content.object_id),
          'badgeSWHIDUrl': this.Urls.swh_badge_swhid(cntSWHID),
          'browseUrl': this.Urls.browse_swhid(cntSWHIDWithContext)
        },
        {
          'objectType': 'directory',
          'objectSWHIDs': [dirSWHIDWithContext, dirSWHID],
          'badgeUrl': this.Urls.swh_badge('directory', swhids.directory.object_id),
          'badgeSWHIDUrl': this.Urls.swh_badge_swhid(dirSWHID),
          'browseUrl': this.Urls.browse_swhid(dirSWHIDWithContext)
        },
        {
          'objectType': 'release',
          'objectSWHIDs': [relSWHIDWithContext, relSWHID],
          'badgeUrl': this.Urls.swh_badge('release', swhids.release.object_id),
          'badgeSWHIDUrl': this.Urls.swh_badge_swhid(relSWHID),
          'browseUrl': this.Urls.browse_swhid(relSWHIDWithContext)
        },
        {
          'objectType': 'revision',
          'objectSWHIDs': [revSWHIDWithContext, revSWHID],
          'badgeUrl': this.Urls.swh_badge('revision', swhids.revision.object_id),
          'badgeSWHIDUrl': this.Urls.swh_badge_swhid(revSWHID),
          'browseUrl': this.Urls.browse_swhid(revSWHIDWithContext)
        },
        {
          'objectType': 'snapshot',
          'objectSWHIDs': [snpSWHIDWithContext, snpSWHID],
          'badgeUrl': this.Urls.swh_badge('snapshot', swhids.snapshot.object_id),
          'badgeSWHIDUrl': this.Urls.swh_badge_swhid(snpSWHID),
          'browseUrl': this.Urls.browse_swhid(snpSWHIDWithContext)
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
    cy.get('#swh-identifiers-content')
      .should('have.css', 'display', 'none');

    cy.get('.ui-slideouttab-handle')
      .click();

    cy.get('#swh-identifiers')
      .should('have.class', 'ui-slideouttab-open');
    cy.get('#swh-identifiers-content')
      .should('have.css', 'display', 'block');

    cy.get('.ui-slideouttab-handle')
      .click();

    cy.get('#swh-identifiers')
      .should('not.have.class', 'ui-slideouttab-open');
    cy.get('#swh-identifiers-content')
      .should('have.css', 'display', 'none');

  });

  it('should display identifiers with permalinks for browsed objects', function() {
    cy.get('.ui-slideouttab-handle')
      .click();

    for (const td of testsData) {
      cy.get(`a[href="#swhid-tab-${td.objectType}"]`)
        .click();

      cy.get(`#swhid-tab-${td.objectType}`)
        .should('be.visible');

      cy.get(`#swhid-tab-${td.objectType} .swhid`)
        .should('have.text', td.objectSWHIDs[0].replace(/;/g, ';\n'))
        .should('have.attr', 'href', this.Urls.browse_swhid(td.objectSWHIDs[0]));

    }

  });

  it('should update other object identifiers contextual info when toggling context checkbox', function() {
    cy.get('.ui-slideouttab-handle')
      .click();

    for (const td of testsData) {

      cy.get(`a[href="#swhid-tab-${td.objectType}"]`)
        .click();

      cy.get(`#swhid-tab-${td.objectType} .swhid`)
        .should('have.text', td.objectSWHIDs[0].replace(/;/g, ';\n'))
        .should('have.attr', 'href', this.Urls.browse_swhid(td.objectSWHIDs[0]));

      cy.get(`#swhid-tab-${td.objectType} .swhid-option`)
        .click();

      cy.get(`#swhid-tab-${td.objectType} .swhid`)
        .contains(td.objectSWHIDs[1])
        .should('have.attr', 'href', this.Urls.browse_swhid(td.objectSWHIDs[1]));

      cy.get(`#swhid-tab-${td.objectType} .swhid-option`)
        .click();

      cy.get(`#swhid-tab-${td.objectType} .swhid`)
        .should('have.text', td.objectSWHIDs[0].replace(/;/g, ';\n'))
        .should('have.attr', 'href', this.Urls.browse_swhid(td.objectSWHIDs[0]));
    }

  });

  it('should display swh badges in identifiers tab for browsed objects', function() {
    cy.get('.ui-slideouttab-handle')
      .click();

    const originBadgeUrl = this.Urls.swh_badge('origin', origin.url);

    for (const td of testsData) {
      cy.get(`a[href="#swhid-tab-${td.objectType}"]`)
        .click();

      cy.get(`#swhid-tab-${td.objectType} .swh-badge-origin`)
        .should('have.attr', 'src', originBadgeUrl);

      cy.get(`#swhid-tab-${td.objectType} .swh-badge-${td.objectType}`)
        .should('have.attr', 'src', td.badgeUrl);

    }

  });

  it('should display badge integration info when clicking on it', function() {

    cy.get('.ui-slideouttab-handle')
      .click();

    for (const td of testsData) {
      cy.get(`a[href="#swhid-tab-${td.objectType}"]`)
        .click();

      cy.get(`#swhid-tab-${td.objectType} .swh-badge-origin`)
        .click()
        .wait(500);

      for (const badgeType of ['html', 'md', 'rst']) {
        cy.get(`.modal .swh-badge-${badgeType}`)
          .should('contain.text', `${urlPrefix}${originBrowseUrl}`)
          .should('contain.text', `${urlPrefix}${originBadgeUrl}`);
      }

      cy.get('.modal .swh-badge-html')
        .should('contain.text', `alt="Archived | ${origin.url}"`);

      cy.get('.modal.show .btn-close')
        .click()
        .wait(500);

      cy.get(`#swhid-tab-${td.objectType} .swh-badge-${td.objectType}`)
        .click()
        .wait(500);

      for (const badgeType of ['html', 'md', 'rst']) {
        cy.get(`.modal .swh-badge-${badgeType}`)
          .should('contain.text', `${urlPrefix}${td.browseUrl}`)
          .should('contain.text', `${urlPrefix}${td.badgeSWHIDUrl}`);
      }

      cy.get('.modal .swh-badge-html')
        .should('contain.text', `alt="Archived | ${td.objectSWHIDs[1]}"`);

      cy.get('.modal.show .btn-close')
        .click()
        .wait(500);

    }
  });

  it('should be possible to retrieve SWHIDs context from JavaScript', function() {
    cy.window().then(win => {
      const swhIdsContext = win.swh.webapp.getSwhIdsContext();
      for (const testData of testsData) {
        assert.isTrue(swhIdsContext.hasOwnProperty(testData.objectType));
        assert.equal(swhIdsContext[testData.objectType].swhid,
                     testData.objectSWHIDs.slice(-1)[0]);
      }
    });
  });

  it('should update tab size according to screen size', function() {
    // use a small viewport size
    cy.viewport(320, 480);
    cy.visit(url);
    cy.get('.ui-slideouttab-handle')
      .click();
    cy.window().then(win => {
      // SWHIDs tab should fit in the screen
      cy.get('#swh-identifiers').invoke('width').should('be.lt', win.innerWidth);
      cy.get('#swh-identifiers').invoke('height').should('be.lt', win.innerHeight);
      // its content should be scrollable
      cy.get('#swh-identifiers').then(tab => {
        expect($(tab).height()).to.be.lessThan($(tab).prop('scrollHeight'));
      });
    });
  });

  it('should update copy buttons after clicking on them', function() {
    cy.get('.ui-slideouttab-handle')
      .click();

    for (const td of testsData) {
      cy.get(`a[href="#swhid-tab-${td.objectType}"]`)
        .click();

      cy.get(`#swhid-tab-${td.objectType}`)
        .should('be.visible');

      cy.get(`#swhid-tab-${td.objectType} .btn-swhid-copy`)
          .should('contain.text', 'Copy identifier')
          .should('not.contain.text', 'Copied!')
          .click()
          .should('have.text', 'Copied!')
          .wait(1001)
          .should('not.contain.text', 'Copied!')
          .should('contain.text', 'Copy identifier');

      cy.get(`#swhid-tab-${td.objectType} .btn-swhid-url-copy`)
          .should('contain.text', 'Copy permalink')
          .should('not.contain.text', 'Copied!')
          .click()
          .should('have.text', 'Copied!')
          .wait(1001)
          .should('not.contain.text', 'Copied!')
          .should('contain.text', 'Copy permalink');
    }
  });
});
