/**
 * Copyright (C) 2022  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import {csrfPost, handleFetchError} from 'utils/functions';

import mailmapFormTemplate from './mailmap-form.ejs';

let mailmapsTable;

export function mailmapForm(buttonText, email = '', displayName = '',
                            displayNameActivated = false, update = false) {
  return mailmapFormTemplate({
    buttonText: buttonText,
    email: email,
    displayName: displayName,
    displayNameActivated: displayNameActivated,
    updateForm: update
  });
}

function getMailmapDataFromForm() {
  return {
    'from_email': $('#swh-mailmap-from-email').val(),
    'display_name': $('#swh-mailmap-display-name').val(),
    'display_name_activated': $('#swh-mailmap-display-name-activated').prop('checked')
  };
}

function processMailmapForm(formTitle, formHtml, formApiUrl) {
  swh.webapp.showModalHtml(formTitle, formHtml);
  $(`#swh-mailmap-form`).on('submit', async event => {
    event.preventDefault();
    event.stopPropagation();
    const postData = getMailmapDataFromForm();
    try {
      const response = await csrfPost(
        formApiUrl, {'Content-Type': 'application/json'}, JSON.stringify(postData)
      );
      $('#swh-web-modal-html').modal('hide');
      handleFetchError(response);
      mailmapsTable.draw();
    } catch (response) {
      const error = await response.text();
      swh.webapp.showModalMessage('Error', error);
    }
  });
}

export function addNewMailmap() {
  const mailmapFormHtml = mailmapForm('Add mailmap');
  processMailmapForm('Add new mailmap', mailmapFormHtml, Urls.profile_mailmap_add());
}

export function updateMailmap(mailmapId) {
  let mailmapData;
  const rows = mailmapsTable.rows().data();
  for (let i = 0; i < rows.length; ++i) {
    const row = rows[i];
    if (row.id === mailmapId) {
      mailmapData = row;
      break;
    }
  }
  const mailmapFormHtml = mailmapForm('Update mailmap', mailmapData.from_email,
                                      mailmapData.display_name,
                                      mailmapData.display_name_activated, true);
  processMailmapForm('Update existing mailmap', mailmapFormHtml, Urls.profile_mailmap_update());
}

const mdiCheckBold = '<i class="mdi mdi-check-bold" aria-hidden="true"></i>';
const mdiCloseThick = '<i class="mdi mdi-close-thick" aria-hidden="true"></i>';

export function initMailmapUI() {
  $(document).ready(() => {
    mailmapsTable = $('#swh-mailmaps-table')
       .on('error.dt', (e, settings, techNote, message) => {
         $('#swh-mailmaps-list-error').text(
           'An error occurred while retrieving the mailmaps list');
         console.log(message);
       })
       .DataTable({
         serverSide: true,
         ajax: Urls.profile_mailmap_list_datatables(),
         columns: [
           {
             data: 'from_email',
             name: 'from_email',
             render: $.fn.dataTable.render.text()
           },
           {
             data: 'from_email_verified',
             name: 'from_email_verified',
             render: (data, type, row) => {
               return data ? mdiCheckBold : mdiCloseThick;
             },
             className: 'dt-center'
           },
           {
             data: 'display_name',
             name: 'display_name',
             render: $.fn.dataTable.render.text()
           },
           {
             data: 'display_name_activated',
             name: 'display_name_activated',
             render: (data, type, row) => {
               return data ? mdiCheckBold : mdiCloseThick;
             },
             className: 'dt-center'
           },
           {
             data: 'last_update_date',
             name: 'last_update_date',
             render: (data, type, row) => {
               if (type === 'display') {
                 const date = new Date(data);
                 return date.toLocaleString();
               }
               return data;
             }
           },
           {
             render: (data, type, row) => {
               const lastUpdateDate = new Date(row.last_update_date);
               const lastProcessingDate = new Date(row.mailmap_last_processing_date);
               if (!lastProcessingDate || lastProcessingDate < lastUpdateDate) {
                 return mdiCloseThick;
               } else {
                 return mdiCheckBold;
               }
             },
             className: 'dt-center',
             orderable: false
           },
           {
             render: (data, type, row) => {
               const html =
                `<button class="btn btn-default"
                         onclick="swh.admin.updateMailmap(${row.id})">
                  Edit
                </button>`;
               return html;
             },
             orderable: false
           }

         ],
         ordering: true,
         searching: true,
         searchDelay: 1000,
         scrollY: '50vh',
         scrollCollapse: true
       });
  });
}
