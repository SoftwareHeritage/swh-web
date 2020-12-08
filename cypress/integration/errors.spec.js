/**
 * Copyright (C) 2019-2020  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

let origin;

const invalidChecksum = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa';

const invalidPageUrl = '/invalidPath';

function urlShouldShowError(url, error) {
  cy.visit(url, {
    failOnStatusCode: false
  });
  cy.get('.swh-http-error')
    .should('be.visible');
  cy.get('.swh-http-error-code')
    .should('contain', error.code);
  cy.get('.swh-http-error-desc')
    .should('contain', error.msg);
}

describe('Test Errors', function() {
  before(function() {
    origin = this.origin[0];
  });

  it('should show navigation buttons on error page', function() {
    cy.visit(invalidPageUrl, {
      failOnStatusCode: false
    });
    cy.get('a[onclick="window.history.back();"]')
      .should('be.visible');
    cy.get('a[href="/"')
      .should('be.visible');
  });

  context('For unarchived repositories', function() {
    it('should display NotFoundExc for unarchived repo', function() {
      const url = `${this.Urls.browse_origin_directory()}?origin_url=${this.unarchivedRepo.url}`;

      urlShouldShowError(url, {
        code: '404',
        msg: 'NotFoundExc: Origin with url ' + this.unarchivedRepo.url + ' not found!'
      });
    });

    it('should display NotFoundExc for unarchived content', function() {
      const url = this.Urls.browse_content(`sha1_git:${this.unarchivedRepo.content[0].sha1git}`);

      urlShouldShowError(url, {
        code: '404',
        msg: 'NotFoundExc: Content with sha1_git checksum equals to ' + this.unarchivedRepo.content[0].sha1git + ' not found!'
      });
    });

    it('should display NotFoundExc for unarchived directory sha1git', function() {
      const url = this.Urls.browse_directory(this.unarchivedRepo.rootDirectory);

      urlShouldShowError(url, {
        code: '404',
        msg: 'NotFoundExc: Directory with sha1_git ' + this.unarchivedRepo.rootDirectory + ' not found'
      });
    });

    it('should display NotFoundExc for unarchived revision sha1git', function() {
      const url = this.Urls.browse_revision(this.unarchivedRepo.revision);

      urlShouldShowError(url, {
        code: '404',
        msg: 'NotFoundExc: Revision with sha1_git ' + this.unarchivedRepo.revision + ' not found.'
      });
    });

    it('should display NotFoundExc for unarchived snapshot sha1git', function() {
      const url = this.Urls.browse_snapshot(this.unarchivedRepo.snapshot);

      urlShouldShowError(url, {
        code: '404',
        msg: 'Snapshot with id ' + this.unarchivedRepo.snapshot + ' not found!'
      });
    });

  });

  context('For archived repositories', function() {
    before(function() {
      const url = `${this.Urls.browse_origin_directory()}?origin_url=${origin.url}`;
      cy.visit(url);
    });

    it('should display NotFoundExc for invalid directory from archived repo', function() {
      const subDir = `${this.Urls.browse_origin_directory()}?origin_url=${origin.url}&path=${origin.invalidSubDir}`;

      urlShouldShowError(subDir, {
        code: '404',
        msg: 'NotFoundExc: Directory entry with path ' +
              origin.invalidSubDir + ' from root directory ' +
              origin.rootDirectory + ' not found'
      });
    });

    it(`should display NotFoundExc for incorrect origin_url
        with correct content hash`, function() {
      const url = this.Urls.browse_content(`sha1_git:${origin.content[0].sha1git}`) +
                  `?origin_url=${this.unarchivedRepo.url}`;
      urlShouldShowError(url, {
        code: '404',
        msg: 'The Software Heritage archive has a content ' +
            'with the hash you provided but the origin ' +
            'mentioned in your request appears broken: ' +
            this.unarchivedRepo.url + '. ' +
            'Please check the URL and try again.\n\n' +
            'Nevertheless, you can still browse the content ' +
            'without origin information: ' +
            '/browse/content/sha1_git:' +
            origin.content[0].sha1git + '/'
      });
    });
  });

  context('For invalid data', function() {
    it(`should display 400 for invalid checksum for
        directory, snapshot, revision, content`, function() {
      const types = ['directory', 'snapshot', 'revision', 'content'];
      for (let type of types) {
        const url = this.Urls[`browse_${type}`](invalidChecksum);
        urlShouldShowError(url, {
          code: '400',
          msg: 'BadInputExc: Invalid checksum query string ' +
                invalidChecksum
        });
      }
    });

    it('should show 404 error for invalid path', function() {
      urlShouldShowError(invalidPageUrl, {
        code: '404',
        msg: 'The resource ' + invalidPageUrl +
            ' could not be found on the server.'
      });
    });
  });
});
