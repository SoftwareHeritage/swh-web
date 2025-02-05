/**
 * Copyright (C) 2024 The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

const emailAddress = 'email@example.com';
// should match django's settings
const adminEmailAddress = 'alter-support@example.org';
const legalEmailAddress = 'alter-legal@example.org';
// see create_test_alter.py
const blockedEmailAddress = 'blocked@domain.local';
const expiredEmailToken = 'ExpiredEmailToken';
const expiredAccessToken = 'ExpiredAccessToken';
const validAccessToken = 'ValidAccessToken';
const copyrightAlterationId = '00000000-0000-4000-8000-000000000001';
const copyrightAlterationEmail = 'user1@domain.local';

const categoriesId = ['categoryCopyright', 'categoryPii', 'categoryLegal'];
const defaultOrigins = [
  'https://many.origins/35',
  'https://git.example.org/repo_with_submodules',
  'https://many.origins/45'
];
// content policies
const step0Url = '/content-policies/';
// email validation
const step1Url = '/alteration/email/';
// category selection
const step2Url = '/alteration/category/';
// origins selection
const step3Url = '/alteration/origins/';
// reasons & expected outcome
const step4Url = '/alteration/reasons/';
// summary
const step5Url = '/alteration/summary/';
// admin dashboard
const adminUrl = '/admin/alteration/';
// admin alteration
const copyrightAlterationAdminUrl = `/admin/alteration/${copyrightAlterationId}/`;
const copyrightAlterationTitle = 'Copyright / License infringement by user1@domain.local';
// client side
const copyrightAlterationUrl = `/alteration/${copyrightAlterationId}/`;
const copyrightAlterationTokenUrl = `/alteration/link/${validAccessToken}`;

/**
 * Extracts urls from a text
 * @param {string} text a text containing urls
 * @returns an Array of urls path
 */
function extractUrls(text) {
  const urls = [];
  text.match(/\bhttps?:\/\/\S+/gi).forEach((url) => {
    urls.push(new URL(url).pathname);
  });
  return urls;
}

/**
 * Fills the email confirmation form
 * @param {string} address an email address
 */
function fillEmail(address) {
  cy.get('#id_email').type(address);
  cy.get('form.form button[type="submit"]').click();
}

/**
 * Finds the email confirmation link and click it
 * @param {string} address an email address
 */
function confirmEmail(address) {
  cy.task('findEmail', {subject: 'Please confirm your email address', recipient: address}).then((message) => {
    cy.visit(extractUrls(message)[0]);
  });
}

/**
 * Chooses a category from the categories accordion
 * @param {string} categoryId a category id
 */
function chooseCategory(categoryId) {
  cy.get(`button[aria-controls="${categoryId}"]`).click();
  cy.get(`div#${categoryId}`).should('be.visible');
  cy.get(`div#${categoryId}`).find('button[type=submit]').click();
}

/**
 * Search origins and submit the form
 * @param {string} query a search query
 */
function searchOrigins(query) {
  cy.get('#id_query').clear();
  cy.get('#id_query').type(query + '{enter}');
}

/**
 * Checks checkboxes matching origins and submit the form
 * @param {Array} origins an array of urls
 */
function checkOrigins(origins) {
  defaultOrigins.forEach((url) => {
    cy.get(`input[type=checkbox][value="${url}"]`).check();
  });
  cy.get('button[form=origins-form][type=submit]').click();
}

/**
 * Clears and fills a form input.
 * @param {string} input an input selector
 * @param {string} value a value
 */
function fillInput(input, value) {
  cy.get(input).clear();
  cy.get(input).type(value);
}

/**
 * Fills reasons & expected outcome and submit the form
 * @param {string} reasons reasons
 * @param {string} outcome expected outcome
 */
function fillReasons(reasons, outcome) {
  fillInput('#id_reasons', reasons);
  fillInput('#id_expected_outcome', outcome);
  cy.get('form#reasons-form').find('button[type=submit]').click();
}

/**
 * Confirms summary and submit the form
 * @param {Array} origins an array of urls
 */
function confirmSummary() {
  cy.get('input#id_confirm').check();
  cy.get('form#summary-form').find('button[type=submit]').click();
}

