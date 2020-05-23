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

// data to use as request query response
let responseDeposits;
let expectedOrigins;

describe('Test admin deposit page', function() {
  beforeEach(() => {
    responseDeposits = [
      {
        'id': 614,
        'external_id': 'ch-de-1',
        'reception_date': '2020-05-18T13:48:27Z',
        'status': 'done',
        'status_detail': null,
        'swh_id': 'swh:1:dir:ef04a768',
        'swh_id_context': 'swh:1:dir:ef04a768;origin=https://w.s.o/c-d-1;visit=swh:1:snp:b234be1e;anchor=swh:1:rev:d24a75c9;path=/'
      },
      {
        'id': 613,
        'external_id': 'ch-de-2',
        'reception_date': '2020-05-18T11:20:16Z',
        'status': 'done',
        'status_detail': null,
        'swh_id': 'swh:1:dir:181417fb',
        'swh_id_context': 'swh:1:dir:181417fb;origin=https://w.s.o/c-d-2;visit=swh:1:snp:8c32a2ef;anchor=swh:1:rev:3d1eba04;path=/'
      },
      {
        'id': 612,
        'external_id': 'ch-de-3',
        'reception_date': '2020-05-18T11:20:16Z',
        'status': 'rejected',
        'status_detail': 'incomplete deposit!',
        'swh_id': null,
        'swh_id_context': null
      }
    ];
    // those are computed from the
    expectedOrigins = {
      614: 'https://w.s.o/c-d-1',
      613: 'https://w.s.o/c-d-2',
      612: ''
    };

  });

  it('Should filter out deposits matching excluding pattern from display', function() {
    cy.visit(this.Urls.admin_deposit());
    // FIXME: cypress anti-pattern, do not use ui to log ¯\_(ツ)_/¯
    // https://docs.cypress.io/guides/getting-started/testing-your-app.html#Logging-in
    login(username, password);

    cy.server();

    // entry supposed to be excluded from the display by default
    let extraDeposit = {
      'id': 10,
      'external_id': 'check-deposit-3',
      'reception_date': '2020-05-18T11:20:16Z',
      'status': 'done',
      'status_detail': null,
      'swh_id': 'swh:1:dir:fb234417',
      'swh_id_context': 'swh:1:dir:fb234417;origin=https://w.s.o/c-d-3;visit=swh:1:snp:181417fb;anchor=swh:1:rev:3d166604;path=/'
    };

    // of course, that's how to copy a list (an "array")
    let testDeposits = responseDeposits.slice();
    // and add a new element to that array by mutating it...
    testDeposits.push(extraDeposit);
    expectedOrigins[10] = 'https://w.s.o/c-d-3';

    // ensure we don't touch the original reference
    expect(responseDeposits.length).to.be.equal(3);
    expect(testDeposits.length).to.be.equal(4);

    cy.route({
      method: 'GET',
      url: `${this.Urls.admin_deposit_list()}**`,
      response: {
        'draw': 10,
        'recordsTotal': testDeposits.length,
        'recordsFiltered': testDeposits.length,
        'data': testDeposits
      }
    }).as('listDeposits');

    cy.location('pathname')
      .should('be.equal', this.Urls.admin_deposit());
    cy.url().should('include', '/admin/deposit');

    cy.get('#swh-admin-deposit-list')
      .should('exist');

    cy.wait('@listDeposits').then((xhr) => {
      let deposits = xhr.response.body.data;
      expect(deposits.length).to.equal(testDeposits.length);

      cy.get('#swh-admin-deposit-list').find('tbody > tr').as('rows');

      // only 2 entries
      cy.get('@rows').each((row, idx, collection) => {
        let deposit = deposits[idx];
        let responseDeposit = testDeposits[idx];
        cy.log('deposit', deposit);
        cy.log('responseDeposit', responseDeposit);
        expect(deposit.id).to.be.equal(responseDeposit['id']);
        expect(deposit.external_id).to.be.equal(responseDeposit['external_id']);
        expect(deposit.status).to.be.equal(responseDeposit['status']);
        expect(deposit.status_detail).to.be.equal(responseDeposit['status_detail']);
        expect(deposit.swh_id).to.be.equal(responseDeposit['swh_id']);
        expect(deposit.swh_id_context).to.be.equal(responseDeposit['swh_id_context']);

        let expectedOrigin = expectedOrigins[deposit.id];

        // part of the data, but it should not be displayed (got filtered out)
        if (deposit.external_id === 'check-deposit-3') {
          cy.contains(deposit.status).should('not.be.visible');
          cy.contains(deposit.status_detail).should('not.be.visible');
          cy.contains(deposit.external_id).should('not.be.visible');
          cy.contains(expectedOrigin).should('not.be.visible');
          cy.contains(deposit.swh_id).should('not.be.visible');
          cy.contains(deposit.swh_id_context).should('not.be.visible');
        } else {
          expect(deposit.external_id).to.be.not.equal('check-deposit-3');
          cy.contains(deposit.id).should('be.visible');
          if (deposit.status !== 'rejected') {
            cy.contains(deposit.external_id).should('not.be.visible');
            cy.contains(expectedOrigin).should('be.visible');
            // ensure it's in the dom
          }
          cy.contains(deposit.status).should('be.visible');
          // those are hidden by default, so now visible
          if (deposit.status_detail !== null) {
            cy.contains(deposit.status_detail).should('not.be.visible');
          }

          // those are hidden by default
          if (deposit.swh_id !== null) {
            cy.contains(deposit.swh_id).should('not.be.visible');
            cy.contains(deposit.swh_id_context).should('not.be.visible');
          }
        }
      });

      // toggling all links and ensure, the previous checks are inverted
      cy.get('a.toggle-col').click({'multiple': true}).then(() => {
        cy.get('#swh-admin-deposit-list').find('tbody > tr').as('rows');

        cy.get('@rows').should('have.length', 3);

        cy.get('@rows').each((row, idx, collection) => {
          let deposit = deposits[idx];
          let expectedOrigin = expectedOrigins[deposit.id];

          // filtered out deposit
          if (deposit.external_id === 'check-deposit-3') {
            cy.contains(deposit.status).should('not.be.visible');
            cy.contains(deposit.status_detail).should('not.be.visible');
            cy.contains(deposit.external_id).should('not.be.visible');
            cy.contains(expectedOrigin).should('not.be.visible');
            cy.contains(deposit.swh_id).should('not.be.visible');
            cy.contains(deposit.swh_id_context).should('not.be.visible');
          } else {
            expect(deposit.external_id).to.be.not.equal('check-deposit-3');
            // ensure it's in the dom
            cy.contains(deposit.id).should('not.be.visible');
            if (deposit.status !== 'rejected') {
              cy.contains(deposit.external_id).should('not.be.visible');
              expect(row).to.contain(expectedOrigin);
            }

            expect(row).to.not.contain(deposit.status);
            // those are hidden by default, so now visible
            if (deposit.status_detail !== null) {
              cy.contains(deposit.status_detail).should('be.visible');
            }

            // those are hidden by default, so now they should be visible
            if (deposit.swh_id !== null) {
              cy.contains(deposit.swh_id).should('be.visible');
              cy.contains(deposit.swh_id_context).should('be.visible');
            }
          }
        });
      });

      cy.get('#swh-admin-deposit-list-error')
        .should('not.contain',
                'An error occurred while retrieving the list of deposits');
    });

  });

  it('Should display properly entries', function() {
    cy.visit(this.Urls.admin_deposit());
    // FIXME: cypress anti-pattern, do not use ui to log ¯\_(ツ)_/¯
    // https://docs.cypress.io/guides/getting-started/testing-your-app.html#Logging-in
    login(username, password);

    let testDeposits = responseDeposits;

    cy.server();
    cy.route({
      method: 'GET',
      url: `${this.Urls.admin_deposit_list()}**`,
      response: {
        'draw': 10,
        'recordsTotal': testDeposits.length,
        'recordsFiltered': testDeposits.length,
        'data': testDeposits
      }
    }).as('listDeposits');

    cy.location('pathname')
      .should('be.equal', this.Urls.admin_deposit());
    cy.url().should('include', '/admin/deposit');

    cy.get('#swh-admin-deposit-list')
      .should('exist');

    cy.wait('@listDeposits').then((xhr) => {
      cy.log('response:', xhr.response);
      cy.log(xhr.response.body);
      let deposits = xhr.response.body.data;
      cy.log('Deposits: ', deposits);
      expect(deposits.length).to.equal(testDeposits.length);

      cy.get('#swh-admin-deposit-list').find('tbody > tr').as('rows');

      // only 2 entries
      cy.get('@rows').each((row, idx, collection) => {
        let deposit = deposits[idx];
        let responseDeposit = testDeposits[idx];
        assert.isNotNull(deposit);
        assert.isNotNull(responseDeposit);
        expect(deposit.id).to.be.equal(responseDeposit['id']);
        expect(deposit.external_id).to.be.equal(responseDeposit['external_id']);
        expect(deposit.status).to.be.equal(responseDeposit['status']);
        expect(deposit.status_detail).to.be.equal(responseDeposit['status_detail']);
        expect(deposit.swh_id).to.be.equal(responseDeposit['swh_id']);
        expect(deposit.swh_id_context).to.be.equal(responseDeposit['swh_id_context']);

        let expectedOrigin = expectedOrigins[deposit.id];
        // ensure it's in the dom
        cy.contains(deposit.id).should('be.visible');
        if (deposit.status !== 'rejected') {
          expect(row).to.not.contain(deposit.external_id);
          cy.contains(expectedOrigin).should('be.visible');
        }

        cy.contains(deposit.status).should('be.visible');
        // those are hidden by default, so now visible
        if (deposit.status_detail !== null) {
          cy.contains(deposit.status_detail).should('not.be.visible');
        }

        // those are hidden by default
        if (deposit.swh_id !== null) {
          cy.contains(deposit.swh_id).should('not.be.visible');
          cy.contains(deposit.swh_id_context).should('not.be.visible');
        }
      });

      // toggling all links and ensure, the previous checks are inverted
      cy.get('a.toggle-col').click({'multiple': true}).then(() => {
        cy.get('#swh-admin-deposit-list').find('tbody > tr').as('rows');

        cy.get('@rows').each((row, idx, collection) => {
          let deposit = deposits[idx];
          let expectedOrigin = expectedOrigins[deposit.id];

          // ensure it's in the dom
          cy.contains(deposit.id).should('not.be.visible');
          if (deposit.status !== 'rejected') {
            expect(row).to.not.contain(deposit.external_id);
            expect(row).to.contain(expectedOrigin);
          }

          expect(row).to.not.contain(deposit.status);
          // those are hidden by default, so now visible
          if (deposit.status_detail !== null) {
            cy.contains(deposit.status_detail).should('be.visible');
          }

          // those are hidden by default, so now they should be visible
          if (deposit.swh_id !== null) {
            cy.contains(deposit.swh_id).should('be.visible');
            cy.contains(deposit.swh_id_context).should('be.visible');
          }
        });
      });

      cy.get('#swh-admin-deposit-list-error')
        .should('not.contain',
                'An error occurred while retrieving the list of deposits');
    });

  });
});
