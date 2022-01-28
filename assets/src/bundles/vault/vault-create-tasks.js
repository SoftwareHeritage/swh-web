/**
 * Copyright (C) 2018-2022  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import * as EmailValidator from 'email-validator';

import {handleFetchError, csrfPost, htmlAlert} from 'utils/functions';

const alertStyle = {
  'position': 'fixed',
  'left': '1rem',
  'bottom': '1rem',
  'z-index': '100000'
};

function vaultModalHandleEnterKey(event) {
  if (event.keyCode === 13) {
    event.preventDefault();
    $('.modal.show').last().find('button:contains("Ok")').trigger('click');
  }
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
  if (data.exception === 'NotFoundExc' || data.status === 'failed') {
    // if last cooking has failed, remove previous task info from localStorage
    // in order to force the recooking of the object
    swh.vault.removeCookingTaskInfo([swhid]);
    const vaultModalId = `#vault-cook-${objectType}-modal`;
    $(vaultModalId).modal('show');
    $('body').on('keyup', vaultModalId, vaultModalHandleEnterKey);
    // object has been cooked and should be in the vault cache,
    // it will be asked to cook it again if it is not
  } else if (data.status === 'done') {
    const vaultModalId = `#vault-fetch-${objectType}-modal`;
    $(vaultModalId).modal('show');
    $('body').on('keyup', vaultModalId, vaultModalHandleEnterKey);
  } else {
    const cookingServiceDownAlert =
          $(htmlAlert('danger',
                      'Archive cooking service is currently experiencing issues.<br/>' +
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
      $('body').off('keyup', '#vault-cook-directory-modal', vaultModalHandleEnterKey);
      $('#vault-cook-revision-modal').modal('hide');
      $('body').off('keyup', '#vault-cook-revision-modal', vaultModalHandleEnterKey);
      const cookingTaskCreatedAlert =
          $(htmlAlert('success',
                      'Archive cooking request successfully submitted.<br/>' +
                      `Go to the <a href="${Urls.browse_vault()}">Downloads</a> page ` +
                      'to get the download link once it is ready.',
                      true));
      cookingTaskCreatedAlert.css(alertStyle);
      $('body').append(cookingTaskCreatedAlert);
    } catch (_) {
      $('#vault-cook-directory-modal').modal('hide');
      $('body').off('keyup', '#vault-cook-directory-modal', vaultModalHandleEnterKey);
      $('#vault-cook-revision-modal').modal('hide');
      $('body').off('keyup', '#vault-cook-revision-modal', vaultModalHandleEnterKey);
      const cookingTaskFailedAlert =
          $(htmlAlert('danger',
                      'Archive cooking request submission failed.',
                      true));
      cookingTaskFailedAlert.css(alertStyle);
      $('body').append(cookingTaskFailedAlert);
    }
  }
}

export function cookDirectoryArchive(swhid) {
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
    $('body').on('keyup', '#invalid-email-modal', vaultModalHandleEnterKey);
  }
}

export async function fetchDirectoryArchive(directorySwhid) {
  $('#vault-fetch-directory-modal').modal('hide');
  $('body').off('keyup', '#vault-cook-revision-modal', vaultModalHandleEnterKey);
  const vaultUrl = Urls.api_1_vault_cook_flat(directorySwhid);
  const response = await fetch(vaultUrl);
  const data = await response.json();
  swh.vault.fetchCookedObject(data.fetch_url);
}

export function cookRevisionArchive(revisionId) {
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
    $('body').on('keyup', '#invalid-email-modal', vaultModalHandleEnterKey);
  }
}

export async function fetchRevisionArchive(revisionSwhid) {
  $('#vault-fetch-revision-modal').modal('hide');
  $('body').off('keyup', '#vault-fetch-revision-modal', vaultModalHandleEnterKey);
  const vaultUrl = Urls.api_1_vault_cook_git_bare(revisionSwhid);
  const response = await fetch(vaultUrl);
  const data = await response.json();
  swh.vault.fetchCookedObject(data.fetch_url);
}
