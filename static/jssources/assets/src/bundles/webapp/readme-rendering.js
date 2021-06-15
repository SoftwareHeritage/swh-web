/**
 * Copyright (C) 2018-2021  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import {handleFetchError} from 'utils/functions';

import {decode} from 'html-encoder-decoder';

export async function renderMarkdown(domElt, markdownDocUrl) {

  let showdown = await import(/* webpackChunkName: "showdown" */ 'utils/showdown');
  await import(/* webpackChunkName: "highlightjs" */ 'utils/highlightjs');

  // Adapted from https://github.com/Bloggify/showdown-highlight
  // Copyright (c) 2016-19 Bloggify <support@bloggify.org> (https://bloggify.org)
  function showdownHighlight() {
    return [{
      type: 'output',
      filter: function(text, converter, options) {
        let left = '<pre><code\\b[^>]*>';
        let right = '</code></pre>';
        let flags = 'g';
        let classAttr = 'class="';
        let replacement = (wholeMatch, match, left, right) => {
          match = decode(match);
          let lang = (left.match(/class="([^ "]+)/) || [])[1];

          if (left.includes(classAttr)) {
            let attrIndex = left.indexOf(classAttr) + classAttr.length;
            left = left.slice(0, attrIndex) + 'hljs ' + left.slice(attrIndex);
          } else {
            left = left.slice(0, -1) + ' class="hljs">';
          }

          if (lang && hljs.getLanguage(lang)) {
            return left + hljs.highlight(match, {language: lang}).value + right;
          } else {
            return left + match + right;
          }
        };

        return showdown.helper.replaceRecursiveRegExp(text, replacement, left, right, flags);
      }
    }];
  }

  $(document).ready(async() => {
    let converter = new showdown.Converter({
      tables: true,
      extensions: [showdownHighlight]
    });

    try {
      const response = await fetch(markdownDocUrl);
      handleFetchError(response);
      const data = await response.text();
      $(domElt).addClass('swh-showdown');
      $(domElt).html(swh.webapp.filterXSS(converter.makeHtml(data)));
    } catch (_) {
      $(domElt).text('Readme bytes are not available');
    }
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
  $(document).ready(async() => {
    try {
      const response = await fetch(orgDocUrl);
      handleFetchError(response);
      const data = await response.text();
      renderOrgData(domElt, data);
    } catch (_) {
      $(domElt).text('Readme bytes are not available');
    }
  });
}

export function renderTxt(domElt, txtDocUrl) {
  $(document).ready(async() => {
    try {
      const response = await fetch(txtDocUrl);
      handleFetchError(response);
      const data = await response.text();

      let orgMode = '-*- mode: org -*-';
      if (data.indexOf(orgMode) !== -1) {
        renderOrgData(domElt, data.replace(orgMode, ''));
      } else {
        $(domElt).addClass('swh-readme-txt');
        $(domElt)
            .html('')
            .append($('<pre></pre>').text(data));
      }
    } catch (_) {
      $(domElt).text('Readme bytes are not available');
    }
  });
}
