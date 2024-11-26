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

    cy.get('#swh-identifiers .ui-slideouttab-handle')
      .click();

    cy.get('#swh-identifiers')
      .should('have.class', 'ui-slideouttab-open');
    cy.get('#swh-identifiers-content')
      .should('have.css', 'display', 'block');

    cy.get('#swh-identifiers .ui-slideouttab-handle')
      .click();

    cy.get('#swh-identifiers')
      .should('not.have.class', 'ui-slideouttab-open');
    cy.get('#swh-identifiers-content')
      .should('have.css', 'display', 'none');

  });

  it('should display identifiers with permalinks for browsed objects', function() {
    cy.get('#swh-identifiers .ui-slideouttab-handle')
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
    cy.get('#swh-identifiers .ui-slideouttab-handle')
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
    cy.get('#swh-identifiers .ui-slideouttab-handle')
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

    cy.get('#swh-identifiers .ui-slideouttab-handle')
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
    cy.get('#swh-identifiers .ui-slideouttab-handle')
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
    cy.get('#swh-identifiers .ui-slideouttab-handle')
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

function logout() {
  cy.contains('logout')
    .click();
}

describe('Citations Tests', function() {

  beforeEach(function() {
    const originUrl = 'https://git.example.org/repo_with_cff_file';
    this.url = `${this.Urls.browse_origin()}?origin_url=${originUrl}`;
    cy.adminLogin();
    cy.visit(this.url);
    cy.intercept(this.Urls.api_1_raw_intrinsic_citation_swhid_get() + '**')
      .as('apiRawIntrinsicCitationGet');
  });

  it('should not make citations tab available for anonymous user', function() {
    logout();
    cy.visit(this.url);
    cy.get('#swh-citations .ui-slideouttab-handle')
      .should('not.exist');
  });

  it('should make citations tab available for ambassador user', function() {
    logout();
    cy.ambassadorLogin();
    cy.visit(this.url);
    cy.get('#swh-citations .ui-slideouttab-handle')
      .should('be.visible');
  });

  it('should make citations tab current when clicking on its handle', function() {
    cy.get('#swh-citations .ui-slideouttab-handle')
      .should('be.visible')
      .click();

    cy.get('#swh-citations-content')
      .should('be.visible');

    cy.get('#swh-identifiers-content')
      .should('not.be.visible');
  });

  it('should switch opened tabs when clicking on their handles', function() {
    cy.get('#swh-identifiers .ui-slideouttab-handle')
      .click();

    cy.get('#swh-identifiers-content')
      .should('be.visible');

    cy.get('#swh-citations-content')
      .should('not.be.visible');

    cy.get('#swh-citations .ui-slideouttab-handle')
      .click();

    cy.get('#swh-citations-content')
      .should('be.visible');

    cy.get('#swh-identifiers-content')
      .should('not.be.visible');

    cy.get('#swh-identifiers .ui-slideouttab-handle')
      .click();

    cy.get('#swh-identifiers-content')
      .should('be.visible');

    cy.get('#swh-citations-content')
      .should('not.be.visible');
  });

  it('should generate BibTex citation when selecting an object type', function() {
    cy.get('#swh-citations .ui-slideouttab-handle')
      .click();

    cy.wait('@apiRawIntrinsicCitationGet');

    // citation for directory object type is generated when opening citations tab
    cy.get('#citation-tab-directory .swh-citation')
      .should('contain', '@softwareversion{');

    const citationMetadataSWHID = 'swh:1:cnt:a93d22c5d806cd945de928e60e93b52b141c653e;' +
      'origin=https://git.example.org/repo_with_cff_file;' +
      'visit=swh:1:snp:eefa4d83d6ffb2b9b293bc3af1345a298d56af54;' +
      'anchor=swh:1:rev:384d62ee00f4cb3d4fa9f20a342c6f7209c9efe1;' +
      'path=/citation.cff';

    cy.get('#citation-source-directory a')
      .should('exist')
      .should('have.attr', 'href', `/${citationMetadataSWHID}`);

    cy.get('#citation-copy-button-directory .btn-citation-copy')
      .should('be.enabled');

    // revision object type
    cy.get(`a[href="#citation-tab-revision"]`)
      .click();

    cy.wait('@apiRawIntrinsicCitationGet');

    cy.get('#citation-tab-revision .swh-citation')
      .should('contain', '@softwareversion{');

    cy.get('#citation-source-revision a')
      .should('exist')
      .should('have.attr', 'href', `/${citationMetadataSWHID}`);

    cy.get('#citation-copy-button-revision .btn-citation-copy')
      .should('be.enabled');

    // snapshot object type
    cy.get(`a[href="#citation-tab-snapshot"]`)
      .click();

    cy.wait('@apiRawIntrinsicCitationGet');

    cy.get('#citation-tab-snapshot .swh-citation')
      .should('contain', '@software{');

    cy.get('#citation-source-snapshot a')
      .should('exist')
      .should('have.attr', 'href', `/${citationMetadataSWHID}`);

    cy.get('#citation-copy-button-snapshot .btn-citation-copy')
      .should('be.enabled');

  });

  it('should copy BibTex citation to clipboard', function() {
    cy.get('#swh-citations .ui-slideouttab-handle')
      .click();

    cy.wait('@apiRawIntrinsicCitationGet');

    cy.get('#citation-copy-button-directory .btn-citation-copy')
      .click();

    cy.window().then(win => {
      win.navigator.clipboard.readText().then(text => {
        expect(text.startsWith('@softwareversion{')).to.be.true;
      });

    });
  });

  it('should add selected lines info when generating citation for content', function() {
    cy.get('td a')
      .contains('citation.cff')
      .click();

    cy.get('.hljs-ln-numbers[data-line-number="1"]')
      .click()
      .get('.hljs-ln-numbers[data-line-number="3"]')
      .click({shiftKey: true});

    cy.get('#swh-citations .ui-slideouttab-handle')
      .click();

    cy.wait('@apiRawIntrinsicCitationGet');

    cy.get('#citation-tab-content .swh-citation')
      .should('contain', ';lines=1-3');
  });

  it('should not display citations tab if no citation can be generated', function() {
    cy.visit(`${this.Urls.browse_origin_directory()}?origin_url=${this.origin[0].url}`);

    cy.wait('@apiRawIntrinsicCitationGet');

    cy.get('#swh-citations')
      .should('not.be.visible');
  });

});
