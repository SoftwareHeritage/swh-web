/**
 * Copyright (C) 2018  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import {handleFetchError, csrfPost} from 'utils/functions';

function addVaultCookingTask(cookingTask) {
  let vaultCookingTasks = JSON.parse(localStorage.getItem('swh-vault-cooking-tasks'));
  if (!vaultCookingTasks) {
    vaultCookingTasks = [];
  }
  if (vaultCookingTasks.find(val => {
    return val.object_type === cookingTask.object_type &&
            val.object_id === cookingTask.object_id;
  }) === undefined) {
    let cookingUrl;
    if (cookingTask.object_type === 'directory') {
      cookingUrl = Urls.api_vault_cook_directory(cookingTask.object_id);
    } else {
      cookingUrl = Urls.api_vault_cook_revision_gitfast(cookingTask.object_id);
    }
    if (cookingTask.email) {
      cookingUrl += '?email=' + cookingTask.email;
    }
    csrfPost(cookingUrl)
      .then(handleFetchError)
      .then(() => {
        vaultCookingTasks.push(cookingTask);
        localStorage.setItem('swh-vault-cooking-tasks', JSON.stringify(vaultCookingTasks));
        $('#vault-cook-directory-modal').modal('hide');
        $('#vault-cook-revision-modal').modal('hide');
        window.location = Urls.browse_vault();
      })
      .catch(() => {
        $('#vault-cook-directory-modal').modal('hide');
        $('#vault-cook-revision-modal').modal('hide');
      });
  } else {
    window.location = Urls.browse_vault();
  }
}

function validateEmail(email) {
  let re = /^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
  return re.test(String(email).toLowerCase());
}

export function cookDirectoryArchive(directoryId) {
  let email = $('#swh-vault-directory-email').val().trim();
  if (!email || validateEmail(email)) {
    let cookingTask = {'object_type': 'directory',
      'object_id': directoryId,
      'email': email,
      'status': 'new'};
    addVaultCookingTask(cookingTask);

  } else {
    $('#invalid-email-modal').modal('show');
  }
}

export function cookRevisionArchive(revisionId) {
  let email = $('#swh-vault-revision-email').val().trim();
  if (!email || validateEmail(email)) {
    let cookingTask = {
      'object_type': 'revision',
      'object_id': revisionId,
      'email': email,
      'status': 'new'
    };
    addVaultCookingTask(cookingTask);
  } else {
    $('#invalid-email-modal').modal('show');
  }
}

export function initTaskCreationUi() {

  // reparent the modals to the top navigation div in order to be able
  // to display them
  $(document).ready(function() {
    $('.swh-browse-top-navigation').append($('#vault-cook-directory-modal'));
    $('.swh-browse-top-navigation').append($('#vault-cook-revision-modal'));
    $('.swh-browse-top-navigation').append($('#invalid-email-modal'));
  });

}
