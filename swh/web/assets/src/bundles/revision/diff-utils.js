/**
 * Copyright (C) 2018-2019  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import 'waypoints/lib/jquery.waypoints';

import {staticAsset} from 'utils/functions';

// path to static spinner asset
let swhSpinnerSrc = staticAsset('img/swh-spinner.gif');
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

// to check if a DOM element is in the viewport
function isInViewport(elt) {
  let elementTop = $(elt).offset().top;
  let elementBottom = elementTop + $(elt).outerHeight();

  let viewportTop = $(window).scrollTop();
  let viewportBottom = viewportTop + $(window).height();

  return elementBottom > viewportTop && elementTop < viewportBottom;
}

// to format the diffs line numbers
function formatDiffLineNumbers(fromLine, toLine, maxNumberChars) {
  let ret = '';
  if (fromLine != null) {
    for (let i = 0; i < (maxNumberChars - fromLine.length); ++i) {
      ret += ' ';
    }
    ret += fromLine;
  }
  if (fromLine != null && toLine != null) {
    ret += '  ';
  }
  if (toLine != null) {
    for (let i = 0; i < (maxNumberChars - toLine.length); ++i) {
      ret += ' ';
    }
    ret += toLine;
  }
  return ret;
}

// to compute diff and process it for display
export function computeDiff(diffUrl, diffId) {

  // force diff computation ?
  let force = diffUrl.indexOf('force=true') !== -1;

  // it no forced computation and diff already computed, do nothing
  if (!force && computedDiffs.hasOwnProperty(diffId)) {
    return;
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
          hljs.lineNumbersBlock(block);
        });

        // hljs.lineNumbersBlock is asynchronous so we have to postpone our
        // next treatments by adding it at the end of the current js events queue
        setTimeout(() => {

          // process unified diff lines in order to generate side-by-side diffs text
          // but also compute line numbers for unified and side-by-side diffs
          let linesInfoRegExp = new RegExp(/^@@ -(\d+),(\d+) \+(\d+),(\d+) @@$/gm);
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
            let linesInfo = linesInfoRegExp.exec(lnText);
            let fromLine = '';
            let toLine = '';
            // parsed lines info from the diff output
            if (linesInfo) {
              baseFromLine = parseInt(linesInfo[1]) - 1;
              baseToLine = parseInt(linesInfo[3]) - 1;
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

          // set side-by-side diffs text
          $(`#${diffId}-from`).text(diffFromStr);
          $(`#${diffId}-to`).text(diffToStr);

          // code highlighting for side-by-side diffs
          $(`#${diffId}-from, #${diffId}-to`).each((i, block) => {
            hljs.highlightBlock(block);
            hljs.lineNumbersBlock(block);
          });

          // hljs.lineNumbersBlock is asynchronous so we have to postpone our
          // next treatments by adding it at the end of the current js events queue
          setTimeout(() => {
            // diff highlighting for added/removed lines on top of code highlighting
            $(`.${diffId} .hljs-ln-numbers`).each((i, lnElt) => {
              let lnText = lnElt.nextSibling.innerText;
              let linesInfo = linesInfoRegExp.exec(lnText);
              if (linesInfo) {
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
              $(lnElt).children().attr(
                'data-line-number',
                formatDiffLineNumbers(fromToLines[i][0], fromToLines[i][1],
                                      maxNumberChars));
            });

            // set line numbers for the from side-by-side diff
            $(`#${diffId}-from .hljs-ln-numbers`).each((i, lnElt) => {
              $(lnElt).children().attr(
                'data-line-number',
                formatDiffLineNumbers(fromLines[i], null,
                                      maxNumberChars));
            });

            // set line numbers for the to side-by-side diff
            $(`#${diffId}-to .hljs-ln-numbers`).each((i, lnElt) => {
              $(lnElt).children().attr(
                'data-line-number',
                formatDiffLineNumbers(null, toLines[i],
                                      maxNumberChars));
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
              $(`#panel_${diffId} .diff-styles`).css('visibility', 'visible');
            }

            setDiffVisible(diffId);

          });
        });
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
      let diffId = elt.id.replace('panel_', '');
      computeDiff(diffsUrls[diffId], diffId);
    }
  });
}

function genDiffPanel(diffData) {
  let diffPanelTitle = diffData.path;
  if (diffData.type === 'rename') {
    diffPanelTitle = `${diffData.from_path} &rarr; ${diffData.to_path}`;
  }
  let diffPanelHtml =
  `<div id="panel_${diffData.id}" class="card swh-file-diff-panel">
    <div class="card-header bg-gray-light border-bottom-0">
      <a data-toggle="collapse" href="#panel_${diffData.id}_content">
        <div class="pull-left swh-title-color">
          <strong>${diffPanelTitle}</strong>
        </div>
      </a>
      <div class="pull-right">
        <div class="btn-group btn-group-toggle diff-styles" data-toggle="buttons" style="visibility: hidden;">
          <label class="btn btn-default btn-sm form-check-label active unified-diff-button" onclick="swh.revision.showUnifiedDiff(event, '${diffData.id}')">
            <input type="radio" name="diffs-switch" id="unified" autocomplete="off" checked> Unified
          </label>
          <label class="btn btn-default btn-sm form-check-label splitted-diff-button" onclick="swh.revision.showSplittedDiff(event, '${diffData.id}')">
            <input type="radio" name="diffs-switch" id="side-by-side" autocomplete="off"> Side-by-side
          </label>
        </div>
        <a href="${diffData.content_url}" class="btn btn-default btn-sm" role="button">View file</a>
      </div>
      <div class="clearfix"></div>
    </div>
    <div id="panel_${diffData.id}_content" class="collapse show">
      <div class="swh-diff-loading text-center" id="${diffData.id}-loading" style="visibility: hidden;">
        <img src=${swhSpinnerSrc}></img>
        <p>Loading diff ...</p>
      </div>
      <div class="highlightjs swh-content" style="display: none;" id="${diffData.id}-highlightjs">
        <div id="${diffData.id}-unified-diff">
          <pre><code class="${diffData.id}" id="${diffData.id}"></code></pre>
        </div>
        <div style="width: 100%; display: none;" id="${diffData.id}-splitted-diff">
          <pre class="float-left" style="width: 50%;"><code class="${diffData.id}" id="${diffData.id}-from"></code></pre>
          <pre style="width: 50%"><code class="${diffData.id}" id="${diffData.id}-to"></code></pre>
        </div>
      </div>
    </div>
  </div>`;
  return diffPanelHtml;
}

// setup waypoints to request diffs computation on the fly while scrolling
function setupWaypoints() {
  for (let i = 0; i < changes.length; ++i) {
    let diffData = changes[i];

    // create a waypoint that will trigger diff computation when
    // the top of the diff panel hits the bottom of the viewport
    $(`#panel_${diffData.id}`).waypoint({
      handler: function() {
        if (isInViewport(this.element)) {
          let diffId = this.element.id.replace('panel_', '');
          computeDiff(diffsUrls[diffId], diffId);
          this.destroy();
        }
      },
      offset: '100%'
    });

    // create a waypoint that will trigger diff computation when
    // the bottom of the diff panel hits the top of the viewport
    $(`#panel_${diffData.id}`).waypoint({
      handler: function() {
        if (isInViewport(this.element)) {
          let diffId = this.element.id.replace('panel_', '');
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

// callback to switch from side-by-side diff to unified one
export function showUnifiedDiff(event, diffId) {
  $(`#${diffId}-splitted-diff`).css('display', 'none');
  $(`#${diffId}-unified-diff`).css('display', 'block');
}

// callback to switch from unified diff to side-by-side one
export function showSplittedDiff(event, diffId) {
  $(`#${diffId}-unified-diff`).css('display', 'none');
  $(`#${diffId}-splitted-diff`).css('display', 'block');
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
    if (e.currentTarget.text.trim() === 'Changes') {

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
        });
    } else if (e.currentTarget.text.trim() === 'Files') {
      $('#readme-panel').css('display', 'block');
    }
  });

  $(document).ready(() => {

    if (revisionMessageBody.length > 0) {
      $('#swh-revision-message').addClass('in');
    } else {
      $('#swh-collapse-revision-message').attr('data-toggle', '');
    }

    let $root = $('html, body');

    // callback when the user requests to scroll on a specific diff or back to top
    $('#swh-revision-changes-list a[href^="#"], #back-to-top a[href^="#"]').click(e => {
      let href = $.attr(e.currentTarget, 'href');
      // disable waypoints while scrolling as we do not want to
      // launch computation of diffs the user is not interested in
      // (file changes list can be large)
      Waypoint.disableAll();

      $root.animate(
        {
          scrollTop: $(href).offset().top
        },
        {
          duration: 500,
          complete: () => {
            window.location.hash = href;
            // enable waypoints back after scrolling
            Waypoint.enableAll();
            // compute diffs visible in the viewport
            computeVisibleDiffs();
          }
        });

      return false;
    });

  });

}
