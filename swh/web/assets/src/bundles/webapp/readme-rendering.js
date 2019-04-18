/**
 * Copyright (C) 2018-2019  The Software Heritage developers
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
        $(domElt).html(swh.webapp.filterXSS(converter.makeHtml(data)));
      })
      .catch(() => {
        $(domElt).text('Readme bytes are not available');
      });
  });

}

export async function renderOrgData(domElt, orgDocData) {

  let org = await import(/* webpackChunkName: "org" */ 'utils/org');

  let parser = new org.Parser();
  let orgDocument = parser.parse(orgDocData, {toc: false});
  let orgHTMLDocument = orgDocument.convert(org.ConverterHTML, {});
  $(domElt).addClass('swh-org');
  $(domElt).html(swh.webapp.filterXSS(orgHTMLDocument.toString()));
  // remove toc and section numbers to get consistent
  // with other readme renderings
  $('.swh-org ul').first().remove();
  $('.section-number').remove();

}

export function renderOrg(domElt, orgDocUrl) {

  $(document).ready(() => {
    fetch(orgDocUrl)
      .then(handleFetchError)
      .then(response => response.text())
      .then(data => {
        renderOrgData(domElt, data);
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
        let orgMode = '-*- mode: org -*-';
        if (data.indexOf(orgMode) !== -1) {
          renderOrgData(domElt, data.replace(orgMode, ''));
        } else {
          $(domElt).addClass('swh-readme-txt');
          $(domElt)
            .html('')
            .append($('<pre></pre>').text(data));
        }
      })
      .catch(() => {
        $(domElt).text('Readme bytes are not available');
      });
  });

}
