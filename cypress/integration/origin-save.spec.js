/**
 * Copyright (C) 2019-2020  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

let url;
let origin;
const $ = Cypress.$;

const saveCodeMsg = {
  'success': 'The "save code now" request has been accepted and will be processed as soon as possible.',
  'warning': 'The "save code now" request has been put in pending state and may be accepted for processing after manual review.',
  'rejected': 'The "save code now" request has been rejected because the provided origin url is blacklisted.',
  'rateLimit': 'The rate limit for "save code now" requests has been reached. Please try again later.',
  'unknownError': 'An unexpected error happened when submitting the "save code now request',
  'csrfError': 'CSRF Failed: Referrer checking failed - no Referrer.'
};

function makeOriginSaveRequest(originType, originUrl) {
  cy.get('#swh-input-origin-url')
    .type(originUrl)
    .get('#swh-input-visit-type')
    .select(originType)
    .get('#swh-save-origin-form')
    .submit();
}

function checkAlertVisible(alertType, msg) {
  cy.get('#swh-origin-save-request-status')
    .should('be.visible')
    .find(`.alert-${alertType}`)
    .should('be.visible')
    .and('contain', msg);
}

// Stub requests to save an origin
function stubSaveRequest(requestUrl, objectType, status, originUrl, taskStatus,
                         responseStatus = 200, errorMessage = '') {
  let response;
  if (responseStatus !== 200 && errorMessage) {
    response = {'detail': errorMessage};
  } else {
    response = genOriginSaveResponse(objectType, status, originUrl, Date().toString(), taskStatus);
  }
  cy.route({
    method: 'POST',
    status: responseStatus,
    url: requestUrl,
    response: response
  }).as('saveRequest');
}

// Mocks API response : /save/(:object_type)/(:origin_url)
// object_type : {'git', 'hg', 'svn'}
function genOriginSaveResponse(objectType, saveRequestStatus, originUrl, saveRequestDate, saveTaskStatus) {
  return {
    'visit_type': objectType,
    'save_request_status': saveRequestStatus,
    'origin_url': originUrl,
    'id': 1,
    'save_request_date': saveRequestDate,
    'save_task_status': saveTaskStatus,
    'visit_date': null
  };
};

describe('Origin Save Tests', function() {
  before(function() {
    url = this.Urls.origin_save();
    origin = this.origin[0];
    this.originSaveUrl = this.Urls.origin_save_request(origin.type, origin.url);
  });

  beforeEach(function() {
    cy.fixture('origin-save').as('originSaveJSON');
    cy.fixture('save-task-info').as('saveTaskInfoJSON');
    cy.visit(url);
    cy.server();
  });

  it('should display accepted message when accepted', function() {
    stubSaveRequest(this.originSaveUrl, origin.type, 'accepted',
                    origin.url, 'not yet scheduled');

    makeOriginSaveRequest(origin.type, origin.url);

    cy.wait('@saveRequest').then(() => {
      checkAlertVisible('success', saveCodeMsg['success']);
    });
  });

  it('should validate gitlab subproject url', function() {
    const gitlabSubProjectUrl = 'https://gitlab.com/user/project/sub/';
    const originSaveUrl = this.Urls.origin_save_request('git', gitlabSubProjectUrl);
    stubSaveRequest(originSaveUrl, 'git', 'accepted',
                    gitlabSubProjectUrl, 'not yet scheduled');

    makeOriginSaveRequest('git', gitlabSubProjectUrl);

    cy.wait('@saveRequest').then(() => {
      checkAlertVisible('success', saveCodeMsg['success']);
    });
  });

  it('should display warning message when pending', function() {
    stubSaveRequest(this.originSaveUrl, origin.type, 'pending',
                    origin.url, 'not created');

    makeOriginSaveRequest(origin.type, origin.url);

    cy.wait('@saveRequest').then(() => {
      checkAlertVisible('warning', saveCodeMsg['warning']);
    });
  });

  it('should show error when csrf validation failed (status: 403)', function() {
    stubSaveRequest(this.originSaveUrl, origin.type, 'rejected',
                    origin.url, 'not created', 403, saveCodeMsg['csrfError']);

    makeOriginSaveRequest(origin.type, origin.url);

    cy.wait('@saveRequest').then(() => {
      checkAlertVisible('danger', saveCodeMsg['csrfError']);
    });
  });

  it('should show error when origin is rejected (status: 403)', function() {
    stubSaveRequest(this.originSaveUrl, origin.type, 'rejected',
                    origin.url, 'not created', 403, saveCodeMsg['rejected']);

    makeOriginSaveRequest(origin.type, origin.url);

    cy.wait('@saveRequest').then(() => {
      checkAlertVisible('danger', saveCodeMsg['rejected']);
    });
  });

  it('should show error when rate limited (status: 429)', function() {
    stubSaveRequest(this.originSaveUrl, origin.type,
                    'Request was throttled. Expected available in 60 seconds.',
                    origin.url, 'not created', 429);

    makeOriginSaveRequest(origin.type, origin.url);

    cy.wait('@saveRequest').then(() => {
      checkAlertVisible('danger', saveCodeMsg['rateLimit']);
    });
  });

  it('should show error when unknown error occurs (status other than 200, 403, 429)', function() {
    stubSaveRequest(this.originSaveUrl, origin.type, 'Error',
                    origin.url, 'not created', 406);

    makeOriginSaveRequest(origin.type, origin.url);

    cy.wait('@saveRequest').then(() => {
      checkAlertVisible('danger', saveCodeMsg['unknownError']);
    });
  });

  it('should display origin save info in the requests table', function() {
    cy.route('GET', '/save/requests/list/**', '@originSaveJSON');
    cy.get('#swh-origin-save-requests-list-tab').click();
    cy.get('tbody tr').then(rows => {
      let i = 0;
      for (let row of rows) {
        const cells = row.cells;
        const requestDateStr = new Date(this.originSaveJSON.data[i].save_request_date).toLocaleString();
        const saveStatus = this.originSaveJSON.data[i].save_task_status;
        assert.equal($(cells[0]).text(), requestDateStr);
        assert.equal($(cells[1]).text(), this.originSaveJSON.data[i].visit_type);
        let html = '';
        if (saveStatus === 'succeed') {
          let browseOriginUrl = `${this.Urls.browse_origin()}?origin_url=${this.originSaveJSON.data[i].origin_url}`;
          browseOriginUrl += `&amp;timestamp=${this.originSaveJSON.data[i].visit_date}`;
          html += `<a href="${browseOriginUrl}">${this.originSaveJSON.data[i].origin_url}</a>`;
        } else {
          html += this.originSaveJSON.data[i].origin_url;
        }
        html += `&nbsp;<a href="${this.originSaveJSON.data[i].origin_url}">`;
        html += '<i class="mdi mdi-open-in-new" aria-hidden="true"></i></a>';
        assert.equal($(cells[2]).html(), html);
        assert.equal($(cells[3]).text(), this.originSaveJSON.data[i].save_request_status);
        assert.equal($(cells[4]).text(), saveStatus);
        ++i;
      }
    });
  });

  it('should display/close task info popover when clicking on the info button', function() {
    cy.route('GET', '/save/requests/list/**', '@originSaveJSON');
    cy.route('GET', '/save/task/info/**', '@saveTaskInfoJSON');

    cy.get('#swh-origin-save-requests-list-tab').click();
    cy.get('.swh-save-request-info')
      .eq(0)
      .click();

    cy.get('.swh-save-request-info-popover')
      .should('be.visible');

    cy.get('.swh-save-request-info')
      .eq(0)
      .click();

    cy.get('.swh-save-request-info-popover')
      .should('not.be.visible');
  });

  it('should hide task info popover when clicking on the close button', function() {
    cy.route('GET', '/save/requests/list/**', '@originSaveJSON');
    cy.route('GET', '/save/task/info/**', '@saveTaskInfoJSON');

    cy.get('#swh-origin-save-requests-list-tab').click();
    cy.get('.swh-save-request-info')
      .eq(0)
      .click();

    cy.get('.swh-save-request-info-popover')
      .should('be.visible');

    cy.get('.swh-save-request-info-close')
      .click();

    cy.get('.swh-save-request-info-popover')
      .should('not.be.visible');
  });

  it('should fill save request form when clicking on "Save again" button', function() {
    cy.route('GET', '/save/requests/list/**', '@originSaveJSON');

    cy.get('#swh-origin-save-requests-list-tab').click();
    cy.get('.swh-save-origin-again')
      .eq(0)
      .click();

    cy.get('tbody tr').eq(0).then(row => {
      const cells = row[0].cells;
      cy.get('#swh-input-visit-type')
        .should('have.value', $(cells[1]).text());
      cy.get('#swh-input-origin-url')
        .should('have.value', $(cells[2]).text().slice(0, -1));
    });
  });

  it('should select correct origin type if possible when clicking on "Save again" button', function() {
    const originUrl = 'https://gitlab.inria.fr/solverstack/maphys/maphys/';
    const badOriginType = 'hg';
    const goodOriginType = 'git';
    cy.route('GET', '/save/requests/list/**', '@originSaveJSON');
    stubSaveRequest(this.Urls.origin_save_request(badOriginType, originUrl),
                    badOriginType, 'accepted',
                    originUrl, 'failed', 200, saveCodeMsg['accepted']);

    makeOriginSaveRequest(badOriginType, originUrl);

    cy.get('#swh-origin-save-requests-list-tab').click();
    cy.wait('@saveRequest').then(() => {
      cy.get('.swh-save-origin-again')
        .eq(0)
        .click();

      cy.get('tbody tr').eq(0).then(row => {
        const cells = row[0].cells;
        cy.get('#swh-input-visit-type')
          .should('have.value', goodOriginType);
        cy.get('#swh-input-origin-url')
          .should('have.value', $(cells[2]).text().slice(0, -1));
      });
    });
  });

});
