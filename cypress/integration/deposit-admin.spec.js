/**
 * Copyright (C) 2020  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

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
        'swhid': 'swh:1:dir:ef04a768',
        'swhid_context': 'swh:1:dir:ef04a768;origin=https://w.s.o/c-d-1;visit=swh:1:snp:b234be1e;anchor=swh:1:rev:d24a75c9;path=/'
      },
      {
        'id': 613,
        'external_id': 'ch-de-2',
        'reception_date': '2020-05-18T11:20:16Z',
        'status': 'done',
        'status_detail': null,
        'swhid': 'swh:1:dir:181417fb',
        'swhid_context': 'swh:1:dir:181417fb;origin=https://w.s.o/c-d-2;visit=swh:1:snp:8c32a2ef;anchor=swh:1:rev:3d1eba04;path=/'
      },
      {
        'id': 612,
        'external_id': 'ch-de-3',
        'reception_date': '2020-05-18T11:20:16Z',
        'status': 'rejected',
        'status_detail': 'incomplete deposit!',
        'swhid': null,
        'swhid_context': null
      }
    ];
    // those are computed from the
    expectedOrigins = {
      614: 'https://w.s.o/c-d-1',
      613: 'https://w.s.o/c-d-2',
      612: ''
    };

  });

  it('Should display properly entries', function() {
    cy.adminLogin();
    cy.visit(this.Urls.admin_deposit());

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
        expect(deposit.swhid).to.be.equal(responseDeposit['swhid']);
        expect(deposit.swhid_context).to.be.equal(responseDeposit['swhid_context']);

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
          cy.contains(deposit.status_detail).should('not.exist');
        }

        // those are hidden by default
        if (deposit.swhid !== null) {
          cy.contains(deposit.swhid).should('not.exist');
          cy.contains(deposit.swhid_context).should('not.exist');
        }
      });

      // toggling all links and ensure, the previous checks are inverted
      cy.get('a.toggle-col').click({'multiple': true}).then(() => {
        cy.get('#swh-admin-deposit-list').find('tbody > tr').as('rows');

        cy.get('@rows').each((row, idx, collection) => {
          let deposit = deposits[idx];
          let expectedOrigin = expectedOrigins[deposit.id];

          // ensure it's in the dom
          cy.contains(deposit.id).should('not.exist');
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
          if (deposit.swhid !== null) {
            cy.contains(deposit.swhid).should('be.visible');
            cy.contains(deposit.swhid_context).should('be.visible');
            // check SWHID link text formatting
            cy.contains(deposit.swhid_context).then(elt => {
              expect(elt[0].innerHTML).to.equal(deposit.swhid_context.replace(/;/g, ';<br>'));
            });
          }
        });
      });

      cy.get('#swh-admin-deposit-list-error')
        .should('not.contain',
                'An error occurred while retrieving the list of deposits');
    });

  });
});
