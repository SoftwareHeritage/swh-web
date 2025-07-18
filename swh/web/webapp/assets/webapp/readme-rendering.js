/**
 * Copyright (C) 2018-2025  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import {handleFetchError} from 'utils/functions';
import {decode} from 'html-encoder-decoder';

export function addReadmeHeadingAnchors() {
  swh.webapp.addHeadingAnchors('.swh-readme');
}

export async function renderMarkdown(domElt, markdownDocUrl, allowCSS = false) {

  const showdown = await import(/* webpackChunkName: "showdown" */ 'utils/showdown');
  await import(/* webpackChunkName: "highlightjs" */ 'utils/highlightjs');

  // Adapted from https://github.com/Bloggify/showdown-highlight
  // MIT License
  // Copyright (c) 2016-22 Bloggify <support@bloggify.org> (https://bloggify.org)
  function showdownHighlight() {
    return [{
      type: 'output',
      filter: function(text, converter, options) {
        const params = {
          left: '<pre><code\\b[^>]*>',
          right: '</code></pre>',
          flags: 'g'
        };

        const replacement = (wholeMatch, match, left, right) => {
          match = decode(match);

          let lang = (left.match(/class="([^ "]+)/) || [])[1];

          if (!lang) {
            return wholeMatch;
          } else if (lang && lang.indexOf(',') > 0) {
            // ensure to strip any code block annotation after language
            const langNoAnnotation = lang.slice(0, lang.indexOf(','));
            left = left.replace(new RegExp(lang, 'g'), langNoAnnotation);
            lang = langNoAnnotation;
          }

          const classAttr = 'class="';

          if (left.includes(classAttr)) {
            const attrIndex = left.indexOf(classAttr) + classAttr.length;
            left = left.slice(0, attrIndex) + 'hljs ' + left.slice(attrIndex);
          } else {
            left = left.slice(0, -1) + ' class="hljs">';
          }

          if (lang && hljs.getLanguage(lang)) {
            return left + hljs.highlight(match, {language: lang}).value + right;
          }

          return left + hljs.highlightAuto(match).value + right;
        };

        return showdown.helper.replaceRecursiveRegExp(
          text,
          replacement,
          params.left,
          params.right,
          params.flags
        );
      }
    }];
  }

  const converter = new showdown.Converter({
    tables: true,
    extensions: [showdownHighlight]
  });
  const url = new URL(window.location.href);
  if (url.searchParams.has('origin_url')) {
    try {
      const originUrl = new URL(url.searchParams.get('origin_url'));
      if (originUrl.hostname === 'github.com') {
        converter.setFlavor('github');
      }
    } catch (TypeError) {}
  }

  try {
    const response = await fetch(markdownDocUrl);
    handleFetchError(response);
    const data = await response.text();
    const html = converter.makeHtml(data);
    const sanitizedHtml = swh.webapp.filterXSS(html, allowCSS);
    if (domElt) {
      $(domElt).addClass('swh-showdown');
      $(domElt).html(sanitizedHtml);
      addReadmeHeadingAnchors();
    }
    return sanitizedHtml;
  } catch (_) {
    $(domElt).text('Readme bytes are not available');
  }
}

export async function renderOrgData(domElt, orgDocData) {

  const org = await import(/* webpackChunkName: "org" */ 'utils/org');

  const parser = new org.Parser();
  const orgDocument = parser.parse(orgDocData, {toc: false});
  const orgHTMLDocument = orgDocument.convert(org.ConverterHTML, {});
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
      addReadmeHeadingAnchors();
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

      const orgMode = '-*- mode: org -*-';
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
