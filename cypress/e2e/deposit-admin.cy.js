/**
 * Copyright (C) 2020-2022  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

// data to use as request query response
let responseDeposits;
let expectedOrigins;
let depositModerationUrl;
let depositListUrl;

const $ = Cypress.$;

describe('Test moderation deposit Login/logout', function() {
  before(function() {
    depositModerationUrl = this.Urls.admin_deposit();
  });

  it('should not display deposit moderation link in sidebar when anonymous', function() {
    cy.visit(depositModerationUrl);
    cy.get(`.sidebar a[href="${depositModerationUrl}"]`)
      .should('not.exist');
  });

  it('should not display deposit moderation link when connected as unprivileged user', function() {
    cy.userLogin();
    cy.visit(depositModerationUrl);

    cy.get(`.sidebar a[href="${depositModerationUrl}"]`)
      .should('not.exist');

  });

  it('should display deposit moderation link in sidebar when connected as privileged user', function() {
    cy.depositLogin();
    cy.visit(depositModerationUrl);

    cy.get(`.sidebar a[href="${depositModerationUrl}"]`)
      .should('exist');
  });

  it('should display deposit moderation link in sidebar when connected as staff member', function() {
    cy.adminLogin();
    cy.visit(depositModerationUrl);

    cy.get(`.sidebar a[href="${depositModerationUrl}"]`)
      .should('exist');
  });

});

describe('Test admin deposit page', function() {
  before(function() {
    depositModerationUrl = this.Urls.admin_deposit();
    depositListUrl = this.Urls.admin_deposit_list();
  });

  beforeEach(() => {
    responseDeposits = [
      {
        'id': 614,
        'type': 'code',
        'external_id': 'ch-de-1',
        'reception_date': '2020-05-18T13:48:27Z',
        'status': 'done',
        'status_detail': null,
        'swhid': 'swh:1:dir:ef04a768',
        'swhid_context': 'swh:1:dir:ef04a768;origin=https://w.s.o/c-d-1;visit=swh:1:snp:b234be1e;anchor=swh:1:rev:d24a75c9;path=/',
        'raw_metadata': '<foo>bar</foo>',
        'uri': 'https://w.s.o/c-d-1'
      },
      {
        'id': 613,
        'type': 'code',
        'external_id': 'ch-de-2',
        'reception_date': '2020-05-18T11:20:16Z',
        'status': 'done',
        'status_detail': null,
        'swhid': 'swh:1:dir:181417fb',
        'swhid_context': 'swh:1:dir:181417fb;origin=https://w.s.o/c-d-2;visit=swh:1:snp:8c32a2ef;anchor=swh:1:rev:3d1eba04;path=/',
        'raw_metadata': null,
        'uri': 'https://w.s.o/c-d-2'
      },
      {
        'id': 612,
        'type': 'code',
        'external_id': 'ch-de-3',
        'reception_date': '2020-05-18T11:20:16Z',
        'status': 'rejected',
        'status_detail': 'incomplete deposit!',
        'swhid': null,
        'swhid_context': null,
        'raw_metadata': null,
        'uri': null
      }
    ];
    // those are computed from the
    expectedOrigins = {
      614: 'https://w.s.o/c-d-1',
      613: 'https://w.s.o/c-d-2',
      612: ''
    };

  });

  it('Should properly display entries', function() {
    cy.adminLogin();

    const testDeposits = responseDeposits;
    cy.intercept(`${depositListUrl}**`, {
      body: {
        'draw': 10,
        'recordsTotal': testDeposits.length,
        'recordsFiltered': testDeposits.length,
        'data': testDeposits
      }
    }).as('listDeposits');

    cy.visit(depositModerationUrl);

    cy.location('pathname')
      .should('be.equal', depositModerationUrl);

    cy.get('#swh-admin-deposit-list')
      .should('exist');

    cy.wait('@listDeposits').then((xhr) => {
      cy.log('response:', xhr.response);
      cy.log(xhr.response.body);
      const deposits = xhr.response.body.data;
      cy.log('Deposits: ', deposits);
      expect(deposits.length).to.equal(testDeposits.length);

      cy.get('#swh-admin-deposit-list').find('tbody > tr').as('rows');

      // only 2 entries
      cy.get('@rows').each((row, idx, collection) => {
        const cells = row[0].cells;
        const deposit = deposits[idx];
        const responseDeposit = testDeposits[idx];
        assert.isNotNull(deposit);
        assert.isNotNull(responseDeposit);
        expect(deposit.id).to.be.equal(responseDeposit['id']);
        expect(deposit.uri).to.be.equal(responseDeposit['uri']);
        expect(deposit.type).to.be.equal(responseDeposit['type']);
        expect(deposit.external_id).to.be.equal(responseDeposit['external_id']);
        expect(deposit.status).to.be.equal(responseDeposit['status']);
        expect(deposit.status_detail).to.be.equal(responseDeposit['status_detail']);
        expect(deposit.swhid).to.be.equal(responseDeposit['swhid']);
        expect(deposit.swhid_context).to.be.equal(responseDeposit['swhid_context']);

        const expectedOrigin = expectedOrigins[deposit.id];
        // ensure it's in the dom
        cy.contains(deposit.id).should('be.visible');
        if (deposit.status !== 'rejected') {
          expect(row).to.not.contain(deposit.external_id);
          cy.contains(expectedOrigin).should('be.visible');
        }

        if (deposit.uri && deposit.swhid_context) {
          let html = `<a href="${this.Urls.browse_swhid(deposit.swhid_context)}">${deposit.uri}</a>`;
          html += `&nbsp;<a href="${deposit.uri}" target="_blank" rel="noopener noreferrer">`;
          html += '<i class="mdi mdi-open-in-new" aria-hidden="true"></i></a>';
          expect($(cells[2]).html()).to.contain(html);
        } else if (!deposit.uri) {
          expect($(cells[2]).text().trim()).to.equal('');
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

        if (deposit.raw_metadata !== null) {
          cy.get('button.metadata', {withinSubject: row})
            .should('exist')
            .should('have.text', 'display')
            .click({force: true});
          cy.get('#swh-web-modal-html code.xml').should('be.visible');

          // Dismiss the modal
          cy.get('body').wait(500).type('{esc}');
          cy.get('#swh-web-modal-html code.xml').should('not.be.visible');
        } else {
          cy.get('button.metadata', {withinSubject: row}).should('not.exist');
          cy.get('#swh-web-modal-html code.xml').should('not.be.visible');
        }

      });

      // toggling all links and ensure, the previous checks are inverted
      cy.get('a.toggle-col').click({'multiple': true}).then(() => {
        cy.get('#swh-admin-deposit-list').find('tbody > tr').as('rows');

        cy.get('@rows').each((row, idx, collection) => {
          const deposit = deposits[idx];
          const expectedOrigin = expectedOrigins[deposit.id];

          // ensure it's in the dom
          expect(row).to.not.contain(deposit.id);
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
