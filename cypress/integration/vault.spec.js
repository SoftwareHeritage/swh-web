/**
 * Copyright (C) 2019  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

function createVaultCookingTask(objectType) {
  cy.contains('button', 'Actions')
    .click();

  cy.contains('.dropdown-item', 'Download')
    .click();

  cy.contains('.dropdown-item', objectType)
    .click();

  cy.get('.modal-dialog')
    .contains('button', 'Ok')
    .click();
}

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

describe('Vault Cooking User Interface Tests', function() {

  before(function() {
    this.directory = this.origin[0].directory[0].id;
    this.directoryUrl = this.Urls.browse_directory(this.directory);
    this.vaultDirectoryUrl = this.Urls.api_1_vault_cook_directory(this.directory);
    this.vaultFetchDirectoryUrl = this.Urls.api_1_vault_fetch_directory(this.directory);
    this.genVaultDirCookingResponse = (status, message = null) => {
      return genVaultCookingResponse('directory', this.directory, status,
                                     message, this.vaultFetchDirectoryUrl);
    };

    this.revision = this.origin[1].revision[0];
    this.revisionUrl = this.Urls.browse_revision(this.revision);
    this.vaultRevisionUrl = this.Urls.api_1_vault_cook_revision_gitfast(this.revision);
    this.vaultFetchRevisionUrl = this.Urls.api_1_vault_fetch_revision_gitfast(this.revision);
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
      method: 'POST',
      url: this.vaultDirectoryUrl,
      response: this.genVaultDirCookingResponse('new')
    }).as('createVaultCookingTask');

    cy.route({
      method: 'GET',
      url: this.vaultDirectoryUrl,
      response: this.genVaultDirCookingResponse('new')
    }).as('checkVaultCookingTask');

    // Create a vault cooking task through the GUI
    createVaultCookingTask('Directory');

    cy.wait('@createVaultCookingTask');

    // Check that a redirection to the vault UI has been performed
    cy.url().should('eq', Cypress.config().baseUrl + this.Urls.browse_vault());

    cy.wait('@checkVaultCookingTask');

    // TODO: - check that a row has been created for the task in
    //         the displayed table
    //
    //       - check progress bar state and color

    // Stub response to the vault API indicating the task is processing
    cy.route({
      method: 'GET',
      url: this.vaultDirectoryUrl,
      response: this.genVaultDirCookingResponse('pending', 'Processing...')
    }).as('checkVaultCookingTask');

    cy.wait('@checkVaultCookingTask');

    // TODO: check progress bar state and color

    // Stub response to the vault API indicating the task is finished
    cy.route({
      method: 'GET',
      url: this.vaultDirectoryUrl,
      response: this.genVaultDirCookingResponse('done')
    }).as('checkVaultCookingTask');

    cy.wait('@checkVaultCookingTask');

    // TODO: check progress bar state and color and that the download
    //       button appeared

    // Stub response to the vault API indicating to simulate archive
    // download
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
    // TODO: The above test must be factorized to handle the revision cooking test
  });

  it('should offer to recook an archive if no more available to download', function() {
    // TODO:
    //  - Simulate an already executed task by filling the 'swh-vault-cooking-tasks'
    //    entry in browser localStorage (see vault-ui.js).
    //
    //  - Stub the response to the archive fetch url to return a 404 error.
    //
    //  - Check that the dialog offering to recook the archive is displayed
    //    and that the cooking task can be created from it.
  });

});
