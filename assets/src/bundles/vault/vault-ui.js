/**
 * Copyright (C) 2018-2019  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import {handleFetchError, handleFetchErrors, csrfPost} from 'utils/functions';
import vaultTableRowTemplate from './vault-table-row.ejs';

let progress =
  `<div class="progress">
    <div class="progress-bar progress-bar-success progress-bar-striped"
          role="progressbar" aria-valuenow="100" aria-valuemin="0"
          aria-valuemax="100" style="width: 100%;height: 100%;">
    </div>
  </div>;`;

let pollingInterval = 5000;
let checkVaultId;

function updateProgressBar(progressBar, cookingTask) {
  if (cookingTask.status === 'new') {
    progressBar.css('background-color', 'rgba(128, 128, 128, 0.5)');
  } else if (cookingTask.status === 'pending') {
    progressBar.css('background-color', 'rgba(0, 0, 255, 0.5)');
  } else if (cookingTask.status === 'done') {
    progressBar.css('background-color', '#5cb85c');
  } else if (cookingTask.status === 'failed') {
    progressBar.css('background-color', 'rgba(255, 0, 0, 0.5)');
    progressBar.css('background-image', 'none');
  }
  progressBar.text(cookingTask.progress_message || cookingTask.status);
  if (cookingTask.status === 'new' || cookingTask.status === 'pending') {
    progressBar.addClass('progress-bar-animated');
  } else {
    progressBar.removeClass('progress-bar-striped');
  }
}

let recookTask;

// called when the user wants to download a cooked archive
export function fetchCookedObject(fetchUrl) {
  recookTask = null;
  // first, check if the link is still available from the vault
  fetch(fetchUrl)
    .then(response => {
      // link is still alive, proceed to download
      if (response.ok) {
        $('#vault-fetch-iframe').attr('src', fetchUrl);
      // link is dead
      } else {
        // get the associated cooking task
        let vaultCookingTasks = JSON.parse(localStorage.getItem('swh-vault-cooking-tasks'));
        for (let i = 0; i < vaultCookingTasks.length; ++i) {
          if (vaultCookingTasks[i].fetch_url === fetchUrl) {
            recookTask = vaultCookingTasks[i];
            break;
          }
        }
        // display a modal asking the user if he wants to recook the archive
        $('#vault-recook-object-modal').modal('show');
      }
    });
}

// called when the user wants to recook an archive
// for which the download link is not available anymore
export function recookObject() {
  if (recookTask) {
    // stop cooking tasks status polling
    clearTimeout(checkVaultId);
    // build cook request url
    let cookingUrl;
    if (recookTask.object_type === 'directory') {
      cookingUrl = Urls.api_1_vault_cook_directory(recookTask.object_id);
    } else {
      cookingUrl = Urls.api_1_vault_cook_revision_gitfast(recookTask.object_id);
    }
    if (recookTask.email) {
      cookingUrl += '?email=' + recookTask.email;
    }
    // request archive cooking
    csrfPost(cookingUrl)
      .then(handleFetchError)
      .then(() => {
        // update task status
        recookTask.status = 'new';
        let vaultCookingTasks = JSON.parse(localStorage.getItem('swh-vault-cooking-tasks'));
        for (let i = 0; i < vaultCookingTasks.length; ++i) {
          if (vaultCookingTasks[i].object_id === recookTask.object_id) {
            vaultCookingTasks[i] = recookTask;
            break;
          }
        }
        // save updated tasks to local storage
        localStorage.setItem('swh-vault-cooking-tasks', JSON.stringify(vaultCookingTasks));
        // restart cooking tasks status polling
        checkVaultCookingTasks();
        // hide recook archive modal
        $('#vault-recook-object-modal').modal('hide');
      })
      // something went wrong
      .catch(() => {
        checkVaultCookingTasks();
        $('#vault-recook-object-modal').modal('hide');
      });
  }
}

function checkVaultCookingTasks() {
  let vaultCookingTasks = JSON.parse(localStorage.getItem('swh-vault-cooking-tasks'));
  if (!vaultCookingTasks || vaultCookingTasks.length === 0) {
    $('.swh-vault-table tbody tr').remove();
    checkVaultId = setTimeout(checkVaultCookingTasks, pollingInterval);
    return;
  }
  let cookingTaskRequests = [];
  let tasks = {};
  let currentObjectIds = [];

  for (let i = 0; i < vaultCookingTasks.length; ++i) {
    let cookingTask = vaultCookingTasks[i];
    currentObjectIds.push(cookingTask.object_id);
    tasks[cookingTask.object_id] = cookingTask;
    let cookingUrl;
    if (cookingTask.object_type === 'directory') {
      cookingUrl = Urls.api_1_vault_cook_directory(cookingTask.object_id);
    } else {
      cookingUrl = Urls.api_1_vault_cook_revision_gitfast(cookingTask.object_id);
    }
    if (cookingTask.status !== 'done' && cookingTask.status !== 'failed') {
      cookingTaskRequests.push(fetch(cookingUrl));
    }
  }
  $('.swh-vault-table tbody tr').each((i, row) => {
    let objectId = $(row).find('.vault-object-info').data('object-id');
    if ($.inArray(objectId, currentObjectIds) === -1) {
      $(row).remove();
    }
  });
  Promise.all(cookingTaskRequests)
    .then(handleFetchErrors)
    .then(responses => Promise.all(responses.map(r => r.json())))
    .then(cookingTasks => {
      let table = $('#vault-cooking-tasks tbody');
      for (let i = 0; i < cookingTasks.length; ++i) {
        let cookingTask = tasks[cookingTasks[i].obj_id];
        cookingTask.status = cookingTasks[i].status;
        cookingTask.fetch_url = cookingTasks[i].fetch_url;
        cookingTask.progress_message = cookingTasks[i].progress_message;
      }
      for (let i = 0; i < vaultCookingTasks.length; ++i) {
        let cookingTask = vaultCookingTasks[i];
        let rowTask = $(`#vault-task-${cookingTask.object_id}`);

        if (!rowTask.length) {

          let browseUrl = cookingTask.browse_url;
          if (!browseUrl) {
            if (cookingTask.object_type === 'directory') {
              browseUrl = Urls.browse_directory(cookingTask.object_id);
            } else {
              browseUrl = Urls.browse_revision(cookingTask.object_id);
            }
          }

          let progressBar = $.parseHTML(progress)[0];
          let progressBarContent = $(progressBar).find('.progress-bar');
          updateProgressBar(progressBarContent, cookingTask);
          table.prepend(vaultTableRowTemplate({
            browseUrl: browseUrl,
            cookingTask: cookingTask,
            progressBar: progressBar,
            Urls: Urls,
            swh: swh
          }));
        } else {
          let progressBar = rowTask.find('.progress-bar');
          updateProgressBar(progressBar, cookingTask);
          let downloadLink = rowTask.find('.vault-dl-link');
          if (cookingTask.status === 'done') {
            downloadLink[0].innerHTML =
              '<button class="btn btn-default btn-sm" ' +
              `onclick="swh.vault.fetchCookedObject('${cookingTask.fetch_url}')">` +
              '<i class="mdi mdi-download mdi-fw" aria-hidden="true"></i>Download</button>';
          } else {
            downloadLink[0].innerHTML = '';
          }
        }
      }
      localStorage.setItem('swh-vault-cooking-tasks', JSON.stringify(vaultCookingTasks));
      checkVaultId = setTimeout(checkVaultCookingTasks, pollingInterval);
    })
    .catch(error => {
      console.log('Error when fetching vault cooking tasks:', error);
    });
}

export function removeCookingTaskInfo(tasksToRemove) {
  let vaultCookingTasks = JSON.parse(localStorage.getItem('swh-vault-cooking-tasks'));
  if (!vaultCookingTasks) {
    return;
  }
  vaultCookingTasks = $.grep(vaultCookingTasks, task => {
    return $.inArray(task.object_id, tasksToRemove) === -1;
  });
  localStorage.setItem('swh-vault-cooking-tasks', JSON.stringify(vaultCookingTasks));
}

export function initUi() {

  $('#vault-tasks-toggle-selection').change(event => {
    $('.vault-task-toggle-selection').prop('checked', event.currentTarget.checked);
  });

  $('#vault-remove-tasks').click(() => {
    clearTimeout(checkVaultId);
    let tasksToRemove = [];
    $('.swh-vault-table tbody tr').each((i, row) => {
      let taskSelected = $(row).find('.vault-task-toggle-selection').prop('checked');
      if (taskSelected) {
        let objectId = $(row).find('.vault-object-info').data('object-id');
        tasksToRemove.push(objectId);
        $(row).remove();
      }
    });
    removeCookingTaskInfo(tasksToRemove);
    $('#vault-tasks-toggle-selection').prop('checked', false);
    checkVaultId = setTimeout(checkVaultCookingTasks, pollingInterval);
  });

  checkVaultCookingTasks();

  window.onfocus = () => {
    clearTimeout(checkVaultId);
    checkVaultCookingTasks();
  };

}
