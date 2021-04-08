/**
 * Copyright (C) 2018-2019  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import {handleFetchError, csrfPost, htmlAlert} from 'utils/functions';

const alertStyle = {
  'position': 'fixed',
  'left': '1rem',
  'bottom': '1rem',
  'z-index': '100000'
};

export function vaultRequest(objectType, objectId) {
  let vaultUrl;
  if (objectType === 'directory') {
    vaultUrl = Urls.api_1_vault_cook_directory(objectId);
  } else {
    vaultUrl = Urls.api_1_vault_cook_revision_gitfast(objectId);
  }
  // check if object has already been cooked
  fetch(vaultUrl)
    .then(response => response.json())
    .then(data => {
      // object needs to be cooked
      if (data.exception === 'NotFoundExc' || data.status === 'failed') {
        // if last cooking has failed, remove previous task info from localStorage
        // in order to force the recooking of the object
        swh.vault.removeCookingTaskInfo([objectId]);
        $(`#vault-cook-${objectType}-modal`).modal('show');
      // object has been cooked and should be in the vault cache,
      // it will be asked to cook it again if it is not
      } else if (data.status === 'done') {
        $(`#vault-fetch-${objectType}-modal`).modal('show');
      } else {
        const cookingServiceDownAlert =
          $(htmlAlert('danger',
                      'Archive cooking service is currently experiencing issues.<br/>' +
                      'Please try again later.',
                      true));
        cookingServiceDownAlert.css(alertStyle);
        $('body').append(cookingServiceDownAlert);
      }
    });
}

function addVaultCookingTask(cookingTask) {

  const swhidsContext = swh.webapp.getSwhIdsContext();
  cookingTask.origin = swhidsContext[cookingTask.object_type].context.origin;
  cookingTask.path = swhidsContext[cookingTask.object_type].context.path;
  cookingTask.browse_url = swhidsContext[cookingTask.object_type].swhid_with_context_url;
  if (!cookingTask.browse_url) {
    cookingTask.browse_url = swhidsContext[cookingTask.object_type].swhid_url;
  }

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
      cookingUrl = Urls.api_1_vault_cook_directory(cookingTask.object_id);
    } else {
      cookingUrl = Urls.api_1_vault_cook_revision_gitfast(cookingTask.object_id);
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
        const cookingTaskCreatedAlert =
          $(htmlAlert('success',
                      'Archive cooking request successfully submitted.<br/>' +
                      `Go to the <a href="${Urls.browse_vault()}">Downloads</a> page ` +
                      'to get the download link once it is ready.',
                      true));
        cookingTaskCreatedAlert.css(alertStyle);
        $('body').append(cookingTaskCreatedAlert);
      })
      .catch(() => {
        $('#vault-cook-directory-modal').modal('hide');
        $('#vault-cook-revision-modal').modal('hide');
        const cookingTaskFailedAlert =
          $(htmlAlert('danger',
                      'Archive cooking request submission failed.',
                      true));
        cookingTaskFailedAlert.css(alertStyle);
        $('body').append(cookingTaskFailedAlert);
      });
  }
}

function validateEmail(email) {
  let re = /^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
  return re.test(String(email).toLowerCase());
}

export function cookDirectoryArchive(directoryId) {
  let email = $('#swh-vault-directory-email').val().trim();
  if (!email || validateEmail(email)) {
    let cookingTask = {
      'object_type': 'directory',
      'object_id': directoryId,
      'email': email,
      'status': 'new'
    };
    addVaultCookingTask(cookingTask);

  } else {
    $('#invalid-email-modal').modal('show');
  }
}

export function fetchDirectoryArchive(directoryId) {
  $('#vault-fetch-directory-modal').modal('hide');
  const vaultUrl = Urls.api_1_vault_cook_directory(directoryId);
  fetch(vaultUrl)
    .then(response => response.json())
    .then(data => {
      swh.vault.fetchCookedObject(data.fetch_url);
    });
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

export function fetchRevisionArchive(revisionId) {
  $('#vault-fetch-directory-modal').modal('hide');
  const vaultUrl = Urls.api_1_vault_cook_revision_gitfast(revisionId);
  fetch(vaultUrl)
    .then(response => response.json())
    .then(data => {
      swh.vault.fetchCookedObject(data.fetch_url);
    });
}
