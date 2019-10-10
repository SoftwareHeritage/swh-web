/**
 * Copyright (C) 2019  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

let vaultItems = [];

const progressbarColors = {
  'new': 'rgba(128, 128, 128, 0.5)',
  'pending': 'rgba(0, 0, 255, 0.5)',
  'done': 'rgb(92, 184, 92)'
};

function checkVaultCookingTask(objectType) {
  cy.contains('button', 'Actions')
    .click();

  cy.contains('.dropdown-item', 'Download')
    .click();

  cy.contains('.dropdown-item', objectType)
    .click();

  cy.wait('@checkVaultCookingTask');
}

function updateVaultItemList(vaultUrl, vaultItems) {
  cy.visit(vaultUrl)
    .then(() => {
      // Add uncooked task to localStorage
      // which updates it in vault items list
      window.localStorage.setItem('swh-vault-cooking-tasks', JSON.stringify(vaultItems));
    });
}

// Mocks API response : /api/1/vault/(:objectType)/(:hash)
// objectType : {'directory', 'revision'}
function genVaultCookingResponse(objectType, objectId, status, message, fetchUrl) {
  return {
    'obj_type': objectType,
    'id': 1,
    'progress_message': message,
    'status': status,
    'obj_id': objectId,
    'fetch_url': fetchUrl
  };
};

// Tests progressbar color, status
// And status in localStorage
function testStatus(taskId, color, statusMsg, status) {
  cy.get(`.swh-vault-table #vault-task-${taskId}`)
    .should('be.visible')
    .find('.progress-bar')
    .should('be.visible')
    .and('have.css', 'background-color', color)
    .and('contain', statusMsg)
    .then(() => {
      // Vault item with object_id as taskId should exist in localStorage
      const currentVaultItems = JSON.parse(window.localStorage.getItem('swh-vault-cooking-tasks'));
      const vaultItem = currentVaultItems.find(obj => obj.object_id === taskId);

      assert.isNotNull(vaultItem);
      assert.strictEqual(vaultItem.status, status);
    });
}

describe('Vault Cooking User Interface Tests', function() {

  before(function() {
    this.directory = this.origin[0].directory[0].id;
    this.directoryUrl = this.Urls.browse_directory(this.directory);
    this.vaultDirectoryUrl = this.Urls.api_1_vault_cook_directory(this.directory);
    this.vaultFetchDirectoryUrl = this.Urls.api_1_vault_fetch_directory(this.directory);

    this.revision = this.origin[1].revisions[0];
    this.revisionUrl = this.Urls.browse_revision(this.revision);
    this.vaultRevisionUrl = this.Urls.api_1_vault_cook_revision_gitfast(this.revision);
    this.vaultFetchRevisionUrl = this.Urls.api_1_vault_fetch_revision_gitfast(this.revision);

    vaultItems[0] = {
      'object_type': 'revision',
      'object_id': this.revision,
      'email': '',
      'status': 'done',
      'fetch_url': `/api/1/vault/revision/${this.revision}/gitfast/raw/`,
      'progress_message': null
    };
  });

  beforeEach(function() {
    this.genVaultDirCookingResponse = (status, message = null) => {
      return genVaultCookingResponse('directory', this.directory, status,
                                     message, this.vaultFetchDirectoryUrl);
    };

    this.genVaultRevCookingResponse = (status, message = null) => {
      return genVaultCookingResponse('revision', this.revision, status,
                                     message, this.vaultFetchRevisionUrl);
    };

    cy.server();
  });

  it('should create a directory cooking task and report its status', function() {

    // Browse a directory
    cy.visit(this.directoryUrl);

    // Stub responses when requesting the vault API to simulate
    // a task has been created

    cy.route({
      method: 'GET',
      url: this.vaultDirectoryUrl,
      response: {'exception': 'NotFoundExc'}
    }).as('checkVaultCookingTask');

    cy.route({
      method: 'POST',
      url: this.vaultDirectoryUrl,
      response: this.genVaultDirCookingResponse('new')
    }).as('createVaultCookingTask');

    checkVaultCookingTask('as tarball');

    cy.route({
      method: 'GET',
      url: this.vaultDirectoryUrl,
      response: this.genVaultDirCookingResponse('new')
    }).as('checkVaultCookingTask');

    // Create a vault cooking task through the GUI
    cy.get('.modal-dialog')
      .contains('button:visible', 'Ok')
      .click();

    cy.wait('@createVaultCookingTask');

    // Check that a redirection to the vault UI has been performed
    cy.url().should('eq', Cypress.config().baseUrl + this.Urls.browse_vault());

    cy.wait('@checkVaultCookingTask').then(() => {
      testStatus(this.directory, progressbarColors['new'], 'new', 'new');
    });

    // Stub response to the vault API indicating the task is processing
    cy.route({
      method: 'GET',
      url: this.vaultDirectoryUrl,
      response: this.genVaultDirCookingResponse('pending', 'Processing...')
    }).as('checkVaultCookingTask');

    cy.wait('@checkVaultCookingTask').then(() => {
      testStatus(this.directory, progressbarColors['pending'], 'Processing...', 'pending');
    });

    // Stub response to the vault API indicating the task is finished
    cy.route({
      method: 'GET',
      url: this.vaultDirectoryUrl,
      response: this.genVaultDirCookingResponse('done')
    }).as('checkVaultCookingTask');

    cy.wait('@checkVaultCookingTask').then(() => {
      testStatus(this.directory, progressbarColors['done'], 'done', 'done');
    });

    // Stub response to the vault API to simulate archive download
    cy.route({
      method: 'GET',
      url: this.vaultFetchDirectoryUrl,
      response: `fx:${this.directory}.tar.gz,binary`,
      headers: {
        'Content-disposition': `attachment; filename=${this.directory}.tar.gz`,
        'Content-Type': 'application/gzip'
      }
    }).as('fetchCookedArchive');

    cy.get(`#vault-task-${this.directory} .vault-dl-link button`)
      .click();

    cy.wait('@fetchCookedArchive').then((xhr) => {
      assert.isNotNull(xhr.response.body);
    });

  });

  it('should create a revision cooking task and report its status', function() {
    // Browse a revision
    cy.visit(this.revisionUrl);

    // Stub responses when requesting the vault API to simulate
    // a task has been created

    cy.route({
      method: 'GET',
      url: this.vaultRevisionUrl,
      response: {'exception': 'NotFoundExc'}
    }).as('checkVaultCookingTask');

    cy.route({
      method: 'POST',
      url: this.vaultRevisionUrl,
      response: this.genVaultRevCookingResponse('new')
    }).as('createVaultCookingTask');

    // Create a vault cooking task through the GUI
    checkVaultCookingTask('as git');

    cy.route({
      method: 'GET',
      url: this.vaultRevisionUrl,
      response: this.genVaultRevCookingResponse('new')
    }).as('checkVaultCookingTask');

    // Create a vault cooking task through the GUI
    cy.get('.modal-dialog')
      .contains('button:visible', 'Ok')
      .click();

    cy.wait('@createVaultCookingTask');

    // Check that a redirection to the vault UI has been performed
    cy.url().should('eq', Cypress.config().baseUrl + this.Urls.browse_vault());

    cy.wait('@checkVaultCookingTask').then(() => {
      testStatus(this.revision, progressbarColors['new'], 'new', 'new');
    });

    // Stub response to the vault API indicating the task is processing
    cy.route({
      method: 'GET',
      url: this.vaultRevisionUrl,
      response: this.genVaultRevCookingResponse('pending', 'Processing...')
    }).as('checkVaultCookingTask');

    cy.wait('@checkVaultCookingTask').then(() => {
      testStatus(this.revision, progressbarColors['pending'], 'Processing...', 'pending');
    });

    // Stub response to the vault API indicating the task is finished
    cy.route({
      method: 'GET',
      url: this.vaultRevisionUrl,
      response: this.genVaultRevCookingResponse('done')
    }).as('checkVaultCookingTask');

    cy.wait('@checkVaultCookingTask').then(() => {
      testStatus(this.revision, progressbarColors['done'], 'done', 'done');
    });

    // Stub response to the vault API indicating to simulate archive
    // download
    cy.route({
      method: 'GET',
      url: this.vaultFetchRevisionUrl,
      response: `fx:${this.revision}.gitfast.gz,binary`,
      headers: {
        'Content-disposition': `attachment; filename=${this.revision}.gitfast.gz`,
        'Content-Type': 'application/gzip'
      }
    }).as('fetchCookedArchive');

    cy.get(`#vault-task-${this.revision} .vault-dl-link button`)
      .click();

    cy.wait('@fetchCookedArchive').then((xhr) => {
      assert.isNotNull(xhr.response.body);
    });
  });

  it('should offer to recook an archive if no more available to download', function() {

    updateVaultItemList(this.Urls.browse_vault(), vaultItems);

    // Send 404 when fetching vault item
    cy.route({
      method: 'GET',
      status: 404,
      url: this.vaultFetchRevisionUrl,
      response: {
        'exception': 'NotFoundExc',
        'reason': `Revision with ID '${this.revision}' not found.`
      },
      headers: {
        'Content-Type': 'json'
      }
    }).as('fetchCookedArchive');

    cy.get(`#vault-task-${this.revision} .vault-dl-link button`)
      .click();

    cy.wait('@fetchCookedArchive').then(() => {
      cy.route({
        method: 'POST',
        url: this.vaultRevisionUrl,
        response: this.genVaultRevCookingResponse('new')
      }).as('createVaultCookingTask');

      cy.route({
        method: 'GET',
        url: this.vaultRevisionUrl,
        response: this.genVaultRevCookingResponse('new')
      }).as('checkVaultCookingTask');

      cy.get('#vault-recook-object-modal > .modal-dialog')
        .should('be.visible')
        .contains('button:visible', 'Ok')
        .click();

      cy.wait('@createVaultCookingTask')
        .wait('@checkVaultCookingTask')
        .then(() => {
          testStatus(this.revision, progressbarColors['new'], 'new', 'new');
        });
    });
  });

  it('should remove selected vault items', function() {

    updateVaultItemList(this.Urls.browse_vault(), vaultItems);

    cy.get(`#vault-task-${this.revision}`)
      .find('input[type="checkbox"]')
      .click();
    cy.contains('button', 'Remove selected tasks')
      .click();

    cy.get(`#vault-task-${this.revision}`)
      .should('not.exist');
  });

  it('should offer to immediately download a directory tarball if already cooked', function() {

    // Browse a directory
    cy.visit(this.directoryUrl);

    // Stub responses when requesting the vault API to simulate
    // the directory tarball has already been cooked
    cy.route({
      method: 'GET',
      url: this.vaultDirectoryUrl,
      response: this.genVaultDirCookingResponse('done')
    }).as('checkVaultCookingTask');

    // Stub response to the vault API to simulate archive download
    cy.route({
      method: 'GET',
      url: this.vaultFetchDirectoryUrl,
      response: `fx:${this.directory}.tar.gz,binary`,
      headers: {
        'Content-disposition': `attachment; filename=${this.directory}.tar.gz`,
        'Content-Type': 'application/gzip'
      }
    }).as('fetchCookedArchive');

    // Create a vault cooking task through the GUI
    checkVaultCookingTask('as tarball');

    // Start archive download through the GUI
    cy.get('.modal-dialog')
      .contains('button:visible', 'Ok')
      .click();

    cy.wait('@fetchCookedArchive');

  });

  it('should offer to immediately download a revision gitfast archive if already cooked', function() {

    // Browse a directory
    cy.visit(this.revisionUrl);

    // Stub responses when requesting the vault API to simulate
    // the directory tarball has already been cooked
    cy.route({
      method: 'GET',
      url: this.vaultRevisionUrl,
      response: this.genVaultRevCookingResponse('done')
    }).as('checkVaultCookingTask');

    // Stub response to the vault API to simulate archive download
    cy.route({
      method: 'GET',
      url: this.vaultFetchRevisionUrl,
      response: `fx:${this.revision}.gitfast.gz,binary`,
      headers: {
        'Content-disposition': `attachment; filename=${this.revision}.gitfast.gz`,
        'Content-Type': 'application/gzip'
      }
    }).as('fetchCookedArchive');

    checkVaultCookingTask('as git');

    // Start archive download through the GUI
    cy.get('.modal-dialog')
      .contains('button:visible', 'Ok')
      .click();

    cy.wait('@fetchCookedArchive');

  });

});
