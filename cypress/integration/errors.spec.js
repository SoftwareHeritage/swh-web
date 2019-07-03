/**
 * Copyright (C) 2019  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import {httpGetJson} from '../utils';

const unarchivedRepo = {
  url: 'https://github.com/SoftwareHeritage/swh-web',
  revisionSha1git: '7bf1b2f489f16253527807baead7957ca9e8adde',
  snapshotSha1git: 'd9829223095de4bb529790de8ba4e4813e38672d',
  rootDirSha1git: '7d887d96c0047a77e2e8c4ee9bb1528463677663',
  readmeSha1git: 'b203ec39300e5b7e97b6e20986183cbd0b797859'
};

const archivedRepo = {
  url: 'https://github.com/memononen/libtess2',
  invalidSubDir: 'Source1'
};

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

describe('Test Errors for unarchived repositories', function() {
  it('should display NotFoundExc for unarchived repo', function() {
    const url = this.Urls.browse_origin_directory(unarchivedRepo.url);

    urlShouldShowError(url, {
      code: '404',
      msg: 'NotFoundExc: Origin with url ' + unarchivedRepo.url + ' not found!'
    });
  });

  it('should display NotFoundExc for unarchived content', function() {
    const url = this.Urls.browse_content(`sha1_git:${unarchivedRepo.readmeSha1git}`);

    urlShouldShowError(url, {
      code: '404',
      msg: 'NotFoundExc: Content with sha1_git checksum equals to ' + unarchivedRepo.readmeSha1git + ' not found!'
    });
  });

  it('should display NotFoundExc for unarchived directory sha1git', function() {
    const url = this.Urls.browse_directory(unarchivedRepo.rootDirSha1git);

    urlShouldShowError(url, {
      code: '404',
      msg: 'NotFoundExc: Directory with sha1_git ' + unarchivedRepo.rootDirSha1git + ' not found'
    });
  });

  it('should display NotFoundExc for unarchived revision sha1git', function() {
    const url = this.Urls.browse_revision(unarchivedRepo.revisionSha1git);

    urlShouldShowError(url, {
      code: '404',
      msg: 'NotFoundExc: Revision with sha1_git ' + unarchivedRepo.revisionSha1git + ' not found.'
    });
  });

  it('should display NotFoundExc for unarchived snapshot sha1git', function() {
    const url = this.Urls.browse_snapshot(unarchivedRepo.snapshotSha1git);

    urlShouldShowError(url, {
      code: '404',
      msg: 'Snapshot with id ' + unarchivedRepo.snapshotSha1git + ' not found!'
    });
  });

});

describe('Test Errors for archived repositories', function() {
  before(function() {
    const url = this.Urls.browse_origin_directory(archivedRepo.url);
    cy.visit(url);
    cy.window().then(async win => {
      const metadata = win.swh.webapp.getBrowsedSwhObjectMetadata();
      const apiUrl = Cypress.config().baseUrl + this.Urls.api_1_directory(metadata.directory);
      const dirContent = await httpGetJson(apiUrl);

      archivedRepo.contentSha1git = dirContent.find(x => x.type === 'file').checksums.sha1_git;
      archivedRepo.directorySha1git = metadata.directory;
    });
  });

  it('should display NotFoundExc for invalid directory from archived repo', function() {
    const rootDir = this.Urls.browse_origin_directory(archivedRepo.url);
    const subDir = rootDir + archivedRepo.invalidSubDir;

    urlShouldShowError(subDir, {
      code: '404',
      msg: 'NotFoundExc: Directory entry with path ' +
            archivedRepo.invalidSubDir + ' from ' +
            archivedRepo.directorySha1git + ' not found'
    });
  });

  it(`should display NotFoundExc for incorrect origin_url
      with correct content hash`, function() {
    const url = this.Urls.browse_content(`sha1_git:${archivedRepo.contentSha1git}`) +
                `?origin_url=${unarchivedRepo.url}`;
    urlShouldShowError(url, {
      code: '404',
      msg: 'The Software Heritage archive has a content ' +
           'with the hash you provided but the origin ' +
           'mentioned in your request appears broken: ' +
           unarchivedRepo.url + '. ' +
           'Please check the URL and try again.\n\n' +
           'Nevertheless, you can still browse the content ' +
           'without origin information: ' +
           '/browse/content/sha1_git:' +
           archivedRepo.contentSha1git + '/'
    });
  });
});

describe('Test errors for invalid data', function() {
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
