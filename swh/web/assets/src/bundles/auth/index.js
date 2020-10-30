/**
 * Copyright (C) 2020  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import {handleFetchError, csrfPost, removeUrlFragment} from 'utils/functions';
import './auth.css';

let apiTokensTable;

function updateSubmitButtonState() {
  const val = $('#swh-user-password').val();
  $('#swh-user-password-submit').prop('disabled', val.length === 0);
}

function passwordForm(infoText, buttonText) {
  const form =
    `<form id="swh-password-form">
      <p id="swh-password-form-text">${infoText}</p>
      <label for="swh-user-password">Password:&nbsp;</label>
      <input id="swh-user-password" type="password" name="swh-user-password" required>
      <input id="swh-user-password-submit" type="submit" value="${buttonText}" disabled>
    </form>`;
  return form;
}

function errorMessage(message) {
  return `<p id="swh-token-error-message" class="mt-3">${message}</p>`;
}

function successMessage(message) {
  return `<p id="swh-token-success-message" class="mt-3">${message}</p>`;
}

function disableSubmitButton() {
  $('#swh-user-password-submit').prop('disabled', true);
  $('#swh-user-password').off('change');
  $('#swh-user-password').off('keyup');
}

function generateToken() {
  csrfPost(Urls.oidc_generate_bearer_token(), {},
           JSON.stringify({password: $('#swh-user-password').val()}))
    .then(handleFetchError)
    .then(response => response.text())
    .then(token => {
      disableSubmitButton();
      const tokenHtml =
        `${successMessage('Below is your token.')}
         <pre id="swh-bearer-token">${token}</pre>`;
      $(`#swh-password-form`).append(tokenHtml);
      apiTokensTable.draw();
    })
    .catch(response => {
      if (response.status === 400) {
        $(`#swh-password-form`).append(
          errorMessage('You are not allowed to generate bearer tokens.'));
      } else if (response.status === 401) {
        $(`#swh-password-form`).append(errorMessage('The password is invalid.'));
      } else {
        $(`#swh-password-form`).append(errorMessage('Internal server error.'));
      }
    });
}

function displayToken(tokenId) {
  const postData = {
    password: $('#swh-user-password').val(),
    token_id: tokenId
  };
  csrfPost(Urls.oidc_get_bearer_token(), {}, JSON.stringify(postData))
    .then(handleFetchError)
    .then(response => response.text())
    .then(token => {
      disableSubmitButton();
      const tokenHtml =
        `${successMessage('Below is your token.')}
         <pre id="swh-bearer-token">${token}</pre>`;
      $(`#swh-password-form`).append(tokenHtml);
    })
    .catch(response => {
      if (response.status === 401) {
        $(`#swh-password-form`).append(errorMessage('The password is invalid.'));
      } else {
        $(`#swh-password-form`).append(errorMessage('Internal server error.'));
      }
    });
}

function revokeTokens(tokenIds) {
  const postData = {
    password: $('#swh-user-password').val(),
    token_ids: tokenIds
  };
  csrfPost(Urls.oidc_revoke_bearer_tokens(), {}, JSON.stringify(postData))
    .then(handleFetchError)
    .then(() => {
      disableSubmitButton();
      $(`#swh-password-form`).append(
        successMessage(`Bearer token${tokenIds.length > 1 ? 's' : ''} successfully revoked`));
      apiTokensTable.draw();
    })
    .catch(response => {
      if (response.status === 401) {
        $(`#swh-password-form`).append(errorMessage('The password is invalid.'));
      } else {
        $(`#swh-password-form`).append(errorMessage('Internal server error.'));
      }
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
    generate: {
      modalTitle: 'Bearer token generation',
      infoText: 'Enter your password and click on the button to generate the token.',
      buttonText: 'Generate token',
      submitCallback: generateToken
    },
    display: {
      modalTitle: 'Display bearer token',
      infoText: 'Enter your password and click on the button to display the token.',
      buttonText: 'Display token',
      submitCallback: displayToken
    },
    revoke: {
      modalTitle: 'Revoke bearer token',
      infoText: 'Enter your password and click on the button to revoke the token.',
      buttonText: 'Revoke token',
      submitCallback: revokeToken
    },
    revokeAll: {
      modalTitle: 'Revoke all bearer tokens',
      infoText: 'Enter your password and click on the button to revoke all tokens.',
      buttonText: 'Revoke tokens',
      submitCallback: revokeAllTokens
    }
  };

  if (!actionData[action]) {
    return;
  }

  const passwordFormHtml = passwordForm(
    actionData[action].infoText, actionData[action].buttonText);

  swh.webapp.showModalHtml(actionData[action].modalTitle, passwordFormHtml);
  $('#swh-user-password').change(updateSubmitButtonState);
  $('#swh-user-password').keyup(updateSubmitButtonState);
  $(`#swh-password-form`).submit(event => {
    event.preventDefault();
    event.stopPropagation();
    actionData[action].submitCallback(tokenId);
  });
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
