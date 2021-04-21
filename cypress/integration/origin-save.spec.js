/**
 * Copyright (C) 2019-2021  The Software Heritage developers
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
function stubSaveRequest({
  requestUrl,
  visitType = 'git',
  saveRequestStatus,
  originUrl,
  saveTaskStatus,
  responseStatus = 200,
  errorMessage = '',
  saveRequestDate = new Date(),
  visitDate = new Date(),
  visitStatus = null
} = {}) {
  let response;
  if (responseStatus !== 200 && errorMessage) {
    response = {
      'detail': errorMessage
    };
  } else {
    response = genOriginSaveResponse({visitType: visitType,
                                      saveRequestStatus: saveRequestStatus,
                                      originUrl: originUrl,
                                      saveRequestDate: saveRequestDate,
                                      saveTaskStatus: saveTaskStatus,
                                      visitDate: visitDate,
                                      visitStatus: visitStatus
    });
  }
  cy.intercept('POST', requestUrl, {body: response, statusCode: responseStatus})
    .as('saveRequest');
}

// Mocks API response : /save/(:visit_type)/(:origin_url)
// visit_type : {'git', 'hg', 'svn'}
function genOriginSaveResponse({
  visitType = 'git',
  saveRequestStatus,
  originUrl,
  saveRequestDate = new Date(),
  saveTaskStatus,
  visitDate = new Date(),
  visitStatus
} = {}) {
  return {
    'visit_type': visitType,
    'save_request_status': saveRequestStatus,
    'origin_url': originUrl,
    'id': 1,
    'save_request_date': saveRequestDate ? saveRequestDate.toISOString() : null,
    'save_task_status': saveTaskStatus,
    'visit_date': visitDate ? visitDate.toISOString() : null,
    'visit_status': visitStatus
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
  });

  it('should display accepted message when accepted', function() {
    stubSaveRequest({requestUrl: this.originSaveUrl,
                     saveRequestStatus: 'accepted',
                     originUrl: origin.url,
                     saveTaskStatus: 'not yet scheduled'});

    makeOriginSaveRequest(origin.type, origin.url);

    cy.wait('@saveRequest').then(() => {
      checkAlertVisible('success', saveCodeMsg['success']);
    });
  });

  it('should validate gitlab subproject url', function() {
    const gitlabSubProjectUrl = 'https://gitlab.com/user/project/sub/';
    const originSaveUrl = this.Urls.origin_save_request('git', gitlabSubProjectUrl);

    stubSaveRequest({requestUrl: originSaveUrl,
                     saveRequestStatus: 'accepted',
                     originurl: gitlabSubProjectUrl,
                     saveTaskStatus: 'not yet scheduled'});

    makeOriginSaveRequest('git', gitlabSubProjectUrl);

    cy.wait('@saveRequest').then(() => {
      checkAlertVisible('success', saveCodeMsg['success']);
    });
  });

  it('should validate project url with _ in username', function() {
    const gitlabSubProjectUrl = 'https://gitlab.com/user_name/project.git';
    const originSaveUrl = this.Urls.origin_save_request('git', gitlabSubProjectUrl);

    stubSaveRequest({requestUrl: originSaveUrl,
                     saveRequestStatus: 'accepted',
                     originurl: gitlabSubProjectUrl,
                     saveTaskStatus: 'not yet scheduled'});

    makeOriginSaveRequest('git', gitlabSubProjectUrl);

    cy.wait('@saveRequest').then(() => {
      checkAlertVisible('success', saveCodeMsg['success']);
    });
  });

  it('should display warning message when pending', function() {
    stubSaveRequest({requestUrl: this.originSaveUrl,
                     saveRequestStatus: 'pending',
                     originUrl: origin.url,
                     saveTaskStatus: 'not created'});

    makeOriginSaveRequest(origin.type, origin.url);

    cy.wait('@saveRequest').then(() => {
      checkAlertVisible('warning', saveCodeMsg['warning']);
    });
  });

  it('should show error when csrf validation failed (status: 403)', function() {
    stubSaveRequest({requestUrl: this.originSaveUrl,
                     saveRequestStatus: 'rejected',
                     originUrl: origin.url,
                     saveTaskStatus: 'not created',
                     responseStatus: 403,
                     errorMessage: saveCodeMsg['csrfError']});

    makeOriginSaveRequest(origin.type, origin.url);

    cy.wait('@saveRequest').then(() => {
      checkAlertVisible('danger', saveCodeMsg['csrfError']);
    });
  });

  it('should show error when origin is rejected (status: 403)', function() {
    stubSaveRequest({requestUrl: this.originSaveUrl,
                     saveRequestStatus: 'rejected',
                     originUrl: origin.url,
                     saveTaskStatus: 'not created',
                     responseStatus: 403,
                     errorMessage: saveCodeMsg['rejected']});

    makeOriginSaveRequest(origin.type, origin.url);

    cy.wait('@saveRequest').then(() => {
      checkAlertVisible('danger', saveCodeMsg['rejected']);
    });
  });

  it('should show error when rate limited (status: 429)', function() {
    stubSaveRequest({requestUrl: this.originSaveUrl,
                     saveRequestStatus: 'Request was throttled. Expected available in 60 seconds.',
                     originUrl: origin.url,
                     saveTaskStatus: 'not created',
                     responseStatus: 429});

    makeOriginSaveRequest(origin.type, origin.url);

    cy.wait('@saveRequest').then(() => {
      checkAlertVisible('danger', saveCodeMsg['rateLimit']);
    });
  });

  it('should show error when unknown error occurs (status other than 200, 403, 429)', function() {
    stubSaveRequest({requestUrl: this.originSaveUrl,
                     saveRequestStatus: 'Error',
                     originUrl: origin.url,
                     saveTaskStatus: 'not created',
                     responseStatus: 406});

    makeOriginSaveRequest(origin.type, origin.url);

    cy.wait('@saveRequest').then(() => {
      checkAlertVisible('danger', saveCodeMsg['unknownError']);
    });
  });

  it('should display origin save info in the requests table', function() {
    cy.intercept('/save/requests/list/**', {fixture: 'origin-save'});
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
        if (saveStatus === 'succeeded') {
          let browseOriginUrl = `${this.Urls.browse_origin()}?origin_url=${encodeURIComponent(this.originSaveJSON.data[i].origin_url)}`;
          browseOriginUrl += `&amp;timestamp=${encodeURIComponent(this.originSaveJSON.data[i].visit_date)}`;
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

  it('should not add timestamp to the browse origin URL is no visit date has been found', function() {
    const originUrl = 'https://git.example.org/example.git';
    const saveRequestData = genOriginSaveResponse({
      saveRequestStatus: 'accepted',
      originUrl: originUrl,
      saveTaskStatus: 'succeeded',
      visitDate: null,
      visitStatus: 'full'
    });
    const saveRequestsListData = {
      'recordsTotal': 1,
      'draw': 2,
      'recordsFiltered': 1,
      'data': [saveRequestData]
    };
    cy.intercept('/save/requests/list/**', {body: saveRequestsListData})
      .as('saveRequestsList');
    cy.get('#swh-origin-save-requests-list-tab').click();
    cy.wait('@saveRequestsList');
    cy.get('tbody tr').then(rows => {
      const firstRowCells = rows[0].cells;
      const browseOriginUrl = `${this.Urls.browse_origin()}?origin_url=${encodeURIComponent(originUrl)}`;
      const browseOriginLink = `<a href="${browseOriginUrl}">${originUrl}</a>`;
      expect($(firstRowCells[2]).html()).to.have.string(browseOriginLink);
    });
  });

  it('should display/close task info popover when clicking on the info button', function() {
    cy.intercept('/save/requests/list/**', {fixture: 'origin-save'});
    cy.intercept('/save/task/info/**', {fixture: 'save-task-info'});

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
      .should('not.exist');
  });

  it('should hide task info popover when clicking on the close button', function() {
    cy.intercept('/save/requests/list/**', {fixture: 'origin-save'});
    cy.intercept('/save/task/info/**', {fixture: 'save-task-info'});

    cy.get('#swh-origin-save-requests-list-tab').click();
    cy.get('.swh-save-request-info')
      .eq(0)
      .click();

    cy.get('.swh-save-request-info-popover')
      .should('be.visible');

    cy.get('.swh-save-request-info-close')
      .click();

    cy.get('.swh-save-request-info-popover')
      .should('not.exist');
  });

  it('should fill save request form when clicking on "Save again" button', function() {
    cy.intercept('/save/requests/list/**', {fixture: 'origin-save'});

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

  it('should select correct visit type if possible when clicking on "Save again" button', function() {
    const originUrl = 'https://gitlab.inria.fr/solverstack/maphys/maphys/';
    const badVisitType = 'hg';
    const goodVisitType = 'git';
    cy.intercept('/save/requests/list/**', {fixture: 'origin-save'});
    stubSaveRequest({requestUrl: this.Urls.origin_save_request(badVisitType, originUrl),
                     visitType: badVisitType,
                     saveRequestStatus: 'accepted',
                     originUrl: originUrl,
                     saveTaskStatus: 'failed',
                     visitStatus: 'failed',
                     responseStatus: 200,
                     errorMessage: saveCodeMsg['accepted']});

    makeOriginSaveRequest(badVisitType, originUrl);

    cy.get('#swh-origin-save-requests-list-tab').click();
    cy.wait('@saveRequest').then(() => {
      cy.get('.swh-save-origin-again')
        .eq(0)
        .click();

      cy.get('tbody tr').eq(0).then(row => {
        const cells = row[0].cells;
        cy.get('#swh-input-visit-type')
          .should('have.value', goodVisitType);
        cy.get('#swh-input-origin-url')
          .should('have.value', $(cells[2]).text().slice(0, -1));
      });
    });
  });

});
