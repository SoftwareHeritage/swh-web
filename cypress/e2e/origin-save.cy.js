/**
 * Copyright (C) 2019-2022  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

let url;
const origin = {
  type: 'git',
  url: 'https://git.example.org/user/repo'
};
const $ = Cypress.$;

const saveCodeMsg = {
  'success': 'The "save code now" request has been accepted and will be processed as soon as possible.',
  'warning': 'The "save code now" request has been put in pending state and may be accepted for processing after manual review.',
  'rejected': 'The "save code now" request has been rejected because the provided origin url is blacklisted.',
  'rateLimit': 'The rate limit for "save code now" requests has been reached. Please try again later.',
  'not-found': 'The provided url does not exist',
  'unknownError': 'An unexpected error happened when submitting the "save code now request',
  'csrfError': 'CSRF Failed: Referrer checking failed - no Referrer.'
};

const anonymousVisitTypes = ['bzr', 'cvs', 'git', 'hg', 'svn'];
const allVisitTypes = ['archives', 'bzr', 'cvs', 'git', 'hg', 'svn'];

function makeOriginSaveRequest(originType, originUrl) {
  cy.get('#swh-input-origin-url')
    .type(originUrl)
    .get('#swh-input-visit-type')
    .select(originType)
    .get('#swh-save-origin-form button[type=submit]')
    .click();
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
  // For error code with the error message in the 'reason' key response
  errorMessage = '',
  saveRequestDate = new Date(),
  visitDate = new Date(),
  visitStatus = null,
  fromWebhook = false
} = {}) {
  let response;
  if (responseStatus !== 200 && errorMessage) {
    response = {
      'reason': errorMessage
    };
  } else {
    response = genOriginSaveResponse({visitType: visitType,
                                      saveRequestStatus: saveRequestStatus,
                                      originUrl: originUrl,
                                      saveRequestDate: saveRequestDate,
                                      saveTaskStatus: saveTaskStatus,
                                      visitDate: visitDate,
                                      visitStatus: visitStatus,
                                      fromWebhook: fromWebhook
    });
  }
  cy.intercept('POST', requestUrl, {body: response, statusCode: responseStatus})
    .as('saveRequest');
}

// Mocks API response : /save/(:visit_type)/(:origin_url)
// visit_type : {'git', 'hg', 'svn', ...}
function genOriginSaveResponse({
  visitType = 'git',
  saveRequestStatus,
  originUrl,
  saveRequestDate = new Date(),
  saveTaskStatus,
  visitDate = new Date(),
  visitStatus,
  fromWebhook = false
} = {}) {
  return {
    'visit_type': visitType,
    'save_request_status': saveRequestStatus,
    'origin_url': originUrl,
    'id': 1,
    'save_request_date': saveRequestDate ? saveRequestDate.toISOString() : null,
    'save_task_status': saveTaskStatus,
    'visit_date': visitDate ? visitDate.toISOString() : null,
    'visit_status': visitStatus,
    'from_webhook': fromWebhook
  };
};

function loadSaveRequestsListPage() {
  // click on tab to visit requests list page
  cy.get('#swh-origin-save-requests-list-tab').click();
  // two XHR requests are sent by datatables when initializing requests table
  cy.wait(['@saveRequestsList', '@saveRequestsList']);
  // ensure datatable got rendered
  cy.wait(100);
}

describe('Origin Save Tests', function() {
  before(function() {
    url = this.Urls.origin_save();
    this.originSaveUrl = this.Urls.api_1_save_origin(origin.type, origin.url);
  });

  beforeEach(function() {
    cy.fixture('origin-save').as('originSaveJSON');
    cy.fixture('save-task-info').as('saveTaskInfoJSON');
    cy.visit(url);
  });

  it('should format appropriately values depending on their type', function() {
    const inputValues = [ // null values stay null
      {type: 'json', value: null, expectedValue: null},
      {type: 'date', value: null, expectedValue: null},
      {type: 'raw', value: null, expectedValue: null},
      {type: 'duration', value: null, expectedValue: null},
      // non null values formatted depending on their type
      {type: 'json', value: '{}', expectedValue: '"{}"'},
      {type: 'date', value: '04/04/2021 01:00:00', expectedValue: '4/4/2021, 1:00:00 AM'},
      {type: 'raw', value: 'value-for-identity', expectedValue: 'value-for-identity'},
      {type: 'duration', value: '10', expectedValue: '10 seconds'},
      {type: 'duration', value: 100, expectedValue: '100 seconds'}
    ];
    cy.window().then(win => {
      inputValues.forEach(function(input, index, array) {
        const actualValue = win.swh.save_code_now.formatValuePerType(input.type, input.value);
        assert.equal(actualValue, input.expectedValue);
      });
    });
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
    const originSaveUrl = this.Urls.api_1_save_origin('git', gitlabSubProjectUrl);

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
    const originSaveUrl = this.Urls.api_1_save_origin('git', gitlabSubProjectUrl);

    stubSaveRequest({requestUrl: originSaveUrl,
                     saveRequestStatus: 'accepted',
                     originurl: gitlabSubProjectUrl,
                     saveTaskStatus: 'not yet scheduled'});

    makeOriginSaveRequest('git', gitlabSubProjectUrl);

    cy.wait('@saveRequest').then(() => {
      checkAlertVisible('success', saveCodeMsg['success']);
    });
  });

  it('should validate git repo url starting with https://git.code.sf.net/u/', function() {
    const sfUserGirProjectUrl = 'https://git.code.sf.net/u/username/project.git';
    const originSaveUrl = this.Urls.api_1_save_origin('git', sfUserGirProjectUrl);

    stubSaveRequest({requestUrl: originSaveUrl,
                     saveRequestStatus: 'accepted',
                     originurl: sfUserGirProjectUrl,
                     saveTaskStatus: 'not yet scheduled'});

    makeOriginSaveRequest('git', sfUserGirProjectUrl);

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

  it('should show error when the origin does not exist (status: 400)', function() {
    stubSaveRequest({requestUrl: this.originSaveUrl,
                     originUrl: origin.url,
                     responseStatus: 400,
                     errorMessage: saveCodeMsg['not-found']});

    makeOriginSaveRequest(origin.type, origin.url);

    cy.wait('@saveRequest').then(() => {
      checkAlertVisible('danger', saveCodeMsg['not-found']);
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
    cy.intercept('/save/requests/list/**', {fixture: 'origin-save'})
      .as('saveRequestsList');

    loadSaveRequestsListPage();

    cy.get('tbody tr').then(rows => {
      let i = 0;
      for (const row of rows) {
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
        html += `&nbsp;<a href="${this.originSaveJSON.data[i].origin_url}" target="_blank" rel="noopener noreferrer">`;
        html += '<i class="mdi mdi-open-in-new" aria-hidden="true"></i></a>';
        assert.equal($(cells[2]).html(), html);
        assert.equal($(cells[3]).text(), this.originSaveJSON.data[i].save_request_status);
        assert.equal($(cells[4]).text(), saveStatus);
        ++i;
      }
    });
  });

  it('should display webhook icon when request was created from forge webhook receiver', function() {
    const originUrl = 'https://git.example.org/example.git';
    const saveRequestData = genOriginSaveResponse({
      saveRequestStatus: 'accepted',
      originUrl: originUrl,
      saveTaskStatus: 'succeeded',
      visitDate: null,
      visitStatus: 'full',
      fromWebhook: true
    });
    const saveRequestsListData = {
      'recordsTotal': 1,
      'draw': 2,
      'recordsFiltered': 1,
      'data': [saveRequestData]
    };

    cy.intercept('/save/requests/list/**', {body: saveRequestsListData})
      .as('saveRequestsList');

    loadSaveRequestsListPage();

    cy.get('tbody tr').then(rows => {
      const firstRowCells = rows[0].cells;
      expect($(firstRowCells[5]).html()).to.contain.string('mdi-webhook');
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

    loadSaveRequestsListPage();

    cy.get('tbody tr').then(rows => {
      const firstRowCells = rows[0].cells;
      const browseOriginUrl = `${this.Urls.browse_origin()}?origin_url=${encodeURIComponent(originUrl)}`;
      const browseOriginLink = `<a href="${browseOriginUrl}">${originUrl}</a>`;
      expect($(firstRowCells[2]).html()).to.have.string(browseOriginLink);
    });
  });

  it('should not add link to browse an origin when there is no visit status', function() {
    const originUrl = 'https://git.example.org/example.git';
    const saveRequestData = genOriginSaveResponse({
      saveRequestStatus: 'accepted',
      originUrl: originUrl,
      saveTaskStatus: 'succeeded',
      visitDate: null,
      visitStatus: null
    });
    const saveRequestsListData = {
      'recordsTotal': 1,
      'draw': 2,
      'recordsFiltered': 1,
      'data': [saveRequestData]
    };
    cy.intercept('/save/requests/list/**', {body: saveRequestsListData})
      .as('saveRequestsList');

    loadSaveRequestsListPage();

    cy.get('tbody tr').then(rows => {
      const firstRowCells = rows[0].cells;
      const tooltip = 'origin was successfully loaded, waiting for data to be available in database';
      const expectedContent = `<span title="${tooltip}">${originUrl}</span>`;
      expect($(firstRowCells[2]).html()).to.have.string(expectedContent);
    });
  });

  it('should display/close task info popover when clicking on the info button', function() {
    cy.intercept('/save/requests/list/**', {fixture: 'origin-save'})
      .as('saveRequestsList');
    cy.intercept('/save/task/info/**', {fixture: 'save-task-info'})
      .as('saveTaskInfo');

    loadSaveRequestsListPage();

    cy.get('.swh-save-request-info')
      .eq(0)
      .click();

    cy.wait('@saveTaskInfo');
    cy.get('.swh-save-request-info-popover')
      .should('be.visible');

    cy.get('.swh-save-request-info')
      .eq(0)
      .click();

    cy.get('.swh-save-request-info-popover')
      .should('not.exist');
  });

  it('should hide task info popover when clicking on the close button', function() {
    cy.intercept('/save/requests/list/**', {fixture: 'origin-save'})
      .as('saveRequestsList');
    cy.intercept('/save/task/info/**', {fixture: 'save-task-info'})
      .as('saveTaskInfo');

    loadSaveRequestsListPage();

    cy.get('.swh-save-request-info')
      .eq(0)
      .click();

    cy.wait('@saveTaskInfo');
    cy.get('.swh-save-request-info-popover')
      .should('be.visible');

    cy.get('.swh-save-request-info-close')
      .click();

    cy.get('.swh-save-request-info-popover')
      .should('not.exist');
  });

  it('should fill save request form when clicking on "Save again" button', function() {
    cy.intercept('/save/requests/list/**', {fixture: 'origin-save'})
      .as('saveRequestsList');

    loadSaveRequestsListPage();

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
    cy.intercept('/save/requests/list/**', {fixture: 'origin-save'})
      .as('saveRequestsList');
    stubSaveRequest({requestUrl: this.Urls.api_1_save_origin(badVisitType, originUrl),
                     visitType: badVisitType,
                     saveRequestStatus: 'accepted',
                     originUrl: originUrl,
                     saveTaskStatus: 'failed',
                     visitStatus: 'failed',
                     responseStatus: 200,
                     errorMessage: saveCodeMsg['accepted']});

    makeOriginSaveRequest(badVisitType, originUrl);

    loadSaveRequestsListPage();

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

  it('should create save request for authenticated user', function() {
    cy.userLogin();
    cy.visit(url);
    const originUrl = 'https://git.example.org/account/repo';
    stubSaveRequest({requestUrl: this.Urls.api_1_save_origin('git', originUrl),
                     saveRequestStatus: 'accepted',
                     originUrl: origin.url,
                     saveTaskStatus: 'not yet scheduled'});

    makeOriginSaveRequest('git', originUrl);

    cy.wait('@saveRequest').then(() => {
      checkAlertVisible('success', saveCodeMsg['success']);
    });
  });

  it('should not show user requests filter checkbox for anonymous users', function() {
    cy.get('#swh-origin-save-requests-list-tab').click();
    cy.get('#swh-save-requests-user-filter').should('not.exist');
  });

  it('should show user requests filter checkbox for authenticated users', function() {
    cy.userLogin();
    cy.visit(url);
    cy.get('#swh-origin-save-requests-list-tab').click();
    cy.get('#swh-save-requests-user-filter').should('exist');
  });

  it('should show only user requests when filter is activated', function() {
    cy.intercept('POST', '/api/1/origin/save/**')
      .as('saveRequest');
    cy.intercept(this.Urls.origin_save_requests_list('all') + '**')
      .as('saveRequestsList');

    const originAnonymousUser = 'https://some.git.server/project/';
    const originAuthUser = 'https://other.git.server/project/';

    // anonymous user creates a save request
    makeOriginSaveRequest('git', originAnonymousUser);
    cy.wait('@saveRequest');

    // authenticated user creates another save request
    cy.userLogin();
    cy.visit(url);
    makeOriginSaveRequest('git', originAuthUser);
    cy.wait('@saveRequest');

    // user requests filter checkbox should be in the DOM
    loadSaveRequestsListPage();
    cy.get('#swh-save-requests-user-filter').should('exist');

    // check unfiltered user requests
    cy.get('tbody tr').then(rows => {
      expect(rows.length).to.eq(2);
      expect($(rows[0].cells[2]).text()).to.contain(originAuthUser);
      expect($(rows[1].cells[2]).text()).to.contain(originAnonymousUser);
    });

    // activate filter and check filtered user requests
    cy.get('#swh-save-requests-user-filter')
      .click({force: true});
    cy.wait('@saveRequestsList');

    cy.get('tbody tr').then(rows => {
      expect(rows.length).to.eq(1);
      expect($(rows[0].cells[2]).text()).to.contain(originAuthUser);
    });

    // deactivate filter and check unfiltered user requests
    cy.get('#swh-save-requests-user-filter')
      .click({force: true});
    cy.wait('@saveRequestsList');

    cy.get('tbody tr').then(rows => {
      expect(rows.length).to.eq(2);
    });

  });

  it('should list unprivileged visit types when not connected', function() {
    cy.visit(url);
    cy.get('#swh-input-visit-type').children('option').then(options => {
      const actual = [...options].map(o => o.value);
      expect(actual).to.deep.eq(anonymousVisitTypes);
    });
  });

  it('should list unprivileged visit types when connected as unprivileged user', function() {
    cy.userLogin();
    cy.visit(url);
    cy.get('#swh-input-visit-type').children('option').then(options => {
      const actual = [...options].map(o => o.value);
      expect(actual).to.deep.eq(anonymousVisitTypes);
    });
  });

  it('should list privileged visit types when connected as ambassador', function() {
    cy.ambassadorLogin();
    cy.visit(url);
    cy.get('#swh-input-visit-type').children('option').then(options => {
      const actual = [...options].map(o => o.value);
      expect(actual).to.deep.eq(allVisitTypes);
    });
  });

  it('should display extra inputs when dealing with \'archives\' visit type', function() {
    cy.ambassadorLogin();
    cy.visit(url);

    for (const visitType of anonymousVisitTypes) {
      cy.get('#swh-input-visit-type').select(visitType);
      cy.get('.swh-save-origin-archives-form').should('not.be.visible');
    }

    // this should display more inputs with the 'archives' type
    cy.get('#swh-input-visit-type').select('archives');
    cy.get('.swh-save-origin-archives-form').should('be.visible');

  });

  it('should be allowed to submit \'archives\' save request when connected as ambassador', function() {
    const originUrl = 'https://github.com/chromium/chromium/tags';
    const artifactUrl = 'https://github.com/chromium/chromium/archive/refs/tags/104.0.5106.1.tar.gz';
    const artifactVersion = '104.0.5106.1';
    stubSaveRequest({
      requestUrl: this.Urls.api_1_save_origin('archives', originUrl),
      saveRequestStatus: 'accepted',
      originUrl: originUrl,
      saveTaskStatus: 'not yet scheduled'
    });

    cy.ambassadorLogin();
    cy.visit(url);

    // input new 'archives' information and submit
    cy.get('#swh-input-origin-url')
      .type(originUrl)
      .get('#swh-input-visit-type')
      .select('archives')
      .get('#swh-input-artifact-url-0')
      .type(artifactUrl)
      .get('#swh-input-artifact-version-0')
      .clear()
      .type(artifactVersion)
      .get('#swh-save-origin-form button[type=submit]')
      .click();

    cy.wait('@saveRequest').then(() => {
      checkAlertVisible('success', saveCodeMsg['success']);
    });

  });

  it('should submit multiple artifacts for the archives visit type', function() {
    const originUrl = 'https://ftp.gnu.org/pub/pub/gnu/3dldf';
    const artifactUrl = 'https://ftp.gnu.org/pub/pub/gnu/3dldf/3DLDF-1.1.4.tar.gz';
    const artifactVersion = '1.1.4';
    const artifact2Url = 'https://ftp.gnu.org/pub/pub/gnu/3dldf/3DLDF-1.1.5.tar.gz';
    const artifact2Version = '1.1.5';

    cy.ambassadorLogin();
    cy.visit(url);

    cy.get('#swh-input-origin-url')
      .type(originUrl)
      .get('#swh-input-visit-type')
      .select('archives');

    // fill first artifact info
    cy.get('#swh-input-artifact-url-0')
      .type(artifactUrl)
      .get('#swh-input-artifact-version-0')
      .clear()
      .type(artifactVersion);

    // add new artifact form row
    cy.get('#swh-add-archive-artifact')
      .click();

    // check new row is displayed
    cy.get('#swh-input-artifact-url-1')
        .should('exist');

    // request removal of newly added row
    cy.get('#swh-remove-archive-artifact-1')
      .click();

    // check row has been removed
    cy.get('#swh-input-artifact-url-1')
      .should('not.exist');

    // add new artifact form row
    cy.get('#swh-add-archive-artifact')
      .click();

    // fill second artifact info
    cy.get('#swh-input-artifact-url-1')
      .type(artifact2Url)
      .get('#swh-input-artifact-version-1')
      .clear()
      .type(artifact2Version);

    // setup request interceptor to check POST data and stub response
    cy.intercept('POST', this.Urls.api_1_save_origin('archives', originUrl), (req) => {
      expect(req.body).to.deep.equal({
        archives_data: [
          {artifact_url: artifactUrl, artifact_version: artifactVersion},
          {artifact_url: artifact2Url, artifact_version: artifact2Version}
        ]
      });
      req.reply(genOriginSaveResponse({
        visitType: 'archives',
        saveRequestStatus: 'accepted',
        originUrl: originUrl,
        saveRequestDate: new Date(),
        saveTaskStatus: 'not yet scheduled',
        visitDate: null,
        visitStatus: null
      }));
    }).as('saveRequest');

    // submit form
    cy.get('#swh-save-origin-form button[type=submit]')
      .click();

    // submission should be successful
    cy.wait('@saveRequest').then(() => {
      checkAlertVisible('success', saveCodeMsg['success']);
    });

  });

  it('should autofill artifact version when pasting artifact url', function() {
    const originUrl = 'https://ftp.gnu.org/pub/pub/gnu/3dldf';
    const artifactUrl = 'https://ftp.gnu.org/pub/pub/gnu/3dldf/3DLDF-1.1.4.tar.gz';
    const artifactVersion = '3DLDF-1.1.4';
    const artifact2Url = 'https://example.org/artifact/test/1.3.0.zip';
    const artifact2Version = '1.3.0';

    cy.ambassadorLogin();
    cy.visit(url);

    cy.get('#swh-input-origin-url')
      .type(originUrl)
      .get('#swh-input-visit-type')
      .select('archives');

    // fill first artifact info
    cy.get('#swh-input-artifact-url-0')
      .type(artifactUrl);

    // check autofilled version
    cy.get('#swh-input-artifact-version-0')
      .should('have.value', artifactVersion);

    // add new artifact form row
    cy.get('#swh-add-archive-artifact')
      .click();

    // fill second artifact info
    cy.get('#swh-input-artifact-url-1')
      .type(artifact2Url);

    // check autofilled version
    cy.get('#swh-input-artifact-version-1')
      .should('have.value', artifact2Version);
  });

  it('should use canonical URL for github repository to save', function() {
    const ownerRepo = 'BIC-MNI/mni_autoreg';
    const canonicalOriginUrl = 'https://github.com/BIC-MNI/mni_autoreg';

    // stub call to github Web API fetching canonical repo URL
    cy.intercept(`https://api.github.com/repos/${ownerRepo.toLowerCase()}`, (req) => {
      req.reply({html_url: canonicalOriginUrl});
    }).as('ghWebApiRequest');

    // stub save request creation with canonical URL of github repo
    cy.intercept('POST', this.Urls.api_1_save_origin('git', canonicalOriginUrl), (req) => {
      req.reply(genOriginSaveResponse({
        visitType: 'git',
        saveRequestStatus: 'accepted',
        originUrl: canonicalOriginUrl,
        saveRequestDate: new Date(),
        saveTaskStatus: 'not yet scheduled',
        visitDate: null,
        visitStatus: null
      }));
    }).as('saveRequest');

    for (const originUrl of ['https://github.com/BiC-MnI/MnI_AuToReG',
                             'https://github.com/BiC-MnI/MnI_AuToReG.git',
                             'https://github.com/BiC-MnI/MnI_AuToReG/',
                             'https://BiC-MnI.github.io/MnI_AuToReG/'
    ]) {

      // enter non canonical URL of github repo
      cy.get('#swh-input-origin-url')
        .clear()
        .type(originUrl);

      // submit form
      cy.get('#swh-save-origin-form button[type=submit]')
        .click();

      // submission should be successful
      cy.wait('@ghWebApiRequest')
        .wait('@saveRequest').then(() => {
          checkAlertVisible('success', saveCodeMsg['success']);
        });
    }

  });

  it('should switch tabs when playing with browser history', function() {
    cy.intercept('/save/requests/list/**', {fixture: 'origin-save'});
    cy.intercept('/save/task/info/**', {fixture: 'save-task-info'});

    cy.get('#swh-origin-save-request-help-tab')
      .should('have.class', 'active');

    cy.get('#swh-origin-save-requests-list-tab')
      .click();

    cy.get('#swh-origin-save-requests-list-tab')
      .should('have.class', 'active');

    cy.go('back')
      .get('#swh-origin-save-request-help-tab')
      .should('have.class', 'active');

    cy.go('forward')
      .get('#swh-origin-save-requests-list-tab')
      .should('have.class', 'active');
  });

  it('should not accept origin URL with password', function() {

    makeOriginSaveRequest('git', 'https://user:password@git.example.org/user/repo');

    cy.get('.invalid-feedback')
      .should('contain', 'The origin url contains a password and cannot be accepted for security reasons');

  });

  it('should accept origin URL with username but without password', function() {

    cy.adminLogin();
    cy.visit(url);

    const originUrl = 'https://user@git.example.org/user/repo';

    stubSaveRequest({requestUrl: this.Urls.api_1_save_origin('git', originUrl),
                     saveRequestStatus: 'accepted',
                     originUrl: originUrl,
                     saveTaskStatus: 'not yet scheduled'});

    makeOriginSaveRequest('git', originUrl);

    cy.wait('@saveRequest').then(() => {
      checkAlertVisible('success', saveCodeMsg['success']);
    });

  });

  it('should accept origin URL with anonymous credentials', function() {

    cy.adminLogin();
    cy.visit(url);

    const originUrl = 'https://anonymous:anonymous@git.example.org/user/repo';

    stubSaveRequest({requestUrl: this.Urls.api_1_save_origin('git', originUrl),
                     saveRequestStatus: 'accepted',
                     originUrl: originUrl,
                     saveTaskStatus: 'not yet scheduled'});

    makeOriginSaveRequest('git', originUrl);

    cy.wait('@saveRequest').then(() => {
      checkAlertVisible('success', saveCodeMsg['success']);
    });

  });

  it('should accept origin URL with empty password', function() {

    cy.adminLogin();
    cy.visit(url);

    const originUrl = 'https://anonymous:@git.example.org/user/repo';

    stubSaveRequest({requestUrl: this.Urls.api_1_save_origin('git', originUrl),
                     saveRequestStatus: 'accepted',
                     originUrl: originUrl,
                     saveTaskStatus: 'not yet scheduled'});

    makeOriginSaveRequest('git', originUrl);

    cy.wait('@saveRequest').then(() => {
      checkAlertVisible('success', saveCodeMsg['success']);
    });

  });

  it('should display csv export button above requests list for staff users', function() {
    cy.intercept('/save/requests/list/**', {fixture: 'origin-save'})
      .as('saveRequestsList');

    loadSaveRequestsListPage();
    cy.get('.requests-csv-export a')
      .should('not.exist');

    cy.adminLogin();
    cy.visit(url);
    loadSaveRequestsListPage();
    cy.get('.requests-csv-export a')
      .should('exist')
      .should('have.attr', 'href', this.Urls.admin_origin_save_requests_csv());
  });

  it('should autofill form when providing origin URL as query parameter', function() {
    const svnUrl = 'svn://example.org/project';
    cy.visit(`${url}?origin_url=${svnUrl}`);

    cy.get('#swh-input-origin-url')
      .should('have.attr', 'value', svnUrl);

    cy.get('#swh-input-visit-type option:selected')
      .should('have.value', 'svn');
  });

});
