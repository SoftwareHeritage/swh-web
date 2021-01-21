/**
 * Copyright (C) 2019-2020  The Software Heritage developers
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
  cy.contains('button', 'Download')
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
    const dirInfo = this.origin[0].directory[0];
    this.directory = dirInfo.id;
    this.directoryUrl = this.Urls.browse_origin_directory() +
      `?origin_url=${this.origin[0].url}&path=${dirInfo.path}`;
    this.vaultDirectoryUrl = this.Urls.api_1_vault_cook_directory(this.directory);
    this.vaultFetchDirectoryUrl = this.Urls.api_1_vault_fetch_directory(this.directory);

    this.revision = this.origin[1].revisions[0];
    this.revisionUrl = this.Urls.browse_revision(this.revision);
    this.vaultRevisionUrl = this.Urls.api_1_vault_cook_revision_gitfast(this.revision);
    this.vaultFetchRevisionUrl = this.Urls.api_1_vault_fetch_revision_gitfast(this.revision);

    const release = this.origin[1].release;
    this.releaseUrl = this.Urls.browse_release(release.id) + `?origin_url=${this.origin[1].url}`;
    this.vaultReleaseDirectoryUrl = this.Urls.api_1_vault_cook_directory(release.directory);

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

  it('should report an error when vault service is experiencing issues', function() {
    // Browse a directory
    cy.visit(this.directoryUrl);

    // Stub responses when requesting the vault API to simulate
    // an internal server error
    cy.route({
      method: 'GET',
      url: this.vaultDirectoryUrl,
      response: {'exception': 'APIError'},
      status: 500
    }).as('checkVaultCookingTask');

    cy.contains('button', 'Download')
      .click();

    // Check error alert is displayed
    cy.get('.alert-danger')
    .should('be.visible')
    .should('contain', 'Archive cooking service is currently experiencing issues.');
  });

  it('should report an error when a cooking task creation failed', function() {

    // Browse a directory
    cy.visit(this.directoryUrl);

    // Stub responses when requesting the vault API to simulate
    // a task can not be created
    cy.route({
      method: 'GET',
      url: this.vaultDirectoryUrl,
      response: {'exception': 'NotFoundExc'}
    }).as('checkVaultCookingTask');

    cy.route({
      method: 'POST',
      url: this.vaultDirectoryUrl,
      response: {'exception': 'ValueError'},
      status: 500
    }).as('createVaultCookingTask');

    cy.contains('button', 'Download')
      .click();

    // Create a vault cooking task through the GUI
    cy.get('.modal-dialog')
      .contains('button:visible', 'Ok')
      .click();

    cy.wait('@createVaultCookingTask');

    // Check error alert is displayed
    cy.get('.alert-danger')
      .should('be.visible')
      .should('contain', 'Archive cooking request submission failed.');
  });

  it('should create a directory cooking task and report the success', function() {

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

    cy.contains('button', 'Download')
      .click();

    cy.route({
      method: 'GET',
      url: this.vaultDirectoryUrl,
      response: this.genVaultDirCookingResponse('new')
    }).as('checkVaultCookingTask');

    cy.window().then(win => {
      const swhIdsContext = win.swh.webapp.getSwhIdsContext();
      const browseDirectoryUrl = swhIdsContext.directory.swhid_with_context_url;

      // Create a vault cooking task through the GUI
      cy.get('.modal-dialog')
        .contains('button:visible', 'Ok')
        .click();

      cy.wait('@createVaultCookingTask');

      // Check success alert is displayed
      cy.get('.alert-success')
        .should('be.visible')
        .should('contain', 'Archive cooking request successfully submitted.');

      // Go to Downloads page
      cy.visit(this.Urls.browse_vault());

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
        response: `fx:${this.directory}.tar.gz`,
        headers: {
          'Content-disposition': `attachment; filename=${this.directory}.tar.gz`,
          'Content-Type': 'application/gzip'
        }
      }).as('fetchCookedArchive');

      cy.get(`#vault-task-${this.directory} .vault-origin a`)
        .should('contain', this.origin[0].url)
        .should('have.attr', 'href', `${this.Urls.browse_origin()}?origin_url=${this.origin[0].url}`);

      cy.get(`#vault-task-${this.directory} .vault-object-info a`)
        .should('have.text', this.directory)
        .should('have.attr', 'href', browseDirectoryUrl);

      cy.get(`#vault-task-${this.directory} .vault-dl-link button`)
        .click();

      cy.wait('@fetchCookedArchive').then((xhr) => {
        assert.isNotNull(xhr.response.body);
      });
    });
  });

  it('should create a revision cooking task and report its status', function() {
    cy.adminLogin();

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

    cy.window().then(win => {
      const swhIdsContext = win.swh.webapp.getSwhIdsContext();
      const browseRevisionUrl = swhIdsContext.revision.swhid_url;

      // Create a vault cooking task through the GUI
      cy.get('.modal-dialog')
        .contains('button:visible', 'Ok')
        .click();

      cy.wait('@createVaultCookingTask');

      // Check success alert is displayed
      cy.get('.alert-success')
        .should('be.visible')
        .should('contain', 'Archive cooking request successfully submitted.');

      // Go to Downloads page
      cy.visit(this.Urls.browse_vault());

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
        response: `fx:${this.revision}.gitfast.gz`,
        headers: {
          'Content-disposition': `attachment; filename=${this.revision}.gitfast.gz`,
          'Content-Type': 'application/gzip'
        }
      }).as('fetchCookedArchive');

      cy.get(`#vault-task-${this.revision} .vault-origin`)
        .should('have.text', 'unknown');

      cy.get(`#vault-task-${this.revision} .vault-object-info a`)
        .should('have.text', this.revision)
        .should('have.attr', 'href', browseRevisionUrl);

      cy.get(`#vault-task-${this.revision} .vault-dl-link button`)
        .click();

      cy.wait('@fetchCookedArchive').then((xhr) => {
        assert.isNotNull(xhr.response.body);
      });
    });
  });

  it('should create a directory cooking task from the release view', function() {

    // Browse a directory
    cy.visit(this.releaseUrl);

    // Stub responses when requesting the vault API to simulate
    // a task has been created
    cy.route({
      method: 'GET',
      url: this.vaultReleaseDirectoryUrl,
      response: {'exception': 'NotFoundExc'}
    }).as('checkVaultCookingTask');

    cy.route({
      method: 'POST',
      url: this.vaultReleaseDirectoryUrl,
      response: this.genVaultDirCookingResponse('new')
    }).as('createVaultCookingTask');

    cy.contains('button', 'Download')
      .click();

    cy.route({
      method: 'GET',
      url: this.vaultReleaseDirectoryUrl,
      response: this.genVaultDirCookingResponse('new')
    }).as('checkVaultCookingTask');

    // Create a vault cooking task through the GUI
    cy.get('.modal-dialog')
        .contains('button:visible', 'Ok')
        .click();

    cy.wait('@createVaultCookingTask');

    // Check success alert is displayed
    cy.get('.alert-success')
        .should('be.visible')
        .should('contain', 'Archive cooking request successfully submitted.');
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
      .click({force: true});
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
      response: `fx:${this.directory}.tar.gz`,
      headers: {
        'Content-disposition': `attachment; filename=${this.directory}.tar.gz`,
        'Content-Type': 'application/gzip'
      }
    }).as('fetchCookedArchive');

    // Create a vault cooking task through the GUI
    cy.contains('button', 'Download')
      .click();

    // Start archive download through the GUI
    cy.get('.modal-dialog')
      .contains('button:visible', 'Ok')
      .click();

    cy.wait('@fetchCookedArchive');

  });

  it('should offer to immediately download a revision gitfast archive if already cooked', function() {
    cy.adminLogin();
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
      response: `fx:${this.revision}.gitfast.gz`,
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

  it('should offer to recook an object if previous vault task failed', function() {

    cy.visit(this.directoryUrl);

    // Stub responses when requesting the vault API to simulate
    // the last cooking of the directory tarball has failed
    cy.route({
      method: 'GET',
      url: this.vaultDirectoryUrl,
      response: this.genVaultDirCookingResponse('failed')
    }).as('checkVaultCookingTask');

    cy.contains('button', 'Download')
      .click();

    // Check that recooking the directory is offered to user
    cy.get('.modal-dialog')
      .contains('button:visible', 'Ok')
      .should('be.visible');
  });

});
