/**
 * Copyright (C) 2018-2021  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import {removeUrlFragment} from 'utils/functions';

// keep track of the first highlighted line
let firstHighlightedLine = null;
// highlighting color
const lineHighlightColor = 'rgb(193, 255, 193)';

// function to highlight a line
export function highlightLine(i, firstHighlighted = false) {
  const lineTd = $(`.hljs-ln-line[data-line-number="${i}"]`);
  lineTd.css('background-color', lineHighlightColor);
  if (firstHighlighted) {
    firstHighlightedLine = i;
  }
  return lineTd;
}

// function to highlight a range of lines
export function highlightLines(first, last) {
  if (!first) {
    return;
  }
  if (!last) {
    last = first;
  }
  for (let i = first; i <= last; ++i) {
    highlightLine(i);
  }
}

// function to reset highlighting
export function resetHighlightedLines() {
  firstHighlightedLine = null;
  $('.hljs-ln-line[data-line-number]').css('background-color', 'inherit');
}

export function scrollToLine(lineDomElt, offset = 70) {
  if ($(lineDomElt).closest('.swh-content').length > 0) {
    $('html, body').animate({
      scrollTop: $(lineDomElt).offset().top - offset
    }, 500);
  }
}

export async function highlightCode(showLineNumbers = true, selector = 'code',
                                    enableLinesSelection = true) {

  await import(/* webpackChunkName: "highlightjs" */ 'utils/highlightjs');

  // function to highlight lines based on a url fragment
  // in the form '#Lx' or '#Lx-Ly'
  function parseUrlFragmentForLinesToHighlight() {
    const lines = [];
    const linesRegexp = new RegExp(/L(\d+)/g);
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
      highlightLines(lines[0] + 1, lines[lines.length - 1]);
    }
  }

  $(document).ready(() => {
    // highlight code and add line numbers
    $(selector).each((i, elt) => {
      $(elt).removeAttr('data-highlighted');
      hljs.highlightElement(elt);
      if (showLineNumbers) {
        hljs.lineNumbersElement(elt, {singleLine: true});
        setTimeout(() => {
          $('.hljs-ln').attr('role', 'presentation');
        });
      }
    });

    if (!showLineNumbers || !enableLinesSelection) {
      return;
    }

    // click handler to dynamically highlight line(s)
    // when the user clicks on a line number (lines range
    // can also be highlighted while holding the shift key)
    $('.swh-content').click(evt => {
      if (evt.target.classList.contains('hljs-ln-n')) {
        const line = parseInt($(evt.target).data('line-number'));
        if (evt.shiftKey && firstHighlightedLine && line > firstHighlightedLine) {
          const firstLine = firstHighlightedLine;
          resetHighlightedLines();
          highlightLines(firstLine, line);
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
