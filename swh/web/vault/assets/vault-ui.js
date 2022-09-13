/**
 * Copyright (C) 2018-2019  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import {handleFetchError, handleFetchErrors, csrfPost} from 'utils/functions';
import vaultTableRowTemplate from './vault-table-row.ejs';

const progress =
  `<div class="progress">
    <div class="progress-bar progress-bar-success progress-bar-striped"
          role="progressbar" aria-valuenow="100" aria-valuemin="0"
          aria-valuemax="100" style="width: 100%;height: 100%;">
    </div>
  </div>;`;

const pollingInterval = 5000;
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
  var text = cookingTask.progress_message || cookingTask.status;
  var firstLine, rest;
  [firstLine, ...rest] = text.split('\n', 2);
  progressBar.text(firstLine);
  if (rest.length) {
    progressBar.prop('title', rest[0]);
  }
  if (cookingTask.status === 'new' || cookingTask.status === 'pending') {
    progressBar.addClass('progress-bar-animated');
  } else {
    progressBar.removeClass('progress-bar-striped');
  }
}

let recookTask;

// called when the user wants to download a cooked archive
export async function fetchCookedObject(fetchUrl) {
  recookTask = null;
  // first, check if the link is still available from the vault
  const response = await fetch(fetchUrl);

  // link is still alive, proceed to download
  if (response.ok) {
    $('#vault-fetch-iframe').attr('src', fetchUrl);
    // link is dead
  } else {
    // get the associated cooking task
    const vaultCookingTasks = JSON.parse(localStorage.getItem('swh-vault-cooking-tasks'));
    for (let i = 0; i < vaultCookingTasks.length; ++i) {
      if (vaultCookingTasks[i].fetch_url === fetchUrl) {
        recookTask = vaultCookingTasks[i];
        break;
      }
    }
    // display a modal asking the user if he wants to recook the archive
    $('#vault-recook-object-modal').modal('show');
  }
}

// called when the user wants to recook an archive
// for which the download link is not available anymore
export async function recookObject() {
  if (recookTask) {
    // stop cooking tasks status polling
    clearTimeout(checkVaultId);
    // build cook request url
    let cookingUrl;
    if (recookTask.bundle_type === 'flat') {
      cookingUrl = Urls.api_1_vault_cook_flat(recookTask.swhid);
    } else {
      cookingUrl = Urls.api_1_vault_cook_git_bare(recookTask.swhid);
    }
    if (recookTask.email) {
      cookingUrl += '?email=' + recookTask.email;
    }
    try {
    // request archive cooking
      const response = await csrfPost(cookingUrl);
      handleFetchError(response);

      // update task status
      recookTask.status = 'new';
      const vaultCookingTasks = JSON.parse(localStorage.getItem('swh-vault-cooking-tasks'));
      for (let i = 0; i < vaultCookingTasks.length; ++i) {
        if (vaultCookingTasks[i].swhid === recookTask.swhid) {
          vaultCookingTasks[i] = recookTask;
          break;
        }
      }
      // save updated tasks to local storage
      localStorage.setItem('swh-vault-cooking-tasks', JSON.stringify(vaultCookingTasks));
      // hide recook archive modal
      $('#vault-recook-object-modal').modal('hide');
      // restart cooking tasks status polling
      await checkVaultCookingTasks();
    } catch (_) {
      // something went wrong
      $('#vault-recook-object-modal').modal('hide');
      await checkVaultCookingTasks();
    }
  }
}

async function checkVaultCookingTasks() {
  const vaultCookingTasks = JSON.parse(localStorage.getItem('swh-vault-cooking-tasks'));
  if (!vaultCookingTasks || vaultCookingTasks.length === 0) {
    $('.swh-vault-table tbody tr').remove();
    checkVaultId = setTimeout(checkVaultCookingTasks, pollingInterval);
    return;
  }
  const cookingTaskRequests = [];
  const tasks = {};
  const currentObjectIds = [];

  for (let i = 0; i < vaultCookingTasks.length; ++i) {
    const cookingTask = vaultCookingTasks[i];

    if (typeof cookingTask.object_type !== 'undefined') {
      // Legacy cooking task, upgrade it to the new schema
      if (cookingTask.object_type === 'directory') {
        cookingTask.swhid = `swh:1:dir:${cookingTask.object_id}`;
        cookingTask.bundle_type = 'flat';
        cookingTask.fetch_url = Urls.api_1_vault_fetch_flat(cookingTask.swhid);
      } else if (cookingTask.object_type === 'revision') {
        cookingTask.swhid = `swh:1:rev:${cookingTask.object_id}`;
        cookingTask.bundle_type = 'git_bare';
        cookingTask.fetch_url = Urls.api_1_vault_fetch_git_bare(cookingTask.swhid);
      } else {
        // Log to the console + Sentry
        console.error(`Unexpected cookingTask.object_type: ${cookingTask.object_type}`);
        // Ignore it for now and hope a future version will fix it
        continue;
      }
      delete cookingTask.object_type;
      delete cookingTask.object_id;
    }

    currentObjectIds.push(cookingTask.swhid);
    tasks[cookingTask.swhid] = cookingTask;
    let cookingUrl;
    if (cookingTask.bundle_type === 'flat') {
      cookingUrl = Urls.api_1_vault_cook_flat(cookingTask.swhid);
    } else {
      cookingUrl = Urls.api_1_vault_cook_git_bare(cookingTask.swhid);
    }
    if (cookingTask.status !== 'done' && cookingTask.status !== 'failed') {
      cookingTaskRequests.push(fetch(cookingUrl));
    }
  }
  $('.swh-vault-table tbody tr').each((i, row) => {
    const swhid = $(row).find('.vault-object-info').data('swhid');
    if ($.inArray(swhid, currentObjectIds) === -1) {
      $(row).remove();
    }
  });
  try {
    const responses = await Promise.all(cookingTaskRequests);
    handleFetchErrors(responses);
    const cookingTasks = await Promise.all(responses.map(r => r.json()));

    const table = $('#vault-cooking-tasks tbody');
    for (let i = 0; i < cookingTasks.length; ++i) {
      const cookingTask = tasks[cookingTasks[i].swhid];
      cookingTask.status = cookingTasks[i].status;
      cookingTask.fetch_url = cookingTasks[i].fetch_url;
      cookingTask.progress_message = cookingTasks[i].progress_message;
    }
    for (let i = 0; i < vaultCookingTasks.length; ++i) {
      const cookingTask = vaultCookingTasks[i];
      const rowTask = $(`#vault-task-${CSS.escape(cookingTask.swhid)}`);

      if (!rowTask.length) {

        let browseUrl = cookingTask.browse_url;
        if (!browseUrl) {
          browseUrl = Urls.browse_swhid(cookingTask.swhid);
        }

        const progressBar = $.parseHTML(progress)[0];
        const progressBarContent = $(progressBar).find('.progress-bar');
        updateProgressBar(progressBarContent, cookingTask);
        table.prepend(vaultTableRowTemplate({
          browseUrl: browseUrl,
          cookingTask: cookingTask,
          progressBar: progressBar,
          Urls: Urls,
          swh: swh
        }));
      } else {
        const progressBar = rowTask.find('.progress-bar');
        updateProgressBar(progressBar, cookingTask);
        const downloadLink = rowTask.find('.vault-dl-link');
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

  } catch (error) {
    console.log('Error when fetching vault cooking tasks:', error);
  }
}

export function removeCookingTaskInfo(tasksToRemove) {
  let vaultCookingTasks = JSON.parse(localStorage.getItem('swh-vault-cooking-tasks'));
  if (!vaultCookingTasks) {
    return;
  }
  vaultCookingTasks = $.grep(vaultCookingTasks, task => {
    return $.inArray(task.swhid, tasksToRemove) === -1;
  });
  localStorage.setItem('swh-vault-cooking-tasks', JSON.stringify(vaultCookingTasks));
}

export function initUi() {

  $('#vault-tasks-toggle-selection').change(event => {
    $('.vault-task-toggle-selection').prop('checked', event.currentTarget.checked);
  });

  $('#vault-remove-tasks').click(() => {
    clearTimeout(checkVaultId);
    const tasksToRemove = [];
    $('.swh-vault-table tbody tr').each((i, row) => {
      const taskSelected = $(row).find('.vault-task-toggle-selection').prop('checked');
      if (taskSelected) {
        const swhid = $(row).find('.vault-object-info').data('swhid');
        tasksToRemove.push(swhid);
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
