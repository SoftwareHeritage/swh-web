/**
 * Copyright (C) 2018-2022  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import * as EmailValidator from 'email-validator';

import {csrfPost, handleFetchError, htmlAlert} from 'utils/functions';

const alertStyle = {
  'position': 'fixed',
  'left': '1rem',
  'bottom': '1rem',
  'z-index': '100000'
};

export function displayCookingTaskCreatedAlert() {
  const cookingTaskCreatedAlert =
    $(htmlAlert('success',
                'Archive cooking request successfully submitted.<br/>' +
                      `Go to the <a class="alert-link" href="${Urls.vault()}">Downloads</a> page ` +
                      'to get the download link once it is ready.',
                true));
  cookingTaskCreatedAlert.css(alertStyle);
  $('body').append(cookingTaskCreatedAlert);
}

export function displayCookingTaskCreationFailedAlert() {
  const cookingTaskFailedAlert =
      $(htmlAlert('danger',
                  'Archive cooking request submission failed.',
                  true));
  cookingTaskFailedAlert.css(alertStyle);
  $('body').append(cookingTaskFailedAlert);
}

export async function vaultRequest(objectType, swhid) {
  let vaultUrl;
  if (objectType === 'directory') {
    vaultUrl = Urls.api_1_vault_cook_flat(swhid);
  } else {
    vaultUrl = Urls.api_1_vault_cook_git_bare(swhid);
  }
  // check if object has already been cooked
  const response = await fetch(vaultUrl);
  const data = await response.json();

  // object needs to be cooked
  const statusForCooking = ['failed', 'pending', 'new'];
  if (data.exception === 'NotFoundExc' || statusForCooking.includes(data.status)) {
    // if last cooking has failed, remove previous task info from localStorage
    // in order to force the recooking of the object
    swh.vault.removeCookingTaskInfo([swhid]);
    const vaultModalId = `#vault-cook-${objectType}-modal`;
    $(vaultModalId).modal('show');
  } else if (data.status === 'done') {
    // object has been cooked but is no longer in the vault cache,
    // it will be asked to cook it again
    const vaultModalId = `#vault-download-${objectType}-modal`;
    $(vaultModalId).modal('show');
  } else {
    const cookingServiceDownAlert =
          $(htmlAlert('danger',
                      'Something unexpected happened when requesting the archive cooking service.<br/>' +
                      'Please try again later.',
                      true));
    cookingServiceDownAlert.css(alertStyle);
    $('body').append(cookingServiceDownAlert);
  }
}

async function addVaultCookingTask(objectType, cookingTask) {

  const swhidsContext = swh.webapp.getSwhIdsContext();
  cookingTask.origin = swhidsContext[objectType].context.origin;
  cookingTask.path = swhidsContext[objectType].context.path;
  cookingTask.browse_url = swhidsContext[objectType].swhid_with_context_url;
  if (!cookingTask.browse_url) {
    cookingTask.browse_url = swhidsContext[objectType].swhid_url;
  }

  let vaultCookingTasks = JSON.parse(localStorage.getItem('swh-vault-cooking-tasks'));
  if (!vaultCookingTasks) {
    vaultCookingTasks = [];
  }
  if (vaultCookingTasks.find(val => {
    return val.bundle_type === cookingTask.bundle_type &&
            val.swhid === cookingTask.swhid;
  }) === undefined) {
    let cookingUrl;
    if (cookingTask.bundle_type === 'flat') {
      cookingUrl = Urls.api_1_vault_cook_flat(cookingTask.swhid);
    } else {
      cookingUrl = Urls.api_1_vault_cook_git_bare(cookingTask.swhid);
    }
    if (cookingTask.email) {
      cookingUrl += '?email=' + encodeURIComponent(cookingTask.email);
    }

    try {
      const response = await csrfPost(cookingUrl);
      handleFetchError(response);
      vaultCookingTasks.push(cookingTask);
      localStorage.setItem('swh-vault-cooking-tasks', JSON.stringify(vaultCookingTasks));
      $('#vault-cook-directory-modal').modal('hide');
      $('#vault-cook-revision-modal').modal('hide');
      displayCookingTaskCreatedAlert();
    } catch (_) {
      $('#vault-cook-directory-modal').modal('hide');
      $('#vault-cook-revision-modal').modal('hide');
      displayCookingTaskCreationFailedAlert();
    }
  }
}

export function cookDirectoryArchive(event, swhid) {
  if (event) {
    event.preventDefault();
  }
  const email = $('#swh-vault-directory-email').val().trim();
  if (!email || EmailValidator.validate(email)) {
    const cookingTask = {
      'bundle_type': 'flat',
      'swhid': swhid,
      'email': email,
      'status': 'new'
    };
    addVaultCookingTask('directory', cookingTask);

  } else {
    $('#invalid-email-modal').modal('show');
  }
}

export async function fetchDirectoryArchive(directorySwhid) {
  $('#vault-download-directory-modal').modal('hide');
  $('#vault-recook-object-modal').attr('swh-object-type', 'directory');
  $('#vault-recook-object-modal').attr('swh-object-swhid', directorySwhid);
  const vaultUrl = Urls.api_1_vault_cook_flat(directorySwhid);
  const response = await fetch(vaultUrl);
  const data = await response.json();
  swh.vault.fetchCookedObject(data.fetch_url);
}

export function cookRevisionArchive(event, revisionId) {
  if (event) {
    event.preventDefault();
  }
  const email = $('#swh-vault-revision-email').val().trim();
  if (!email || EmailValidator.validate(email)) {
    const cookingTask = {
      'bundle_type': 'git_bare',
      'swhid': revisionId,
      'email': email,
      'status': 'new'
    };
    addVaultCookingTask('revision', cookingTask);
  } else {
    $('#invalid-email-modal').modal('show');
  }
}

export async function fetchRevisionArchive(revisionSwhid) {
  $('#vault-download-revision-modal').modal('hide');
  $('#vault-recook-object-modal').attr('swh-object-type', 'revision');
  $('#vault-recook-object-modal').attr('swh-object-swhid', revisionSwhid);
  const vaultUrl = Urls.api_1_vault_cook_git_bare(revisionSwhid);
  const response = await fetch(vaultUrl);
  const data = await response.json();
  swh.vault.fetchCookedObject(data.fetch_url);
}