describe('Archive alteration request, requester side tests', () => {

  beforeEach(() => {
    // remove all emails from the /tmp folder
    cy.task('cleanupEmails');
  });

  it('should request a token to access an alteration request', () => {
    const url = `/alteration/${copyrightAlterationId}/`;
    const accessUrl = url + 'access/';
    cy.visit(url);
    cy.location('pathname').should('be.equal', accessUrl);
    cy.get('div.alert-warning').contains('Access to this page is restricted').should('be.visible');
    // request a magic link
    cy.get('#id_email').type(copyrightAlterationEmail + '{enter}');
    cy.location('pathname').should('be.equal', accessUrl);
    cy.get('div.alert-info').contains('If your email address matches').should('be.visible');
    cy.task('findEmail', {subject: 'Access to your alteration request', recipient: copyrightAlterationEmail}).then((message) => {
      expect(message).to.contain('link will give you access');
      const urls = extractUrls(message);
      expect(urls).to.have.lengthOf(1);
      expect(urls[0]).to.contain('/alteration/link/');
      // click the link
      cy.visit(urls[0]);
    });
    cy.location('pathname').should('be.equal', url);
    cy.get('div.alert-info').contains('You now have access').should('be.visible');
  });

  it('should reject expired access tokens', () => {
    const url = `/alteration/link/${expiredAccessToken}`;
    const accessUrl = `/alteration/${copyrightAlterationId}/access/`;
    cy.visit(url);
    // redirected to the request access url
    cy.location('pathname').should('be.equal', accessUrl);
    cy.get('div.alert-warning').contains('This token has expired').should('be.visible');
  });

  it('should allow access to the requester view of the request with a cookie', () => {
    cy.visit(copyrightAlterationTokenUrl);
    // redirected to the request access url
    cy.location('pathname').should('be.equal', copyrightAlterationUrl);
    // reload is allowed
    cy.reload();
    cy.location('pathname').should('not.contain', '/access/');
    // but without cookies we're redirected to the access form
    cy.clearCookies();
    cy.reload();
    cy.location('pathname').should('contain', '/access/');
  });

  it('should allow access to requester view of the request', () => {
    cy.visit(copyrightAlterationTokenUrl);
    // redirected to the request access url
    cy.location('pathname').should('be.equal', copyrightAlterationUrl);
    // status is: planning
    cy.contains('the actions to be carried out').should('be.visible');

    cy.get('table#alteration-origins tbody tr').contains('https://gitlab.local/user1/code').should('be.visible');
    cy.get('table#alteration-origins tbody tr').contains('https://gitlab.local/user1/project').should('be.visible');
    // no button on the requester interface
    cy.get('table#alteration-origins tbody tr button').should('not.exist');

    cy.get('div#alteration-reasons').contains('not published under an open license').should('be.visible');
    cy.get('div#alteration-expected-outcome').contains('delete everything').should('be.visible');

    cy.get('ul#alteration-events li').contains('created').should('be.visible');
    cy.get('ul#alteration-events li').contains('to be informed').should('be.visible');
    // no internal messages on the requester interface
    cy.get('ul#alteration-events li').contains('internal message').should('not.exist');
  });

  it('should allow the requester to edit the request', () => {
    cy.visit(copyrightAlterationTokenUrl);

    // click the edit request button
    cy.get('div#alteration-modal').should('not.be.visible');
    cy.get('button').contains('Edit this archive alteration request').click();
    cy.get('div#alteration-modal').should('be.visible');

    // only two fields
    cy.get('div#alteration-modal label').should('have.length', 2);
    fillInput('div#alteration-modal #id_reasons', 'not published under an open license at all');
    fillInput('div#alteration-modal #id_expected_outcome', 'delete everything, right now');
    cy.get('div#alteration-modal').find('button[type=submit]').click();

    // redirected to the admin page with the request updated
    cy.location('pathname').should('be.equal', copyrightAlterationUrl);
    cy.get('div.alert-success').contains('has been updated').should('be.visible');
    cy.get('div#alteration-reasons').contains('at all').should('be.visible');
    cy.get('div#alteration-expected-outcome').contains('right now').should('be.visible');
  });

  it('should allow the requester to send a message', () => {
    const messageContent = `My message to an operator ${Date.now()}`;
    cy.visit(copyrightAlterationTokenUrl);

    // click the edit request button
    cy.get('div#message-modal').should('not.be.visible');
    cy.get('button').contains('Send a message').click();
    cy.get('div#message-modal').should('be.visible');

    // only one field
    cy.get('div#message-modal label').should('have.length', 1);
    fillInput('div#message-modal #id_content', messageContent);
    cy.get('div#message-modal').find('button[type=submit]').click();

    // redirected to the admin page with the message shown in the activity log
    cy.location('pathname').should('be.equal', copyrightAlterationUrl);
    cy.get('div.alert-success').contains('Message sent').should('be.visible');
    cy.get('ul#alteration-events li').first().within(() => {
      cy.get('[itemprop=text]').should('contain', messageContent);
      cy.get('[itemprop=sender]').should('contain', 'Requester');
      cy.get('[itemprop=recipient]').should('contain', 'Support');
    });
    // an email to support is sent with the whole message
    cy.task('findEmail', {subject: `New message on ${copyrightAlterationTitle}`, recipient: adminEmailAddress}).then((message) => {
      expect(message).to.contain(messageContent);
      expect(message).to.contain('From: Requester');
      const urls = extractUrls(message);
      // and a link to the alteration request
      expect(urls).to.have.lengthOf(1);
      expect(urls[0]).to.contain(copyrightAlterationAdminUrl);
    });
  });
});

