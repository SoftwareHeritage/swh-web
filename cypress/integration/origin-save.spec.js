/**
 * Copyright (C) 2019  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

let url;
let origin;

const saveCodeMsg = {
  'success': 'The "save code now" request has been accepted and will be processed as soon as possible.',
  'warning': 'The "save code now" request has been put in pending state and may be accepted for processing after manual review.',
  'rejected': 'The "save code now" request has been rejected because the provided origin url is blacklisted.',
  'rateLimit': 'The rate limit for "save code now" requests has been reached. Please try again later.',
  'unknownErr': 'An unexpected error happened when submitting the "save code now request'
};

function makeOriginSaveRequest(originType, originUrl) {
  cy.get('#swh-input-visit-type')
    .select(originType)
    .get('#swh-input-origin-url')
    .type(originUrl)
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
function stubSaveRequest(requestUrl, objectType, status, originUrl, taskStatus, responseStatus = 200) {
  cy.route({
    method: 'POST',
    status: responseStatus,
    url: requestUrl,
    response: genOriginSaveResponse(objectType, status, originUrl, Date().toString(), taskStatus)
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

  it('should display warning message when pending', function() {
    stubSaveRequest(this.originSaveUrl, origin.type, 'pending',
                    origin.url, 'not created');

    makeOriginSaveRequest(origin.type, origin.url);

    cy.wait('@saveRequest').then(() => {
      checkAlertVisible('warning', saveCodeMsg['warning']);
    });
  });

  it('should show error when origin is rejected (status: 403)', function() {
    stubSaveRequest(this.originSaveUrl, origin.type, 'rejected',
                    origin.url, 'not created', 403);

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
      checkAlertVisible('danger', saveCodeMsg['unknownErr']);
    });
  });

});
