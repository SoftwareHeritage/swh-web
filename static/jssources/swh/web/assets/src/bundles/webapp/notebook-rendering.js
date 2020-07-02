/**
 * Copyright (C) 2019-2020  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import 'script-loader!notebookjs';
import AnsiUp from 'ansi_up';
import './notebook.css';

const ansiup = new AnsiUp();
ansiup.escape_for_html = false;

function escapeHTML(text) {
  text = text.replace(/</g, '&lt;');
  text = text.replace(/>/g, '&gt;');
  return text;
}

function unescapeHTML(text) {
  text = text.replace(/&lt;/g, '<');
  text = text.replace(/&gt;/g, '>');
  return text;
}

function escapeLaTeX(text) {

  let blockMath = /\$\$(.+?)\$\$|\\\\\[(.+?)\\\\\]/msg;
  let inlineMath = /\$(.+?)\$|\\\\\((.+?)\\\\\)/g;
  let latexEnvironment = /\\begin\{([a-z]*\*?)\}(.+?)\\end\{\1\}/msg;

  let mathTextFound = [];
  let bm;
  while ((bm = blockMath.exec(text)) !== null) {
    mathTextFound.push(bm[1]);
  }

  let im;
  while ((im = inlineMath.exec(text)) !== null) {
    mathTextFound.push(im[1]);
  }

  let le;
  while ((le = latexEnvironment.exec(text)) !== null) {
    mathTextFound.push(le[1]);
  }

  for (let mathText of mathTextFound) {
    // showdown will remove line breaks in LaTex array and
    // some escaping sequences when converting md to html.
    // So we use the following escaping hacks to keep them in the html
    // output and avoid MathJax typesetting errors.
    let escapedText = mathText.replace('\\\\', '\\\\\\\\');
    for (let specialLaTexChar of ['{', '}', '#', '%', '&', '_']) {
      escapedText = escapedText.replace(new RegExp(`\\\\${specialLaTexChar}`, 'g'),
                                        `\\\\${specialLaTexChar}`);
    }

    // some html escaping is also needed
    escapedText = escapeHTML(escapedText);

    // hack to prevent showdown to replace _ characters
    // by html em tags as it will break some math typesetting
    // (setting the literalMidWordUnderscores option is not
    // enough as iy only works for _ characters contained in words)
    escapedText = escapedText.replace(/_/g, '{@}underscore{@}');

    if (mathText !== escapedText) {
      text = text.replace(mathText, escapedText);
    }
  }

  return text;
}

export async function renderNotebook(nbJsonUrl, domElt) {

  let showdown = await import(/* webpackChunkName: "showdown" */ 'utils/showdown');

  await import(/* webpackChunkName: "highlightjs" */ 'utils/highlightjs');

  function renderMarkdown(text) {
    let converter = new showdown.Converter({
      tables: true,
      simplifiedAutoLink: true,
      rawHeaderId: true,
      literalMidWordUnderscores: true
    });

    // some LaTeX escaping is required to get correct math typesetting
    text = escapeLaTeX(text);

    // render markdown
    let rendered = converter.makeHtml(text);

    // restore underscores in rendered HTML (see escapeLaTeX function)
    rendered = rendered.replace(/{@}underscore{@}/g, '_');

    return rendered;
  }

  function highlightCode(text, preElt, codeElt, lang) {
    // no need to unescape text processed by ansiup
    if (text.indexOf('<span style="color:rgb(') === -1) {
      text = unescapeHTML(text);
    }
    if (lang && hljs.getLanguage(lang)) {
      return hljs.highlight(lang, text).value;
    } else {
      return text;
    }
  }

  function renderAnsi(text) {
    return ansiup.ansi_to_html(text);
  }

  nb.markdown = renderMarkdown;
  nb.highlighter = highlightCode;
  nb.ansi = renderAnsi;

  fetch(nbJsonUrl)
    .then(response => response.json())
    .then(nbJson => {
      // parse the notebook
      let notebook = nb.parse(nbJson);
      // render it to HTML and apply XSS filtering
      let rendered = swh.webapp.filterXSS(notebook.render());
      // insert rendered notebook in the DOM
      $(domElt).append(rendered);
      // set light red background color for stderr output cells
      $('pre.nb-stderr').parent().css('background', '#fdd');
      // load MathJax library for math typesetting
      swh.webapp.typesetMath();
    });
}