describe('Archive alteration request assistant tests', () => {

  beforeEach(() => {
    // remove all emails from the /tmp folder
    cy.task('cleanupEmails');
  });

  it('should have a content policy page that leads to the alteration request tunnel', () => {
    cy.visit('/');
    cy.get('footer.app-footer').find('a[data-testid=swh-web-alter-content-policy]').click();
    cy.location('pathname').should('be.equal', step0Url);
    cy.get('div#swh-web-content').find('a.btn-primary').click();
    cy.location('pathname').should('be.equal', step1Url);
  });

  it('should confirm emails', () => {
    cy.visit(step1Url);
    // Only one step active
    cy.get('nav.process-steps .active').should('have.length', 1);
    cy.get('nav.process-steps a#alter-step-email.active').should('be.visible');
    fillEmail(emailAddress);
    cy.location('pathname').should('be.equal', step1Url);
    cy.get('div.alert-info').contains(emailAddress).should('be.visible');
    confirmEmail(emailAddress);
    cy.location('pathname').should('be.equal', step2Url);
    cy.get('div.alert-success').contains(emailAddress).should('be.visible');
  });

  it('should check email validity', () => {
    cy.visit(step1Url);
    fillEmail('test@swh');
    cy.location('pathname').should('be.equal', step1Url);
    cy.get('div.alert-danger').contains('fix the errors').should('be.visible');
    cy.get('input#id_email').siblings('div.invalid-feedback').contains('valid email').should('be.visible');
  });

  it('should redirect email confirmation', () => {
    cy.visit(step2Url);
    cy.location('pathname').should('be.equal', step1Url);
    cy.get('div.alert-warning').should('be.visible');
    cy.get('div.alert-warning').contains('confirm your email address');
  });

  it('should allow category selection', () => {
    cy.visit(step1Url);
    fillEmail(emailAddress);
    confirmEmail(emailAddress);
    cy.get('nav.process-steps .active').should('have.length', 1);
    cy.get('nav.process-steps a#alter-step-category.active').should('be.visible');
    // accordion is closed by default
    categoriesId.forEach((categoryId) => {
      cy.get(`div#${categoryId}`).should('not.be.visible');
    });
    // open accordions
    categoriesId.forEach((categoryId) => {
      chooseCategory(categoryId);
      cy.location('pathname').should('be.equal', step3Url);
      cy.visit(step2Url); // go back to try the other categories
    });
    // submitting an invalid category returns an error
    cy.get(`button[aria-controls="${categoriesId[0]}"]`).click();
    cy.get(`div#${categoriesId[0]}`).find('button[type=submit]').invoke('attr', 'value', 'invalid').click();
    cy.location('pathname').should('be.equal', step2Url);
    cy.get('div.alert-danger').contains('invalid is not one of the available choices').should('be.visible');
  });

  it('should allow origins selection', () => {
    cy.visit(step1Url);
    fillEmail(emailAddress);
    confirmEmail(emailAddress);
    chooseCategory(categoriesId[0]); // copyright
    cy.get('nav.process-steps .active').should('have.length', 1);
    cy.get('nav.process-steps a#alter-step-origins.active').should('be.visible');
    // by default the table showing origins is hidden
    cy.get('form#origins-form').should('not.exist');
    // fire a search that returns no result
    searchOrigins('a.non.existing.origin');
    cy.location('pathname').should('be.equal', step3Url);
    cy.get('#id_query').should('have.value', 'a.non.existing.origin');
    cy.get('table#origins-results').find('tr.table-warning').contains('are you sure your code has been archived').should('be.visible');
    cy.get('button[form=origins-form][type=submit]').should('be.disabled');
    // a search that returns results but submit without checking anything
    searchOrigins('http');
    cy.location('pathname').should('be.equal', step3Url);
    cy.get('#id_query').should('have.value', 'http');
    cy.get('table#origins-results').find('input[type=checkbox][name=urls]').should('have.length', 50); // archive.search_origin default limit
    cy.get('button[form=origins-form][type=submit]').click();
    cy.get('div.alert-danger').contains('invalid').should('be.visible');
    cy.location('pathname').should('be.equal', step3Url);
    // check some origins + submit
    checkOrigins(defaultOrigins);
    cy.location('pathname').should('be.equal', step4Url);
  });

  it('should allow filling reasons', () => {
    cy.visit(step1Url);
    fillEmail(emailAddress);
    confirmEmail(emailAddress);
    chooseCategory(categoriesId[1]); // PII
    searchOrigins('http');
    checkOrigins(defaultOrigins);
    cy.get('nav.process-steps .active').should('have.length', 1);
    cy.get('nav.process-steps a#alter-step-reasons.active').should('be.visible');
    // should match the reasons template for PII
    cy.get('textarea#id_reasons')
      .invoke('val')
      .then(reasons => {
        expect(reasons).to.contain('rewritten the history');
      });
    cy.get('textarea#id_expected_outcome')
      .invoke('val')
      .then(txt => {
        expect(txt).to.contain('remove archived content');
      });
    fillReasons('random reasons', 'random outcome');
    cy.location('pathname').should('be.equal', step5Url);
  });

  it('should display a summary and submit the request', () => {
    cy.visit(step1Url);
    fillEmail(emailAddress);
    confirmEmail(emailAddress);
    chooseCategory(categoriesId[2]); // Other legal matters
    searchOrigins('http');
    checkOrigins(defaultOrigins);
    fillReasons('random reasons', 'random outcome');
    cy.get('nav.process-steps .active').should('have.length', 1);
    cy.get('nav.process-steps a#alter-step-summary.active').should('be.visible');
    // previous values should be found in the summary
    defaultOrigins.forEach((url) => {
      cy.get('section#origins-summary').contains(url);
    });
    cy.get('section#reasons-summary').contains('random reasons');
    cy.get('section#reasons-summary').contains('random outcome');
    cy.get('section#contact-summary').contains(emailAddress);
    // confirmation checkbox is required
    cy.get('form#summary-form').find('button[type=submit]').click();
    cy.get('input#id_confirm:invalid').should('exist');
    confirmSummary();
    // we're redirected to the request details view
    cy.title().should('contain', 'Other legal matters');
    cy.get('div.alert-success').contains('alteration request has been received').should('be.visible');
  });

  it('should send an email confirmation to the requester after submitting a request', () => {
    cy.visit(step1Url);
    fillEmail(emailAddress);
    confirmEmail(emailAddress);
    chooseCategory(categoriesId[0]);
    searchOrigins('http');
    checkOrigins(defaultOrigins);
    fillReasons('random reasons', 'random outcome');
    confirmSummary();
    cy.task('findEmail', {subject: 'Confirmation of your archive alteration request', recipient: emailAddress}).then((message) => {
      expect(message).to.contain('We have received your alteration request');
      defaultOrigins.forEach((url) => {
        expect(message).to.contain(url);
      });
      const urls = extractUrls(message);
      expect(urls).to.have.lengthOf(4);
      // the last url is the link to the alteration request details, which
      // should be the current page
      cy.location('pathname').should('equal', urls[3]);
    });
  });

  it('should send an admin notification after submitting a request', () => {
    cy.visit(step1Url);
    fillEmail(emailAddress);
    confirmEmail(emailAddress);
    chooseCategory(categoriesId[2]); // other legal matters
    searchOrigins('http');
    checkOrigins(defaultOrigins);
    fillReasons('random reasons', 'random outcome');
    confirmSummary();
    cy.task('findEmail', {subject: 'New archive alteration request', recipient: adminEmailAddress}).then((message) => {
      expect(message).to.contain('Other legal matters');
      defaultOrigins.forEach((url) => {
        expect(message).to.contain(url);
      });
      const urls = extractUrls(message);
      expect(urls).to.have.lengthOf(4);
      // the first url is the link to the alteration request admin
      expect(urls[0]).to.contain('/admin/alteration/');
    });
  });

  it('should use cookie to authorize access to a request', () => {
    cy.visit(step1Url);
    fillEmail(emailAddress);
    confirmEmail(emailAddress);
    chooseCategory(categoriesId[2]); // other legal matters
    searchOrigins('http');
    checkOrigins(defaultOrigins);
    fillReasons('random reasons', 'random outcome');
    confirmSummary();
    // reload is allowed
    cy.reload();
    cy.location('pathname').should('not.contain', '/access/');
    // but without cookies we're redirected to the access form
    cy.clearCookies();
    cy.reload();
    cy.location('pathname').should('contain', '/access/');
  });

  it('should block specific email addresses', () => {
    cy.visit(step1Url);
    fillEmail(blockedEmailAddress);
    cy.location('pathname').should('be.equal', step1Url);
    cy.get('div.alert-danger').contains('fix the errors').should('be.visible');
    cy.get('input#id_email').siblings('div.invalid-feedback').contains('blocked by Software Heritage').should('be.visible');
  });

  it('should reject expired email confirmation tokens', () => {
    const url = `/alteration/email/verification/${expiredEmailToken}/`;
    cy.visit(url);
    cy.location('pathname').should('be.equal', step1Url);
    cy.get('div.alert-warning').contains('token has expired').should('be.visible');
  });
});

