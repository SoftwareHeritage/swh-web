/**
 * Copyright (C) 2020  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import {handleFetchError, csrfPost, removeUrlFragment} from 'utils/functions';
import './auth.css';

let apiTokensTable;

function tokenForm(infoText, buttonText) {
  const form =
    `<form id="swh-token-form" class="text-center">
      <p id="swh-token-form-text">${infoText}</p>
      <input id="swh-token-form-submit" type="submit" value="${buttonText}">
      <div id="swh-token-form-message"></div>
    </form>`;
  return form;
}

function errorMessage(message) {
  return `<p id="swh-token-error-message" class="mt-3 swh-token-form-message">${message}</p>`;
}

function successMessage(message) {
  return `<p id="swh-token-success-message" class="mt-3 swh-token-form-message">${message}</p>`;
}

function disableSubmitButton() {
  $('#swh-token-form-submit').prop('disabled', true);
}

function generateToken() {
  window.location = Urls.oidc_generate_bearer_token();
}

function displayToken(tokenId) {
  const postData = {
    token_id: tokenId
  };
  csrfPost(Urls.oidc_get_bearer_token(), {}, JSON.stringify(postData))
    .then(handleFetchError)
    .then(response => response.text())
    .then(token => {
      const tokenHtml =
        `<p>Below is your token.</p>
         <pre id="swh-bearer-token" class="mt-3">${token}</pre>`;
      swh.webapp.showModalHtml('Display bearer token', tokenHtml);
    })
    .catch(() => {
      swh.webapp.showModalHtml('Display bearer token', errorMessage('Internal server error.'));
    });
}

function revokeTokens(tokenIds) {
  const postData = {
    token_ids: tokenIds
  };
  csrfPost(Urls.oidc_revoke_bearer_tokens(), {}, JSON.stringify(postData))
    .then(handleFetchError)
    .then(() => {
      disableSubmitButton();
      $('#swh-token-form-message').html(
        successMessage(`Bearer token${tokenIds.length > 1 ? 's' : ''} successfully revoked.`));
      apiTokensTable.draw();
    })
    .catch(() => {
      $('#swh-token-form-message').html(errorMessage('Internal server error.'));
    });
}

function revokeToken(tokenId) {
  revokeTokens([tokenId]);
}

function revokeAllTokens() {
  const tokenIds = [];
  const rowsData = apiTokensTable.rows().data();
  for (let i = 0; i < rowsData.length; ++i) {
    tokenIds.push(rowsData[i].id);
  }
  revokeTokens(tokenIds);
}

export function applyTokenAction(action, tokenId) {
  const actionData = {
    display: {
      submitCallback: displayToken
    },
    generate: {
      modalTitle: 'Bearer token generation',
      infoText: 'Click on the button to generate the token. You will be redirected to ' +
                'Software Heritage Authentication Service and might be asked to enter ' +
                'your password again.',
      buttonText: 'Generate token',
      submitCallback: generateToken
    },
    revoke: {
      modalTitle: 'Revoke bearer token',
      infoText: 'Click on the button to revoke the token.',
      buttonText: 'Revoke token',
      submitCallback: revokeToken
    },
    revokeAll: {
      modalTitle: 'Revoke all bearer tokens',
      infoText: 'Click on the button to revoke all tokens.',
      buttonText: 'Revoke tokens',
      submitCallback: revokeAllTokens
    }
  };

  if (!actionData[action]) {
    return;
  }

  if (action !== 'display') {
    const tokenFormHtml = tokenForm(
      actionData[action].infoText, actionData[action].buttonText);

    swh.webapp.showModalHtml(actionData[action].modalTitle, tokenFormHtml);
    $(`#swh-token-form`).submit(event => {
      event.preventDefault();
      event.stopPropagation();
      actionData[action].submitCallback(tokenId);
    });
  } else {
    actionData[action].submitCallback(tokenId);
  }
}

export function initProfilePage() {
  $(document).ready(() => {
    apiTokensTable = $('#swh-bearer-tokens-table')
      .on('error.dt', (e, settings, techNote, message) => {
        $('#swh-origin-save-request-list-error').text(
          'An error occurred while retrieving the tokens list');
        console.log(message);
      })
      .DataTable({
        serverSide: true,
        ajax: Urls.oidc_list_bearer_tokens(),
        columns: [
          {
            data: 'creation_date',
            name: 'creation_date',
            render: (data, type, row) => {
              if (type === 'display') {
                let date = new Date(data);
                return date.toLocaleString();
              }
              return data;
            }
          },
          {
            render: (data, type, row) => {
              const html =
                `<button class="btn btn-default"
                         onclick="swh.auth.applyTokenAction('display', ${row.id})">
                  Display token
                </button>
                <button class="btn btn-default"
                        onclick="swh.auth.applyTokenAction('revoke', ${row.id})">
                  Revoke token
                </button>`;
              return html;
            }
          }
        ],
        ordering: false,
        searching: false,
        scrollY: '50vh',
        scrollCollapse: true
      });
    $('#swh-oidc-profile-tokens-tab').on('shown.bs.tab', () => {
      apiTokensTable.draw();
      window.location.hash = '#tokens';
    });
    $('#swh-oidc-profile-account-tab').on('shown.bs.tab', () => {
      removeUrlFragment();
    });
    if (window.location.hash === '#tokens') {
      $('.nav-tabs a[href="#swh-oidc-profile-tokens"]').tab('show');
    }
  });
}
