/**
 * Copyright (C) 2020  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

const username = 'admin';
const password = 'admin';

function login(username, password) {
  cy.get('input[name="username"]')
    .type(username)
    .get('input[name="password"]')
    .type(password)
    .get('form')
    .submit();
}

describe('Test admin deposit page', function() {
  it('Should test deposit page', function() {
    cy.visit(this.Urls.admin_deposit());
    // FIXME: cypress anti-pattern, do not use ui to log ¯\_(ツ)_/¯
    // https://docs.cypress.io/guides/getting-started/testing-your-app.html#Logging-in
    login(username, password);

    cy.server();
    let inputDeposits = [
      {
        'id': 614,
        'external_id': 'c-d-1',
        'reception_date': '2020-05-18T13:48:27Z',
        'status': 'done',
        'status_detail': 'all good',
        'swh_id': 'swh:1:dir:ef04a768',
        'swh_id_context': 'swh:1:dir:ef04a768;origin=https://w.s.o/c-d-1;visit=swh:1:snp:b234be1e;anchor=swh:1:rev:d24a75c9;path=/'
      },
      {
        'id': 613,
        'external_id': 'c-d-2',
        'reception_date': '2020-05-18T11:20:16Z',
        'status': 'done',
        'status_detail': 'everything is fine',
        'swh_id': 'swh:1:dir:181417fb',
        'swh_id_context': 'swh:1:dir:181417fb;origin=https://w.s.o/c-d-2;visit=swh:1:snp:8c32a2ef;anchor=swh:1:rev:3d1eba04;path=/'
      },
      {
        'id': 612,
        'external_id': 'c-d-3',
        'reception_date': '2020-05-18T11:20:16Z',
        'status': 'rejected',
        'status_detail': 'hu ho, issue!',
        'swh_id': null,
        'swh_id_context': null
      }
    ];
    cy.route({
      method: 'GET',
      url: `${this.Urls.admin_deposit_list()}**`,
      response: {
        'draw': 10,
        'recordsTotal': 3,
        'recordsFiltered': 3,
        'data': inputDeposits
      }
    }).as('listDeposits');

    cy.location('pathname')
      .should('be.equal', this.Urls.admin_deposit());
    cy.url().should('include', '/admin/deposit');

    cy.get('#swh-admin-deposit-list')
      .should('exist');

    // those are computed from the
    let expectedOrigins = ['https://w.s.o/c-d-1', 'https://w.s.o/c-d-2', ''];

    cy.wait('@listDeposits').then((xhr) => {
      cy.log('response:', xhr.response);
      cy.log(xhr.response.body);
      let deposits = xhr.response.body.data;
      cy.log('Deposits: ', deposits);
      expect(deposits.length).to.equal(inputDeposits.length);

      cy.get('#swh-admin-deposit-list').find('tbody > tr').as('rows');

      // only 2 entries
      cy.get('@rows').each((row, idx, collection) => {
        let deposit = deposits[idx];
        let inputDeposit = inputDeposits[idx];
        assert.isNotNull(deposit);
        assert.isNotNull(inputDeposit);
        expect(deposit.id).to.be.equal(inputDeposit['id']);
        expect(deposit.external_id).to.be.equal(inputDeposit['external_id']);
        expect(deposit.status).to.be.equal(inputDeposit['status']);
        expect(deposit.status_detail).to.be.equal(inputDeposit['status_detail']);
        expect(deposit.swh_id).to.be.equal(inputDeposit['swh_id']);
        expect(deposit.swh_id_context).to.be.equal(inputDeposit['swh_id_context']);

        let expectedOrigin = expectedOrigins[idx];
        // ensure it's in the dom
        expect(row).to.contain(deposit.id);
        if (deposit.status === 'done') {
          expect(row).to.contain(deposit.external_id);
        } else {
          expect(row).to.not.contain(deposit.external_id);
        }
        expect(row).to.contain(deposit.status);
        expect(row).to.contain(expectedOrigin);
        // those are hidden by default
        expect(row).to.not.contain(deposit.status_detail);
        expect(row).to.not.contain(deposit.swh_id);
        expect(row).to.not.contain(deposit.swh_id_context);
      });

      // toggling all links and ensure, the previous checks are inverted
      cy.get('a.toggle-col').click({'multiple': true}).then(() => {

        cy.get('#swh-admin-deposit-list').find('tbody > tr').as('rows');
        cy.get('@rows').each((row, idx, collection) => {
          let deposit = deposits[idx];

          // ensure it's in the dom
          expect(row).to.not.contain(deposit.id);
          if (deposit.status === 'done') {
            expect(row).to.contain(deposit.external_id);
          } else {
            expect(row).to.not.contain(deposit.external_id);
          }
          expect(row).to.not.contain(deposit.status);
          // those are hidden by default
          expect(row).to.contain(deposit.status_detail);
          if (deposit.swh_id !== null) {
            expect(row).to.contain(deposit.swh_id);
            expect(row).to.contain(deposit.swh_id_context);
          }
        });

      });

      cy.get('#swh-admin-deposit-list-error')
        .should('not.contain',
                'An error occurred while retrieving the list of deposits');
    });
  });
});
