/**
 * Copyright (C) 2019-2022  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

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

function getVaultItemList() {
  return JSON.parse(window.localStorage.getItem('swh-vault-cooking-tasks'));
}

function updateVaultItemList(vaultItems) {
  window.localStorage.setItem('swh-vault-cooking-tasks', JSON.stringify(vaultItems));
}

// Mocks API response : /api/1/vault/(:bundleType)/(:swhid)
// bundleType : {'flat', 'git_bare'}
function genVaultCookingResponse(bundleType, swhid, status, message, fetchUrl) {
  return {
    'bundle_type': bundleType,
    'id': 1,
    'progress_message': message,
    'status': status,
    'swhid': swhid,
    'fetch_url': fetchUrl
  };
};

// Tests progressbar color, status
// And status in localStorage
function testStatus(taskId, color, statusMsg, status) {
  cy.get(`.swh-vault-table #vault-task-${CSS.escape(taskId)}`)
    .should('be.visible')
    .find('.progress-bar')
    .should('be.visible')
    .and('have.css', 'background-color', color)
    .and('contain', statusMsg)
    .then(() => {
      // Vault item with object_id as taskId should exist in localStorage
      const currentVaultItems = getVaultItemList();
      const vaultItem = currentVaultItems.find(obj => obj.swhid === taskId);

      assert.isNotNull(vaultItem);
      assert.strictEqual(vaultItem.status, status);
    });
}

describe('Vault Cooking User Interface Tests', function() {

  before(function() {
    const dirInfo = this.origin[0].directory[0];
    this.directory = `swh:1:dir:${dirInfo.id}`;
    this.directoryUrl = this.Urls.browse_origin_directory() +
      `?origin_url=${this.origin[0].url}&path=${dirInfo.path}`;
    this.vaultDirectoryUrl = this.Urls.api_1_vault_cook_flat(this.directory);
    this.vaultDownloadDirectoryUrl = this.Urls.api_1_vault_download_flat(this.directory);

    this.revisionId = this.origin[1].revisions[0];
    this.revision = `swh:1:rev:${this.revisionId}`;
    this.revisionUrl = this.Urls.browse_revision(this.revisionId);
    this.vaultRevisionUrl = this.Urls.api_1_vault_cook_git_bare(this.revision);
    this.vaultDownloadRevisionUrl = this.Urls.api_1_vault_download_git_bare(this.revision);

    const release = this.origin[1].release;
    this.releaseUrl = this.Urls.browse_release(release.id) + `?origin_url=${this.origin[1].url}`;
    this.vaultReleaseDirectoryUrl = this.Urls.api_1_vault_cook_flat(`swh:1:dir:${release.directory}`);
  });

  beforeEach(function() {
    // For some reason, this gets reset if we define it in the before() hook,
    // so we need to define it here
    this.vaultItems = [
      {
        'bundle_type': 'git_bare',
        'swhid': this.revision,
        'email': '',
        'status': 'done',
        'fetch_url': `/api/1/vault/git-bare/${this.revision}/raw/`,
        'progress_message': null
      }
    ];
    this.legacyVaultItems = [
      {
        'object_type': 'revision',
        'object_id': this.revisionId,
        'email': '',
        'status': 'done',
        'fetch_url': `/api/1/vault/revision/${this.revisionId}/gitfast/raw/`,
        'progress_message': null
      }
    ];

    this.genVaultDirCookingResponse = (status, message = null) => {
      return genVaultCookingResponse('flat', this.directory, status,
                                     message, this.vaultDownloadDirectoryUrl);
    };

    this.genVaultRevCookingResponse = (status, message = null) => {
      return genVaultCookingResponse('git_bare', this.revision, status,
                                     message, this.vaultDownloadRevisionUrl);
    };

  });

  it('should report pending cooking task when already submitted', function() {
    // Browse a directory
    cy.visit(this.directoryUrl);

    // Stub responses when requesting the vault API to simulate
    // an internal server error
    cy.intercept(this.vaultDirectoryUrl, {
      body: this.genVaultDirCookingResponse('pending', 'Processing...')
    }).as('checkVaultCookingTask');

    cy.intercept('POST', this.vaultDirectoryUrl, {
      body: this.genVaultDirCookingResponse('pending', 'Processing...')
    }).as('createVaultCookingTask');

    cy.contains('button', 'Download')
      .click();

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
    cy.visit(this.Urls.vault());

    cy.wait('@checkVaultCookingTask').then(() => {
      testStatus(this.directory, progressbarColors['pending'], 'Processing...', 'pending');
    });

  });

  it('should report an error when vault service is experiencing issues', function() {
    // Browse a directory
    cy.visit(this.directoryUrl);

    // Stub responses when requesting the vault API to simulate
    // an internal server error
    cy.intercept(this.vaultDirectoryUrl, {
      body: {'exception': 'APIError'},
      statusCode: 500
    }).as('checkVaultCookingTask');

    cy.contains('button', 'Download')
      .click();

    // Check error alert is displayed
    cy.get('.alert-danger')
    .should('be.visible')
    .should('contain', 'Something unexpected happened when requesting the archive cooking service.');
  });

  it('should report an error when a cooking task creation failed', function() {

    // Browse a directory
    cy.visit(this.directoryUrl);

    // Stub responses when requesting the vault API to simulate
    // a task cannot be created
    cy.intercept('GET', this.vaultDirectoryUrl, {
      body: {'exception': 'NotFoundExc'}
    }).as('checkVaultCookingTask');

    cy.intercept('POST', this.vaultDirectoryUrl, {
      body: {'exception': 'ValueError'},
      statusCode: 500
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

  it('should display previous cooking tasks', function() {

    updateVaultItemList(this.vaultItems);

    cy.visit(this.Urls.vault());

    cy.contains(`#vault-task-${CSS.escape(this.revision)} button`, 'Download')
      .click();
  });

  it('should display and upgrade previous cooking tasks from the legacy format', function() {
    updateVaultItemList(this.legacyVaultItems);

    cy.visit(this.Urls.vault());

    // Check it is displayed
    cy.contains(`#vault-task-${CSS.escape(this.revision)} button`, 'Download')
      .then(() => {
        // Check the LocalStorage was upgraded
        expect(getVaultItemList()).to.deep.equal(this.vaultItems);
      });
  });

  it('should create a directory cooking task and report the success', function() {

    // Browse a directory
    cy.visit(this.directoryUrl);

    // Stub response to the vault API to simulate archive download
    cy.intercept('GET', this.vaultDownloadDirectoryUrl, {
      fixture: `${this.directory.replace(/:/g, '_')}.tar.gz`,
      headers: {
        'Content-disposition': `attachment; filename=${this.directory.replace(/:/g, '_')}.tar.gz`,
        'Content-Type': 'application/gzip'
      }
    }).as('fetchCookedArchive');

    // Stub responses when checking vault task status
    const checkVaulResponses = [
      {'exception': 'NotFoundExc'},
      this.genVaultDirCookingResponse('new'),
      this.genVaultDirCookingResponse('pending', 'Processing...'),
      this.genVaultDirCookingResponse('done')
    ];

    // trick to override the response of an intercepted request
    // https://github.com/cypress-io/cypress/issues/9302
    cy.intercept('GET', this.vaultDirectoryUrl, req => req.reply(checkVaulResponses.shift()))
      .as('checkVaultCookingTask');

    // Stub responses when requesting the vault API to simulate
    // a task has been created
    cy.intercept('POST', this.vaultDirectoryUrl, {
      body: this.genVaultDirCookingResponse('new')
    }).as('createVaultCookingTask');

    cy.contains('button', 'Download')
      .click();

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
      cy.visit(this.Urls.vault());

      cy.wait('@checkVaultCookingTask').then(() => {
        testStatus(this.directory, progressbarColors['new'], 'new', 'new');
      });

      cy.wait('@checkVaultCookingTask').then(() => {
        testStatus(this.directory, progressbarColors['pending'], 'Processing...', 'pending');
      });

      cy.wait('@checkVaultCookingTask').then(() => {
        testStatus(this.directory, progressbarColors['done'], 'done', 'done');
      });

      cy.get(`#vault-task-${CSS.escape(this.directory)} .vault-origin a`)
        .should('contain', this.origin[0].url)
        .should('have.attr', 'href', `${this.Urls.browse_origin()}?origin_url=${this.origin[0].url}`);

      cy.get(`#vault-task-${CSS.escape(this.directory)} .vault-object-info a`)
        .should('have.text', this.directory)
        .should('have.attr', 'href', browseDirectoryUrl);

      cy.get(`#vault-task-${CSS.escape(this.directory)}`)
        .invoke('attr', 'title')
        .should('contain', 'the directory can be extracted');

      cy.get(`#vault-task-${CSS.escape(this.directory)} .vault-dl-link button`)
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

    // Stub response to the vault API indicating to simulate archive download
    cy.intercept({url: this.vaultDownloadRevisionUrl}, {
      fixture: `${this.revision.replace(/:/g, '_')}.git.tar`,
      headers: {
        'Content-disposition': `attachment; filename=${this.revision.replace(/:/g, '_')}.git.tar`,
        'Content-Type': 'application/x-tar'
      }
    }).as('fetchCookedArchive');

    // Stub responses when checking vault task status
    const checkVaultResponses = [
      {'exception': 'NotFoundExc'},
      this.genVaultRevCookingResponse('new'),
      this.genVaultRevCookingResponse('pending', 'Processing...'),
      this.genVaultRevCookingResponse('done')
    ];

    // trick to override the response of an intercepted request
    // https://github.com/cypress-io/cypress/issues/9302
    cy.intercept('GET', this.vaultRevisionUrl, req => req.reply(checkVaultResponses.shift()))
      .as('checkVaultCookingTask');

    // Stub responses when requesting the vault API to simulate
    // a task has been created
    cy.intercept('POST', this.vaultRevisionUrl, {
      body: this.genVaultRevCookingResponse('new')
    }).as('createVaultCookingTask');

    // Create a vault cooking task through the GUI
    checkVaultCookingTask('as git');

    cy.window().then(win => {
      const swhIdsContext = win.swh.webapp.getSwhIdsContext();
      const browseRevisionUrl = swhIdsContext.revision.swhid_url;

      // Create a vault cooking task through the GUI
      cy.get('.modal.show #swh-vault-revision-email')
        .type('{enter}');

      cy.wait('@createVaultCookingTask');

      // Check success alert is displayed
      cy.get('.alert-success')
        .should('be.visible')
        .should('contain', 'Archive cooking request successfully submitted.');

      // Go to Downloads page
      cy.visit(this.Urls.vault());

      cy.wait('@checkVaultCookingTask').then(() => {
        testStatus(this.revision, progressbarColors['new'], 'new', 'new');
      });

      cy.wait('@checkVaultCookingTask').then(() => {
        testStatus(this.revision, progressbarColors['pending'], 'Processing...', 'pending');
      });

      cy.wait('@checkVaultCookingTask').then(() => {
        testStatus(this.revision, progressbarColors['done'], 'done', 'done');
      });

      cy.get(`#vault-task-${CSS.escape(this.revision)} .vault-origin`)
        .should('have.text', 'unknown');

      cy.get(`#vault-task-${CSS.escape(this.revision)} .vault-object-info a`)
        .should('have.text', this.revision)
        .should('have.attr', 'href', browseRevisionUrl);

      cy.get(`#vault-task-${CSS.escape(this.revision)}`)
        .invoke('attr', 'title')
        .should('contain', 'the git repository can be imported');

      cy.get(`#vault-task-${CSS.escape(this.revision)} .vault-dl-link button`)
        .click();

      cy.wait('@fetchCookedArchive').then((xhr) => {
        assert.isNotNull(xhr.response.body);
      });
    });
  });

  it('should create a directory cooking task from the release view', function() {

    // Browse a directory
    cy.visit(this.releaseUrl);

    // Stub responses when checking vault task status
    const checkVaultResponses = [
      {'exception': 'NotFoundExc'},
      this.genVaultDirCookingResponse('new')
    ];

    // trick to override the response of an intercepted request
    // https://github.com/cypress-io/cypress/issues/9302
    cy.intercept('GET', this.vaultReleaseDirectoryUrl, req => req.reply(checkVaultResponses.shift()))
      .as('checkVaultCookingTask');

    // Stub responses when requesting the vault API to simulate
    // a task has been created
    cy.intercept('POST', this.vaultReleaseDirectoryUrl, {
      body: this.genVaultDirCookingResponse('new')
    }).as('createVaultCookingTask');

    cy.contains('button', 'Download')
      .click();

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

  it('should create a directory cooking task with an email address', function() {
    // Browse a directory
    cy.visit(this.directoryUrl);

    // Stub responses when checking vault task status
    cy.intercept('GET', this.vaultDirectoryUrl, {body: {'exception': 'NotFoundExc'}})
      .as('checkVaultCookingTask');

    // Stub responses when requesting the vault API to simulate
    // a task has been created
    cy.intercept('POST', this.vaultDirectoryUrl + '?email=foo%2Bbar%40example.org', {
      body: this.genVaultDirCookingResponse('new')
    }).as('createVaultCookingTask');

    // Open vault cook directory modal
    cy.contains('button', 'Download')
      .click();

    cy.wait('@checkVaultCookingTask');

    // Create a vault cooking task through the GUI and fill email input
    cy.get('#vault-cook-directory-modal input[type="email"]')
      .type('foo+bar@example.org', {force: true});

    cy.get('#vault-cook-directory-modal')
      .contains('button:visible', 'Ok')
      .click();

    cy.wait('@createVaultCookingTask');

  });

  it('should offer to recook an archive if no longer available for download', function() {

    updateVaultItemList(this.vaultItems);

    // Send 404 when fetching vault item
    cy.intercept({url: this.vaultDownloadRevisionUrl}, {
      statusCode: 404,
      body: {
        'exception': 'NotFoundExc',
        'reason': `Revision with ID '${this.revision}' not found.`
      },
      headers: {
        'Content-Type': 'json'
      }
    }).as('fetchCookedArchive');

    cy.visit(this.Urls.vault())
      .get(`#vault-task-${CSS.escape(this.revision)} .vault-dl-link button`)
      .click();

    cy.wait('@fetchCookedArchive').then(() => {
      cy.intercept('POST', this.vaultRevisionUrl, {
        body: this.genVaultRevCookingResponse('new')
      }).as('createVaultCookingTask');

      cy.intercept(this.vaultRevisionUrl, {
        body: this.genVaultRevCookingResponse('new')
      }).as('checkVaultCookingTask');

      cy.get('#vault-recook-object-modal > .modal-dialog')
        .should('be.visible')
        .contains('button:visible', 'Ok')
        .click();

      cy.wait('@checkVaultCookingTask')
        .then(() => {
          testStatus(this.revision, progressbarColors['new'], 'new', 'new');
        });
    });
  });

  it('should offer to recook a tarball already cooked by another user but no longer in cache', function() {
    cy.visit(this.directoryUrl);

    // set bundle as already cooked
    cy.intercept(this.vaultDirectoryUrl, {
      body: this.genVaultDirCookingResponse('done')
    }).as('checkVaultCookingTask');

    // but no longer available in cache
    cy.intercept({url: this.vaultDownloadDirectoryUrl}, {
      statusCode: 404,
      body: {
        'exception': 'NotFoundExc',
        'reason': `Directory with ID '${this.directory}' not found.`
      },
      headers: {
        'Content-Type': 'json'
      }
    }).as('fetchCookedArchive');

    cy.intercept('POST', this.vaultDirectoryUrl, {
      body: this.genVaultDirCookingResponse('new')
    }).as('createVaultCookingTask');

    // request tarball download
    cy.contains('button', 'Download')
      .click();

    cy.wait('@checkVaultCookingTask');

    // vault backend indicated tarball was already cooked, download dialog is displayed
    cy.get('#vault-download-directory-modal')
      .should('be.visible')
      .contains('button:visible', 'Ok')
      .click();

    cy.wait('@fetchCookedArchive');

    // tarball is no longer in cache, recook dialog is displayed
    cy.get('#vault-recook-object-modal > .modal-dialog')
      .should('be.visible')
      .contains('button:visible', 'Ok')
      .click();

    // check new cooking request was sent
    cy.wait('@createVaultCookingTask');
  });

  it('should remove selected vault items', function() {

    updateVaultItemList(this.vaultItems);

    cy.visit(this.Urls.vault())
      .get(`#vault-task-${CSS.escape(this.revision)}`)
      .find('input[type="checkbox"]')
      .click({force: true});
    cy.contains('button', 'Remove selected tasks')
      .click();

    cy.get(`#vault-task-${CSS.escape(this.revision)}`)
      .should('not.exist');
  });

  it('should offer to immediately download a directory tarball if already cooked', function() {

    // Browse a directory
    cy.visit(this.directoryUrl);

    // Stub response to the vault API to simulate archive download
    cy.intercept({url: this.vaultDownloadDirectoryUrl}, {
      fixture: `${this.directory.replace(/:/g, '_')}.tar.gz`,
      headers: {
        'Content-disposition': `attachment; filename=${this.directory.replace(/:/g, '_')}.tar.gz`,
        'Content-Type': 'application/gzip'
      }
    }).as('fetchCookedArchive');

    // Stub responses when requesting the vault API to simulate
    // the directory tarball has already been cooked
    cy.intercept(this.vaultDirectoryUrl, {
      body: this.genVaultDirCookingResponse('done')
    }).as('checkVaultCookingTask');

    // Create a vault cooking task through the GUI
    cy.contains('button', 'Download')
      .click();

    // Start archive download through the GUI
    cy.get('.modal-dialog')
      .contains('button:visible', 'Ok')
      .click();

    cy.wait('@fetchCookedArchive');

  });

  it('should offer to immediately download a bare revision git archive if already cooked', function() {
    cy.adminLogin();
    // Browse a directory
    cy.visit(this.revisionUrl);

    // Stub response to the vault API to simulate archive download
    cy.intercept({url: this.vaultDownloadRevisionUrl}, {
      fixture: `${this.revision.replace(/:/g, '_')}.git.tar`,
      headers: {
        'Content-disposition': `attachment; filename=${this.revision.replace(/:/g, '_')}.git.tar`,
        'Content-Type': 'application/x-tar'
      }
    }).as('fetchCookedArchive');

    // Stub responses when requesting the vault API to simulate
    // the directory tarball has already been cooked
    cy.intercept(this.vaultRevisionUrl, {
      body: this.genVaultRevCookingResponse('done')
    }).as('checkVaultCookingTask');

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
    cy.intercept(this.vaultDirectoryUrl, {
      body: this.genVaultDirCookingResponse('failed')
    }).as('checkVaultCookingTask');

    cy.contains('button', 'Download')
      .click();

    // Check that recooking the directory is offered to user
    cy.get('.modal-dialog')
      .contains('button:visible', 'Ok')
      .should('be.visible');
  });

});
