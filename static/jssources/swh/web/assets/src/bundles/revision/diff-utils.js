/**
 * Copyright (C) 2018-2020  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import 'waypoints/lib/jquery.waypoints';

import {swhSpinnerSrc} from 'utils/constants';
import {removeUrlFragment} from 'utils/functions';

import diffPanelTemplate from './diff-panel.ejs';

// number of changed files in the revision
let changes = null;
let nbChangedFiles = 0;
// to track the number of already computed files diffs
let nbDiffsComputed = 0;

// the no newline at end of file marker from Github
let noNewLineMarker = '<span class="no-nl-marker" title="No newline at end of file">' +
                        '<svg aria-hidden="true" height="16" version="1.1" viewBox="0 0 16 16" width="16">' +
                          '<path fill-rule="evenodd" d="M16 5v3c0 .55-.45 1-1 1h-3v2L9 8l3-3v2h2V5h2zM8 8c0 2.2-1.8 4-4 4s-4-1.8-4-4 1.8-4 4-4 4 1.8 4 4zM1.5 9.66L5.66 5.5C5.18 5.19 4.61 5 4 5 2.34 5 1 6.34 1 8c0 .61.19 1.17.5 1.66zM7 8c0-.61-.19-1.17-.5-1.66L2.34 10.5c.48.31 1.05.5 1.66.5 1.66 0 3-1.34 3-3z"></path>' +
                        '</svg>' +
                      '</span>';

// to track the total number of added lines in files diffs
let nbAdditions = 0;
// to track the total number of deleted lines in files diffs
let nbDeletions = 0;
// to track the already computed diffs by id
let computedDiffs = {};
// map a diff id to its computation url
let diffsUrls = {};
// to keep track of diff lines to highlight
let startLines = null;
let endLines = null;
// map max line numbers characters to diff
const diffMaxNumberChars = {};
// focused diff for highlighting
let focusedDiff = null;
// highlighting color
const lineHighlightColor = '#fdf3da';
// might contain diff lines to highlight parsed from URL fragment
let selectedDiffLinesInfo;
// URL fragment to append when switching to 'Changes' tab
const changesUrlFragment = '#swh-revision-changes';
// current displayed tab name
let currentTabName = 'Files';

// to check if a DOM element is in the viewport
function isInViewport(elt) {
  let elementTop = $(elt).offset().top;
  let elementBottom = elementTop + $(elt).outerHeight();

  let viewportTop = $(window).scrollTop();
  let viewportBottom = viewportTop + $(window).height();

  return elementBottom > viewportTop && elementTop < viewportBottom;
}

// to format the diffs line numbers
export function formatDiffLineNumbers(diffId, fromLine, toLine) {
  const maxNumberChars = diffMaxNumberChars[diffId];
  const fromLineStr = toLnStr(fromLine);
  const toLineStr = toLnStr(toLine);
  let ret = '';
  for (let i = 0; i < (maxNumberChars - fromLineStr.length); ++i) {
    ret += ' ';
  }
  ret += fromLineStr;
  ret += '  ';
  for (let i = 0; i < (maxNumberChars - toLineStr.length); ++i) {
    ret += ' ';
  }
  ret += toLineStr;
  return ret;
}

function parseDiffHunkRangeIfAny(lineText) {
  let baseFromLine, baseToLine;
  if (lineText.startsWith('@@')) {
    let linesInfoRegExp = new RegExp(/^@@ -(\d+),(\d+) \+(\d+),(\d+) @@$/gm);
    let linesInfoRegExp2 = new RegExp(/^@@ -(\d+) \+(\d+),(\d+) @@$/gm);
    let linesInfoRegExp3 = new RegExp(/^@@ -(\d+),(\d+) \+(\d+) @@$/gm);
    let linesInfoRegExp4 = new RegExp(/^@@ -(\d+) \+(\d+) @@$/gm);
    let linesInfo = linesInfoRegExp.exec(lineText);
    let linesInfo2 = linesInfoRegExp2.exec(lineText);
    let linesInfo3 = linesInfoRegExp3.exec(lineText);
    let linesInfo4 = linesInfoRegExp4.exec(lineText);
    if (linesInfo) {
      baseFromLine = parseInt(linesInfo[1]) - 1;
      baseToLine = parseInt(linesInfo[3]) - 1;
    } else if (linesInfo2) {
      baseFromLine = parseInt(linesInfo2[1]) - 1;
      baseToLine = parseInt(linesInfo2[2]) - 1;
    } else if (linesInfo3) {
      baseFromLine = parseInt(linesInfo3[1]) - 1;
      baseToLine = parseInt(linesInfo3[3]) - 1;
    } else if (linesInfo4) {
      baseFromLine = parseInt(linesInfo4[1]) - 1;
      baseToLine = parseInt(linesInfo4[2]) - 1;
    }
  }
  if (baseFromLine !== undefined) {
    return [baseFromLine, baseToLine];
  } else {
    return null;
  }
}

function toLnInt(lnStr) {
  return lnStr ? parseInt(lnStr) : 0;
};

function toLnStr(lnInt) {
  return lnInt ? lnInt.toString() : '';
};

// parse diff line numbers to an int array [from, to]
export function parseDiffLineNumbers(lineNumbersStr, from, to) {
  let lines;
  if (!from && !to) {
    lines = lineNumbersStr.replace(/[ ]+/g, ' ').split(' ');
    if (lines.length > 2) {
      lines.shift();
    }
    lines = lines.map(x => toLnInt(x));
  } else {
    let lineNumber = toLnInt(lineNumbersStr.trim());
    if (from) {
      lines = [lineNumber, 0];
    } else if (to) {
      lines = [0, lineNumber];
    }
  }
  return lines;
}

// serialize selected line numbers range to string for URL fragment
export function selectedDiffLinesToFragment(startLines, endLines, unified) {
  let selectedLinesFragment = '';
  selectedLinesFragment += `F${startLines[0] || 0}`;
  selectedLinesFragment += `T${startLines[1] || 0}`;
  selectedLinesFragment += `-F${endLines[0] || 0}`;
  selectedLinesFragment += `T${endLines[1] || 0}`;
  if (unified) {
    selectedLinesFragment += '-unified';
  } else {
    selectedLinesFragment += '-split';
  }
  return selectedLinesFragment;
}

// parse selected lines from URL fragment
export function fragmentToSelectedDiffLines(fragment) {
  const RE_LINES = /F([0-9]+)T([0-9]+)-F([0-9]+)T([0-9]+)-([a-z]+)/;
  const matchObj = RE_LINES.exec(fragment);
  if (matchObj.length === 6) {
    return {
      startLines: [parseInt(matchObj[1]), parseInt(matchObj[2])],
      endLines: [parseInt(matchObj[3]), parseInt(matchObj[4])],
      unified: matchObj[5] === 'unified'
    };
  } else {
    return null;
  }
}

// function to highlight a single diff line
function highlightDiffLine(diffId, i) {
  let line = $(`#${diffId} .hljs-ln-line[data-line-number="${i}"]`);
  let lineNumbers = $(`#${diffId} .hljs-ln-numbers[data-line-number="${i}"]`);
  lineNumbers.css('color', 'black');
  lineNumbers.css('font-weight', 'bold');
  line.css('background-color', lineHighlightColor);
  line.css('mix-blend-mode', 'multiply');
  return line;
}

// function to reset highlighting
function resetHighlightedDiffLines(resetVars = true) {
  if (resetVars) {
    focusedDiff = null;
    startLines = null;
    endLines = null;
  }
  $('.hljs-ln-line[data-line-number]').css('background-color', 'initial');
  $('.hljs-ln-line[data-line-number]').css('mix-blend-mode', 'initial');
  $('.hljs-ln-numbers[data-line-number]').css('color', '#aaa');
  $('.hljs-ln-numbers[data-line-number]').css('font-weight', 'initial');
  if (currentTabName === 'Changes' && window.location.hash !== changesUrlFragment) {
    window.history.replaceState('', document.title,
                                window.location.pathname + window.location.search + changesUrlFragment);
  }
}

// highlight lines in a diff, return first highlighted line numbers element
function highlightDiffLines(diffId, startLines, endLines, unified) {
  let firstHighlightedLine;
  // unified diff case
  if (unified) {
    let start = formatDiffLineNumbers(diffId, startLines[0], startLines[1]);
    let end = formatDiffLineNumbers(diffId, endLines[0], endLines[1]);

    const startLine = $(`#${diffId} .hljs-ln-line[data-line-number="${start}"]`);
    const endLine = $(`#${diffId} .hljs-ln-line[data-line-number="${end}"]`);
    if ($(endLine).position().top < $(startLine).position().top) {
      [start, end] = [end, start];
      firstHighlightedLine = endLine;
    } else {
      firstHighlightedLine = startLine;
    }
    const lineTd = highlightDiffLine(diffId, start);
    let tr = $(lineTd).closest('tr');
    let lineNumbers = $(tr).children('.hljs-ln-line').data('line-number').toString();
    while (lineNumbers !== end) {
      if (lineNumbers.trim()) {
        highlightDiffLine(diffId, lineNumbers);
      }
      tr = $(tr).next();
      lineNumbers = $(tr).children('.hljs-ln-line').data('line-number').toString();
    }
    highlightDiffLine(diffId, end);

  // split diff case
  } else {
    // highlight only from part of the diff
    if (startLines[0] && endLines[0]) {
      const start = Math.min(startLines[0], endLines[0]);
      const end = Math.max(startLines[0], endLines[0]);
      for (let i = start; i <= end; ++i) {
        highlightDiffLine(`${diffId}-from`, i);
      }
      firstHighlightedLine = $(`#${diffId}-from .hljs-ln-line[data-line-number="${start}"]`);
    // highlight only to part of the diff
    } else if (startLines[1] && endLines[1]) {
      const start = Math.min(startLines[1], endLines[1]);
      const end = Math.max(startLines[1], endLines[1]);
      for (let i = start; i <= end; ++i) {
        highlightDiffLine(`${diffId}-to`, i);
      }
      firstHighlightedLine = $(`#${diffId}-to .hljs-ln-line[data-line-number="${start}"]`);
    // highlight both part of the diff
    } else {
      let left, right;
      if (startLines[0] && endLines[1]) {
        left = startLines[0];
        right = endLines[1];
      } else {
        left = endLines[0];
        right = startLines[1];
      }

      const leftLine = $(`#${diffId}-from .hljs-ln-line[data-line-number="${left}"]`);
      const rightLine = $(`#${diffId}-to .hljs-ln-line[data-line-number="${right}"]`);
      const leftLineAbove = $(leftLine).position().top < $(rightLine).position().top;

      if (leftLineAbove) {
        firstHighlightedLine = leftLine;
      } else {
        firstHighlightedLine = rightLine;
      }

      let fromTr = $(`#${diffId}-from tr`).first();
      let fromLn = $(fromTr).children('.hljs-ln-line').data('line-number');
      let toTr = $(`#${diffId}-to tr`).first();
      let toLn = $(toTr).children('.hljs-ln-line').data('line-number');
      let canHighlight = false;

      while (true) {
        if (leftLineAbove && fromLn === left) {
          canHighlight = true;
        } else if (!leftLineAbove && toLn === right) {
          canHighlight = true;
        }

        if (canHighlight && fromLn) {
          highlightDiffLine(`${diffId}-from`, fromLn);
        }

        if (canHighlight && toLn) {
          highlightDiffLine(`${diffId}-to`, toLn);
        }

        if ((leftLineAbove && toLn === right) || (!leftLineAbove && fromLn === left)) {
          break;
        }

        fromTr = $(fromTr).next();
        fromLn = $(fromTr).children('.hljs-ln-line').data('line-number');
        toTr = $(toTr).next();
        toLn = $(toTr).children('.hljs-ln-line').data('line-number');
      }

    }
  }

  let selectedLinesFragment = selectedDiffLinesToFragment(startLines, endLines, unified);
  window.location.hash = `diff_${diffId}+${selectedLinesFragment}`;
  return firstHighlightedLine;
}

// callback to switch from side-by-side diff to unified one
export function showUnifiedDiff(diffId) {
  $(`#${diffId}-split-diff`).css('display', 'none');
  $(`#${diffId}-unified-diff`).css('display', 'block');
}

// callback to switch from unified diff to side-by-side one
export function showSplitDiff(diffId) {
  $(`#${diffId}-unified-diff`).css('display', 'none');
  $(`#${diffId}-split-diff`).css('display', 'block');
}

// to compute diff and process it for display
export function computeDiff(diffUrl, diffId) {

  // force diff computation ?
  let force = diffUrl.indexOf('force=true') !== -1;

  // it no forced computation and diff already computed, do nothing
  if (!force && computedDiffs.hasOwnProperty(diffId)) {
    return;
  }

  function setLineNumbers(lnElt, lineNumbers) {
    $(lnElt).attr('data-line-number', lineNumbers || '');
    $(lnElt).children().attr('data-line-number', lineNumbers || '');
    $(lnElt).siblings().attr('data-line-number', lineNumbers || '');
  }

  // mark diff computation as already requested
  computedDiffs[diffId] = true;

  $(`#${diffId}-loading`).css('visibility', 'visible');

  // set spinner visible while requesting diff
  $(`#${diffId}-loading`).css('display', 'block');
  $(`#${diffId}-highlightjs`).css('display', 'none');

  // request diff computation and process it
  fetch(diffUrl)
    .then(response => response.json())
    .then(data => {
      // increment number of computed diffs
      ++nbDiffsComputed;
      // toggle the 'Compute all diffs' button if all diffs have been computed
      if (nbDiffsComputed === changes.length) {
        $('#swh-compute-all-diffs').addClass('active');
      }

      // Large diff (> threshold) are not automatically computed,
      // add a button to force its computation
      if (data.diff_str.indexOf('Large diff') === 0) {
        $(`#${diffId}`)[0].innerHTML = data.diff_str +
          `<br/><button class="btn btn-default btn-sm" type="button"
           onclick="swh.revision.computeDiff('${diffUrl}&force=true', '${diffId}')">` +
           'Request diff</button>';
        setDiffVisible(diffId);
      } else if (data.diff_str.indexOf('@@') !== 0) {
        $(`#${diffId}`).text(data.diff_str);
        setDiffVisible(diffId);
      } else {

        // prepare code highlighting
        $(`.${diffId}`).removeClass('nohighlight');
        $(`.${diffId}`).addClass(data.language);

        // set unified diff text
        $(`#${diffId}`).text(data.diff_str);

        // code highlighting for unified diff
        $(`#${diffId}`).each((i, block) => {
          hljs.highlightBlock(block);
          hljs.lineNumbersBlockSync(block);
        });

        // process unified diff lines in order to generate side-by-side diffs text
        // but also compute line numbers for unified and side-by-side diffs
        let baseFromLine = '';
        let baseToLine = '';
        let fromToLines = [];
        let fromLines = [];
        let toLines = [];
        let maxNumberChars = 0;
        let diffFromStr = '';
        let diffToStr = '';
        let linesOffset = 0;

        $(`#${diffId} .hljs-ln-numbers`).each((i, lnElt) => {
          let lnText = lnElt.nextSibling.innerText;
          let linesInfo = parseDiffHunkRangeIfAny(lnText);
          let fromLine = '';
          let toLine = '';
          // parsed lines info from the diff output
          if (linesInfo) {
            baseFromLine = linesInfo[0];
            baseToLine = linesInfo[1];
            linesOffset = 0;
            diffFromStr += (lnText + '\n');
            diffToStr += (lnText + '\n');
            fromLines.push('');
            toLines.push('');
          // line removed in the from file
          } else if (lnText.length > 0 && lnText[0] === '-') {
            baseFromLine = baseFromLine + 1;
            fromLine = baseFromLine.toString();
            fromLines.push(fromLine);
            ++nbDeletions;
            diffFromStr += (lnText + '\n');
            ++linesOffset;
          // line added in the to file
          } else if (lnText.length > 0 && lnText[0] === '+') {
            baseToLine = baseToLine + 1;
            toLine = baseToLine.toString();
            toLines.push(toLine);
            ++nbAdditions;
            diffToStr += (lnText + '\n');
            --linesOffset;
          // line present in both files
          } else {
            baseFromLine = baseFromLine + 1;
            baseToLine = baseToLine + 1;
            fromLine = baseFromLine.toString();
            toLine = baseToLine.toString();
            for (let j = 0; j < Math.abs(linesOffset); ++j) {
              if (linesOffset > 0) {
                diffToStr += '\n';
                toLines.push('');
              } else {
                diffFromStr += '\n';
                fromLines.push('');
              }
            }
            linesOffset = 0;
            diffFromStr += (lnText + '\n');
            diffToStr += (lnText + '\n');
            toLines.push(toLine);
            fromLines.push(fromLine);
          }
          if (!baseFromLine) {
            fromLine = '';
          }
          if (!baseToLine) {
            toLine = '';
          }
          fromToLines[i] = [fromLine, toLine];
          maxNumberChars = Math.max(maxNumberChars, fromLine.length);
          maxNumberChars = Math.max(maxNumberChars, toLine.length);
        });

        diffMaxNumberChars[diffId] = maxNumberChars;

        // set side-by-side diffs text
        $(`#${diffId}-from`).text(diffFromStr);
        $(`#${diffId}-to`).text(diffToStr);

        // code highlighting for side-by-side diffs
        $(`#${diffId}-from, #${diffId}-to`).each((i, block) => {
          hljs.highlightBlock(block);
          hljs.lineNumbersBlockSync(block);
        });

        // diff highlighting for added/removed lines on top of code highlighting
        $(`.${diffId} .hljs-ln-numbers`).each((i, lnElt) => {
          let lnText = lnElt.nextSibling.innerText;
          if (lnText.startsWith('@@')) {
            $(lnElt).parent().addClass('swh-diff-lines-info');
            let linesInfoText = $(lnElt).parent().find('.hljs-ln-code .hljs-ln-line').text();
            $(lnElt).parent().find('.hljs-ln-code .hljs-ln-line').children().remove();
            $(lnElt).parent().find('.hljs-ln-code .hljs-ln-line').text('');
            $(lnElt).parent().find('.hljs-ln-code .hljs-ln-line').append(`<span class="hljs-meta">${linesInfoText}</span>`);
          } else if (lnText.length > 0 && lnText[0] === '-') {
            $(lnElt).parent().addClass('swh-diff-removed-line');
          } else if (lnText.length > 0 && lnText[0] === '+') {
            $(lnElt).parent().addClass('swh-diff-added-line');
          }
        });

        // set line numbers for unified diff
        $(`#${diffId} .hljs-ln-numbers`).each((i, lnElt) => {
          const lineNumbers = formatDiffLineNumbers(diffId, fromToLines[i][0], fromToLines[i][1]);
          setLineNumbers(lnElt, lineNumbers);
        });

        // set line numbers for the from side-by-side diff
        $(`#${diffId}-from .hljs-ln-numbers`).each((i, lnElt) => {
          setLineNumbers(lnElt, fromLines[i]);
        });

        // set line numbers for the to side-by-side diff
        $(`#${diffId}-to .hljs-ln-numbers`).each((i, lnElt) => {
          setLineNumbers(lnElt, toLines[i]);
        });

        // last processing:
        //  - remove the '+' and '-' at the beginning of the diff lines
        //    from code highlighting
        //  - add the "no new line at end of file marker" if needed
        $(`.${diffId} .hljs-ln-code`).each((i, lnElt) => {
          if (lnElt.firstChild) {
            if (lnElt.firstChild.nodeName !== '#text') {
              let lineText = lnElt.firstChild.innerHTML;
              if (lineText[0] === '-' || lineText[0] === '+') {
                lnElt.firstChild.innerHTML = lineText.substr(1);
                let newTextNode = document.createTextNode(lineText[0]);
                $(lnElt).prepend(newTextNode);
              }
            }
            $(lnElt).contents().filter((i, elt) => {
              return elt.nodeType === 3; // Node.TEXT_NODE
            }).each((i, textNode) => {
              let swhNoNewLineMarker = '[swh-no-nl-marker]';
              if (textNode.textContent.indexOf(swhNoNewLineMarker) !== -1) {
                textNode.textContent = textNode.textContent.replace(swhNoNewLineMarker, '');
                $(lnElt).append($(noNewLineMarker));
              }
            });
          }
        });

        // hide the diff mode switch button in case of not generated diffs
        if (data.diff_str.indexOf('Diffs are not generated for non textual content') !== 0) {
          $(`#diff_${diffId} .diff-styles`).css('visibility', 'visible');
        }

        setDiffVisible(diffId);

        // highlight diff lines if provided in URL fragment
        if (selectedDiffLinesInfo &&
              selectedDiffLinesInfo.diffPanelId.indexOf(diffId) !== -1) {
          if (!selectedDiffLinesInfo.unified) {
            showSplitDiff(diffId);
          }
          const firstHighlightedLine = highlightDiffLines(
            diffId, selectedDiffLinesInfo.startLines,
            selectedDiffLinesInfo.endLines, selectedDiffLinesInfo.unified);

          $('html, body').animate(
            {
              scrollTop: firstHighlightedLine.offset().top - 50
            },
            {
              duration: 500
            }
          );
        }
      }
    });
}

function setDiffVisible(diffId) {
  // set the unified diff visible by default
  $(`#${diffId}-loading`).css('display', 'none');
  $(`#${diffId}-highlightjs`).css('display', 'block');

  // update displayed counters
  $('#swh-revision-lines-added').text(`${nbAdditions} additions`);
  $('#swh-revision-lines-deleted').text(`${nbDeletions} deletions`);
  $('#swh-nb-diffs-computed').text(nbDiffsComputed);

  // refresh the waypoints triggering diffs computation as
  // the DOM layout has been updated
  Waypoint.refreshAll();
}

// to compute all visible diffs in the viewport
function computeVisibleDiffs() {
  $('.swh-file-diff-panel').each((i, elt) => {
    if (isInViewport(elt)) {
      let diffId = elt.id.replace('diff_', '');
      computeDiff(diffsUrls[diffId], diffId);
    }
  });
}

function genDiffPanel(diffData) {
  let diffPanelTitle = diffData.path;
  if (diffData.type === 'rename') {
    diffPanelTitle = `${diffData.from_path} &rarr; ${diffData.to_path}`;
  }
  return diffPanelTemplate({
    diffData: diffData,
    diffPanelTitle: diffPanelTitle,
    swhSpinnerSrc: swhSpinnerSrc
  });
}

// setup waypoints to request diffs computation on the fly while scrolling
function setupWaypoints() {
  for (let i = 0; i < changes.length; ++i) {
    let diffData = changes[i];

    // create a waypoint that will trigger diff computation when
    // the top of the diff panel hits the bottom of the viewport
    $(`#diff_${diffData.id}`).waypoint({
      handler: function() {
        if (isInViewport(this.element)) {
          let diffId = this.element.id.replace('diff_', '');
          computeDiff(diffsUrls[diffId], diffId);
          this.destroy();
        }
      },
      offset: '100%'
    });

    // create a waypoint that will trigger diff computation when
    // the bottom of the diff panel hits the top of the viewport
    $(`#diff_${diffData.id}`).waypoint({
      handler: function() {
        if (isInViewport(this.element)) {
          let diffId = this.element.id.replace('diff_', '');
          computeDiff(diffsUrls[diffId], diffId);
          this.destroy();
        }
      },
      offset: function() {
        return -$(this.element).height();
      }
    });
  }
  Waypoint.refreshAll();
}

function scrollToDiffPanel(diffPanelId, setHash = true) {
  // disable waypoints while scrolling as we do not want to
  // launch computation of diffs the user is not interested in
  // (file changes list can be large)
  Waypoint.disableAll();

  $('html, body').animate(
    {
      scrollTop: $(diffPanelId).offset().top
    },
    {
      duration: 500,
      complete: () => {
        if (setHash) {
          window.location.hash = diffPanelId;
        }
        // enable waypoints back after scrolling
        Waypoint.enableAll();
        // compute diffs visible in the viewport
        computeVisibleDiffs();
      }
    });
}

// callback when the user clicks on the 'Compute all diffs' button
export function computeAllDiffs(event) {
  $(event.currentTarget).addClass('active');
  for (let diffId in diffsUrls) {
    if (diffsUrls.hasOwnProperty(diffId)) {
      computeDiff(diffsUrls[diffId], diffId);
    }
  }
  event.stopPropagation();
}

export async function initRevisionDiff(revisionMessageBody, diffRevisionUrl) {

  await import(/* webpackChunkName: "highlightjs" */ 'utils/highlightjs');

  // callback when the 'Changes' tab is activated
  $(document).on('shown.bs.tab', 'a[data-toggle="tab"]', e => {
    currentTabName = e.currentTarget.text.trim();
    if (currentTabName === 'Changes') {
      window.location.hash = changesUrlFragment;
      $('#readme-panel').css('display', 'none');

      if (changes) {
        return;
      }

      // request computation of revision file changes list
      // when navigating to the 'Changes' tab and add diff panels
      // to the DOM when receiving the result
      fetch(diffRevisionUrl)
        .then(response => response.json())
        .then(data => {
          changes = data.changes;
          nbChangedFiles = data.total_nb_changes;
          let changedFilesText = `${nbChangedFiles} changed file`;
          if (nbChangedFiles !== 1) {
            changedFilesText += 's';
          }
          $('#swh-revision-changed-files').text(changedFilesText);
          $('#swh-total-nb-diffs').text(changes.length);
          $('#swh-revision-changes-list pre')[0].innerHTML = data.changes_msg;

          $('#swh-revision-changes-loading').css('display', 'none');
          $('#swh-revision-changes-list pre').css('display', 'block');
          $('#swh-compute-all-diffs').css('visibility', 'visible');
          $('#swh-revision-changes-list').removeClass('in');

          if (nbChangedFiles > changes.length) {
            $('#swh-too-large-revision-diff').css('display', 'block');
            $('#swh-nb-loaded-diffs').text(changes.length);
          }

          for (let i = 0; i < changes.length; ++i) {
            let diffData = changes[i];
            diffsUrls[diffData.id] = diffData.diff_url;
            $('#swh-revision-diffs').append(genDiffPanel(diffData));
          }

          setupWaypoints();
          computeVisibleDiffs();

          if (selectedDiffLinesInfo) {
            scrollToDiffPanel(selectedDiffLinesInfo.diffPanelId, false);
          }

        });
    } else if (currentTabName === 'Files') {
      removeUrlFragment();
      $('#readme-panel').css('display', 'block');
    }
  });

  $(document).ready(() => {

    if (revisionMessageBody.length > 0) {
      $('#swh-revision-message').addClass('in');
    } else {
      $('#swh-collapse-revision-message').attr('data-toggle', '');
    }

    // callback when the user requests to scroll on a specific diff or back to top
    $('#swh-revision-changes-list a[href^="#"], #back-to-top a[href^="#"]').click(e => {
      let href = $.attr(e.currentTarget, 'href');
      scrollToDiffPanel(href);
      return false;
    });

    // click callback for highlighting diff lines
    $('body').click(evt => {

      if (currentTabName !== 'Changes') {
        return;
      }

      if (evt.target.classList.contains('hljs-ln-n')) {

        const diffId = $(evt.target).closest('code').prop('id');

        const from = diffId.indexOf('-from') !== -1;
        const to = diffId.indexOf('-to') !== -1;

        const lineNumbers = $(evt.target).data('line-number').toString();

        const currentDiff = diffId.replace('-from', '').replace('-to', '');
        if (!evt.shiftKey || currentDiff !== focusedDiff || !lineNumbers.trim()) {
          resetHighlightedDiffLines();
          focusedDiff = currentDiff;
        }
        if (currentDiff === focusedDiff && lineNumbers.trim()) {
          if (!evt.shiftKey) {
            startLines = parseDiffLineNumbers(lineNumbers, from, to);
            highlightDiffLines(currentDiff, startLines, startLines, !from && !to);
          } else if (startLines) {
            resetHighlightedDiffLines(false);
            endLines = parseDiffLineNumbers(lineNumbers, from, to);
            highlightDiffLines(currentDiff, startLines, endLines, !from && !to);
          }
        }

      } else {
        resetHighlightedDiffLines();
      }
    });

    // if an URL fragment for highlighting a diff is present
    // parse highlighting info and initiate diff loading
    const fragment = window.location.hash;
    if (fragment) {
      const split = fragment.split('+');
      if (split.length === 2) {
        selectedDiffLinesInfo = fragmentToSelectedDiffLines(split[1]);
        if (selectedDiffLinesInfo) {
          selectedDiffLinesInfo.diffPanelId = split[0];
          $(`.nav-tabs a[href="${changesUrlFragment}"]`).tab('show');
        }
      }
      if (fragment === changesUrlFragment) {
        $(`.nav-tabs a[href="${changesUrlFragment}"]`).tab('show');
      }
    }

  });

}
