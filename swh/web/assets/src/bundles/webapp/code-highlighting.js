/**
 * Copyright (C) 2018-2019  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import {removeUrlFragment} from 'utils/functions';

export async function highlightCode(showLineNumbers = true) {

  await import(/* webpackChunkName: "highlightjs" */ 'utils/highlightjs');

  // keep track of the first highlighted line
  let firstHighlightedLine = null;
  // highlighting color
  let lineHighlightColor = 'rgb(193, 255, 193)';

  // function to highlight a line
  function highlightLine(i) {
    let lineTd = $(`.hljs-ln-line[data-line-number="${i}"]`);
    lineTd.css('background-color', lineHighlightColor);
    return lineTd;
  }

  // function to reset highlighting
  function resetHighlightedLines() {
    firstHighlightedLine = null;
    $('.hljs-ln-line[data-line-number]').css('background-color', 'inherit');
  }

  function scrollToLine(lineDomElt) {
    if ($(lineDomElt).closest('.swh-content').length > 0) {
      $('html, body').animate({
        scrollTop: $(lineDomElt).offset().top - 70
      }, 500);
    }
  }

  // function to highlight lines based on a url fragment
  // in the form '#Lx' or '#Lx-Ly'
  function parseUrlFragmentForLinesToHighlight() {
    let lines = [];
    let linesRegexp = new RegExp(/L(\d+)/g);
    let line = linesRegexp.exec(window.location.hash);
    if (line === null) {
      return;
    }
    while (line) {
      lines.push(parseInt(line[1]));
      line = linesRegexp.exec(window.location.hash);
    }
    resetHighlightedLines();
    if (lines.length === 1) {
      firstHighlightedLine = parseInt(lines[0]);
      scrollToLine(highlightLine(lines[0]));
    } else if (lines[0] < lines[lines.length - 1]) {
      firstHighlightedLine = parseInt(lines[0]);
      scrollToLine(highlightLine(lines[0]));
      for (let i = lines[0] + 1; i <= lines[lines.length - 1]; ++i) {
        highlightLine(i);
      }
    }
  }

  $(document).ready(() => {
    // highlight code and add line numbers
    $('code').each((i, elt) => {
      hljs.highlightElement(elt);
      if (showLineNumbers) {
        hljs.lineNumbersElement(elt, {singleLine: true});
      }
    });

    if (!showLineNumbers) {
      return;
    }

    // click handler to dynamically highlight line(s)
    // when the user clicks on a line number (lines range
    // can also be highlighted while holding the shift key)
    $('.swh-content').click(evt => {
      if (evt.target.classList.contains('hljs-ln-n')) {
        let line = parseInt($(evt.target).data('line-number'));
        if (evt.shiftKey && firstHighlightedLine && line > firstHighlightedLine) {
          let firstLine = firstHighlightedLine;
          resetHighlightedLines();
          for (let i = firstLine; i <= line; ++i) {
            highlightLine(i);
          }
          firstHighlightedLine = firstLine;
          window.location.hash = `#L${firstLine}-L${line}`;
        } else {
          resetHighlightedLines();
          highlightLine(line);
          window.location.hash = `#L${line}`;
          scrollToLine(evt.target);
        }
      } else if ($(evt.target).closest('.hljs-ln').length) {
        resetHighlightedLines();
        removeUrlFragment();
      }
    });

    // update lines highlighting when the url fragment changes
    $(window).on('hashchange', () => parseUrlFragmentForLinesToHighlight());

    // schedule lines highlighting if any as hljs.lineNumbersElement() is async
    setTimeout(() => {
      parseUrlFragmentForLinesToHighlight();
    });

  });
}
