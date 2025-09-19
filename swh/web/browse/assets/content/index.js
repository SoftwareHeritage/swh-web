/**
 * Copyright (C) 2025  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

function isMarkdown(filename) {
  return filename &&
    (filename.toLowerCase().endsWith('.md') ||
     filename.toLowerCase().endsWith('.markdown'));
}

function isNotebook(filename) {
  return filename && filename.toLowerCase().endsWith('.ipynb');
}

let rawContent;

export function updateLanguage(language, enableLinesSelection) {
  const codeContainer = $('code');
  codeContainer.text(rawContent);
  codeContainer.removeClass();
  codeContainer.addClass(language);

  const urlParams = new URLSearchParams(window.location.search);
  urlParams.set('language', language);

  const newUrl = window.location.pathname + '?' + urlParams.toString() + window.location.hash;
  window.history.replaceState('', document.title, newUrl);

  swh.webapp.highlightCode(true, '.swh-content code', enableLinesSelection);
}

export function switchToCode() {
  $('.swh-preview-content').css('display', 'none');
  $('.highlightjs').css('display', 'block');
  $('#code-switch').prop('checked', true);
  $('#preview-switch').prop('checked', false);
  const url = new URL(window.location.href);
  url.searchParams.delete('show_preview');
  window.history.replaceState({}, '', url.toString());
}

export function switchToPreview() {
  if (!previewInit) {
    initHtmlPreview();
  }
  $('.swh-preview-content').css('display', 'block');
  $('.highlightjs').css('display', 'none');
  $('#code-switch').prop('checked', false);
  $('#preview-switch').prop('checked', true);
  const url = new URL(window.location.href);
  url.searchParams.set('show_preview', 'true');
  window.history.replaceState({}, '', url.toString());
}

let filename, mimetype, contentUrl, mathjaxLibrary;
let previewInit = false;
async function initHtmlPreview() {
  const iframeResizeLibrary = '/static/jssources/@iframe-resizer/child/index.umd.js';
  // scripts executed in the iframe rendering html to automatically resize it and
  // forward clicked links to parent page
  const iframeScripts = `
<script class="swh-iframe-script" async src="${iframeResizeLibrary}"></script>
<script class="swh-iframe-script" src="${mathjaxLibrary}"></script>
<script class="swh-iframe-script">
  function linkClicked(event) {
    event.preventDefault();
    let hrefVal = event.target.href;
    if (!hrefVal && event.target.parentElement) {
    hrefVal = event.target.parentElement.href;
    }
    parent.postMessage({eventType: 'link', href: hrefVal}, '*');
  }
  const links = document.querySelectorAll('a');
  for (let c = 0; c < links.length; c++) {
    links[c].addEventListener('click', linkClicked);
  }
  swh.mathjax.typesetMath('${window.location.origin}');
</script>`;
  if (isNotebook(filename)) {
    swh.webapp.renderNotebook(contentUrl, '.swh-ipynb');
  } else if (isMarkdown(filename) || mimetype === 'text/html') {
    const response = await fetch(contentUrl);
    const data = await response.text();
    let html = data;
    if (isMarkdown(filename)) {
      html = await swh.webapp.renderMarkdownWithMath(data);
    }
    const sanitizedHtml = swh.webapp.filterXSS(html, true);
    $('.swh-html-content').attr(
      'srcdoc', '<div data-iframe-size>' + sanitizedHtml + '</div>' + iframeScripts);
    swh.webapp.resizeIframe(
      {license: 'GPLv3', waitForLoad: true, heightCalculationMethod: 'taggedElement'},
      '.swh-html-content');
  }
  previewInit = true;
}

export async function renderContent(
  filename_, mimetype_, contentUrl_, mathjaxLibrary_, enableLinesSelection) {

  filename = filename_;
  mimetype = mimetype_;
  contentUrl = contentUrl_;
  mathjaxLibrary = mathjaxLibrary_;

  if (mimetype === 'application/pdf') {
    swh.webapp.renderPdf(contentUrl);
  } else if (isMarkdown(filename) || mimetype === 'text/html') {
    // handle links clicked in iframe to allow navigation between pages
    $(window).on('message', event => {
      event = event.originalEvent;
      if (event && event.data && event.data.hasOwnProperty('eventType')) {
        if (event.data.eventType === 'link') {
          const url = new URL(event.data.href);
          if (url.origin === window.location.origin) {
            // follow relative link by reloading page
            url.searchParams.set('show_preview', 'true');
            window.location = url.toString();
          } else {
            // open external link in new tab
            window.open(url.toString(), '_blank').focus();
          }
        }
      }
    });
  }

  if (isNotebook(filename)) {
    $('.swh-preview-code-switch').removeClass('d-none');
    // render notebook by default to keep existing behavior
    switchToPreview();
  } else if (isMarkdown(filename) || mimetype === 'text/html') {
    // for html rendering the process is only executed when user is
    // requesting preview
    if ($('.swh-preview-content').length) {
      $('.swh-preview-code-switch').removeClass('d-none');
      $('.swh-preview-content').css('display', 'none');
    }

    const url = new URL(window.location.href);
    if (url.searchParams.has('show_preview')) {
      switchToPreview();
    }
  }

  rawContent = $('code').text();

  // highlight code
  swh.webapp.highlightCode(true, '.swh-content code', enableLinesSelection);
}
