/**
 * Copyright (C) 2018  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import {handleFetchError} from 'utils/functions';

export async function renderMarkdown(domElt, markdownDocUrl) {

  let showdown = await import(/* webpackChunkName: "showdown" */ 'utils/showdown');

  $(document).ready(() => {
    let converter = new showdown.Converter({tables: true});
    fetch(markdownDocUrl)
      .then(handleFetchError)
      .then(response => response.text())
      .then(data => {
        $(domElt).addClass('swh-showdown');
        $(domElt).html(converter.makeHtml(data));
      })
      .catch(() => {
        $(domElt).text('Readme bytes are not available');
      });
  });

}

export function renderTxt(domElt, txtDocUrl) {

  $(document).ready(() => {
    fetch(txtDocUrl)
      .then(handleFetchError)
      .then(response => response.text())
      .then(data => {
        $(domElt).addClass('swh-readme-txt');
        $(domElt).html(`<pre>${data}</pre>`);
      })
      .catch(() => {
        $(domElt).text('Readme bytes are not available');
      });
  });

}