describe('Archive alteration request, admin side tests', () => {

  beforeEach(() => {
    // remove all emails from the /tmp folder
    cy.task('cleanupEmails');
  });

  it('should display the alteration admin menu to authorized users', () => {
    cy.visit('/');
    cy.get('nav[aria-label=Administration] li[title="Alteration administration"]').should('not.exist');
    cy.alterSupportLogin();
    cy.visit('/');
    cy.get('nav[aria-label=Administration] li[title="Alteration administration"]').should('be.visible');
    cy.get('a.swh-alteration-admin-link').click();
    cy.location('pathname').should('be.equal', adminUrl);
  });

  it('should allow admin to filter requests', () => {
    cy.alterSupportLogin();
    cy.visit(adminUrl);
    cy.get('table.table tbody tr').its('length').should('be.gt', 1);
    fillInput('#id_query', 'user1@domain.local{enter}');
    cy.get('table.table tbody tr').its('length').should('be.equal', 1);
    cy.get('.form-select').select('planning');
    fillInput('#id_query', '{enter}');
    cy.get('table.table tbody tr').its('length').should('be.equal', 1);
  });

  it('should allow admin to view an alteration', () => {
    cy.alterSupportLogin();
    cy.visit(adminUrl);
    const trSelector = `table.table tbody tr#alteration-${copyrightAlterationId}`;
    // display origins
    cy.get(trSelector).find('button').click();
    cy.get(trSelector).find(`div#origins-${copyrightAlterationId}`).should('be.visible');
    // view alteration
    cy.get(trSelector).find('a').first().click();
    cy.location('pathname').should('be.equal', copyrightAlterationAdminUrl);
    cy.get('table#alteration-origins tbody tr').contains('https://gitlab.local/user1/code').should('be.visible');
    cy.get('table#alteration-origins tbody tr').contains('https://gitlab.local/user1/project').should('be.visible');
    cy.get('div#alteration-reasons').contains('not published under an open license').should('be.visible');
    cy.get('div#alteration-expected-outcome').contains('delete everything').should('be.visible');
    cy.get('ul#alteration-events li').contains('created').should('be.visible');
    cy.get('ul#alteration-events li').contains('to be informed').should('be.visible');
    cy.get('ul#alteration-events li').contains('internal message').should('be.visible');
  });

  it('should allow admin to edit an alteration', () => {
    const newOutcome = 'delete everything, please';
    cy.alterSupportLogin();
    cy.visit(copyrightAlterationAdminUrl);

    // click the edit request button
    cy.get('div#alteration-modal').should('not.be.visible');
    cy.get('button').contains('Edit request').click();
    cy.get('div#alteration-modal').should('be.visible');

    // change the outcome
    fillInput('div#alteration-modal #id_expected_outcome', newOutcome);
    cy.get('div#alteration-modal').find('button[type=submit]').click();

    // redirected to the admin page with the new outcome shown & a new event
    cy.location('pathname').should('be.equal', copyrightAlterationAdminUrl);
    cy.get('div.alert-success').contains('has been updated').should('be.visible');
    cy.get('#alteration-expected-outcome').should('contain', newOutcome);
    cy.get('ul#alteration-events li').contains(newOutcome).should('be.visible');
  });

  it('should allow admin to add an origin', () => {
    const newOrigin = `http://github.localhost/user/repo${Date.now()}`;
    cy.alterSupportLogin();
    cy.visit(copyrightAlterationAdminUrl);

    // click the add origin button
    cy.get('div#origin-create').should('not.be.visible');
    cy.get('button').contains('Add an origin').click();
    cy.get('div#origin-create').should('be.visible');

    // fill the url, outcome & availability
    fillInput('div#origin-create #id_url', newOrigin);
    cy.get('div#origin-create #id_outcome').select('takedown');
    cy.get('div#origin-create #id_available').select('true');
    cy.get('div#origin-create').find('button[type=submit]').click();

    // redirected to the admin page with the new origin shown
    cy.location('pathname').should('be.equal', copyrightAlterationAdminUrl);
    cy.get('div.alert-success').contains(`Origin ${newOrigin}`).should('be.visible');
    cy.get('ul#alteration-events li').contains(newOrigin).should('be.visible');
    cy.get('table#alteration-origins tbody tr').last().within(() => {
      cy.get('[itemprop=url]').should('contain', newOrigin);
      cy.get('[itemprop=available]').should('contain', '✓');
      cy.get('[itemprop=outcome]').should('contain', 'Takedown');
    });
  });

  it('should allow admin to edit an origin', () => {
    const newReason = `Because ${Date.now()}`;
    cy.alterSupportLogin();
    cy.visit(copyrightAlterationAdminUrl);

    // click the edit button of the last origin
    cy.get('div.modal').should('not.be.visible');
    cy.get('table#alteration-origins tbody tr').last().find('button[aria-label=Edit]').click();
    cy.get('div.modal').should('be.visible');

    // set its reason, outcome & availability
    fillInput('div.modal.show #id_reason', newReason);
    cy.get('div.modal.show #id_outcome').select('block');
    cy.get('div.modal.show #id_available').select('true');
    cy.get('div.modal.show').find('button[type=submit]').click();

    // redirected to the admin page with the updated content shown
    cy.location('pathname').should('be.equal', copyrightAlterationAdminUrl);
    cy.get('div.alert-success').contains('has been updated').should('be.visible');
    cy.get('ul#alteration-events li').contains(newReason).should('be.visible');
    cy.get('table#alteration-origins tbody tr').last().within(() => {
      cy.get('[itemprop=reason]').should('contain', newReason);
      cy.get('[itemprop=available]').should('contain', '✓');
      cy.get('[itemprop=outcome]').should('contain', 'Takedown and block');
    });
  });

  it('should allow admin to edit an event', () => {
    const newContent = `Edited ${Date.now()}`;
    cy.alterSupportLogin();
    cy.visit(copyrightAlterationAdminUrl);

    // click the edit button of the first event
    cy.get('div.modal').should('not.be.visible');
    cy.get('ul#alteration-events li').first().find('button[aria-label=Edit]').click();
    cy.get('div.modal').should('be.visible');

    // change its content
    cy.get('div.alert-warning').contains('should be used sparingly').should('be.visible');
    fillInput('div.modal.show #id_content', newContent);
    cy.get('div.modal.show').find('button[type=submit]').click();

    // redirected to the admin page with the updated content shown
    cy.location('pathname').should('be.equal', copyrightAlterationAdminUrl);
    cy.get('div.alert-success').contains('Event updated').should('be.visible');
    cy.get('ul#alteration-events li').contains(newContent).should('be.visible');
  });

  it('should be able send an internal message to an admin role', () => {
    const messageContent = `My message to the legal role ${Date.now()}`;
    cy.alterSupportLogin();
    cy.visit(copyrightAlterationAdminUrl);

    // click the send message button
    cy.get('div.modal').should('not.be.visible');
    cy.get('button').contains('Send a message').click();
    cy.get('div.modal').should('be.visible');

    // choose legal recipient and fill the form
    cy.get('div.modal.show #id_recipient').select('legal');
    fillInput('div.modal.show #id_content', messageContent);
    cy.get('div.modal.show').find('button[type=submit]').click();

    // redirected to the admin page with the message shown in the activity log
    cy.location('pathname').should('be.equal', copyrightAlterationAdminUrl);
    cy.get('div.alert-success').contains('Message sent').should('be.visible');
    cy.get('ul#alteration-events li').first().within(() => {
      cy.get('[itemprop=text]').should('contain', messageContent);
      cy.get('[itemprop=sender]').should('contain', 'alter-support');
      cy.get('[itemprop=recipient]').should('contain', 'Legal');
      cy.get('[itemprop=conditionsOfAccess][title="Internal event"]').should('be.visible');
    });
    // an email to legal is sent with the whole message
    cy.task('findEmail', {subject: `New message on ${copyrightAlterationTitle}`, recipient: legalEmailAddress}).then((message) => {
      expect(message).to.contain(messageContent);
      const urls = extractUrls(message);
      // and a link to the alteration request
      expect(urls).to.have.lengthOf(1);
      expect(urls[0]).to.contain(copyrightAlterationAdminUrl);
    });
  });

  it('should be able send a message to the requester', () => {
    const messageContent = `My message to the requester ${Date.now()}`;
    cy.alterSupportLogin();
    cy.visit(copyrightAlterationAdminUrl);

    // click the send message button
    cy.get('div.modal').should('not.be.visible');
    cy.get('button').contains('Send a message').click();
    cy.get('div.modal').should('be.visible');

    // choose requester recipient and fill the form
    cy.get('div.modal.show #id_recipient').select('requester');
    fillInput('div.modal.show #id_content', messageContent);
    // uncheck internal, can't send an internal message to the requester
    cy.get('div.modal.show #id_internal').uncheck();
    cy.get('div.modal.show').find('button[type=submit]').click();

    // redirected to the admin page with the message shown in the activity log
    cy.location('pathname').should('be.equal', copyrightAlterationAdminUrl);
    cy.get('div.alert-success').contains('Message sent').should('be.visible');
    cy.get('ul#alteration-events li').first().within(() => {
      cy.get('[itemprop=text]').should('contain', messageContent);
      cy.get('[itemprop=sender]').should('contain', 'alter-support');
      cy.get('[itemprop=recipient]').should('contain', 'Requester');
      cy.get('[itemprop=conditionsOfAccess][title="Public event"]').should('be.visible');
    });
    // an email to the request is sent without the whole message
    cy.task('findEmail', {subject: 'New message notification', recipient: copyrightAlterationEmail}).then((message) => {
      expect(message).to.not.contain(messageContent);
      expect(message).to.contain('a new message');
      const urls = extractUrls(message);
      // and a link to the alteration request
      expect(urls).to.have.lengthOf(1);
      expect(urls[0]).to.contain(copyrightAlterationUrl);
    });
  });

  it('should be able send an internal message to the requester', () => {
    const messageContent = `My internal message to the requester ${Date.now()}`;
    cy.alterSupportLogin();
    cy.visit(copyrightAlterationAdminUrl);

    // click the send message button
    cy.get('button').contains('Send a message').click();

    // choose requester recipient and leave internal checked
    cy.get('div.modal.show #id_recipient').select('requester');
    fillInput('div.modal.show #id_content', messageContent);
    cy.get('div.modal.show #id_internal').should('be.checked'); // internal by default
    cy.get('div.modal.show').find('button[type=submit]').click();

    // redirected to the admin page with an error message and nothing in the event log
    cy.location('pathname').should('be.equal', copyrightAlterationAdminUrl);
    cy.get('div.alert-danger').contains("Can't send").should('be.visible');
    cy.get('ul#alteration-events li').first().should('not.contain', messageContent);
  });

});
