/**
 * Copyright (C) 2019-2020  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

const $ = Cypress.$;
const origin = 'https://github.com/memononen/libtess2';
const revision = '98c65dad5e47ad888032b6cdf556f192e0e028d0';

const diffsHighlightingData = {
  'unified': {
    diffId: '3d4c0797cf0e89430410e088339aac384dfa4d82',
    startLines: [913, 915],
    endLines: [0, 979]
  },
  'split-from': {
    diffId: '602cec77c3d3f41d396d9e1083a0bbce0796b505',
    startLines: [192, 0],
    endLines: [198, 0]
  },
  'split-to': {
    diffId: '602cec77c3d3f41d396d9e1083a0bbce0796b505',
    startLines: [0, 120],
    endLines: [0, 130]
  },
  'split-from-top-to-bottom': {
    diffId: 'a00c33990655a93aa2c821c4008bbddda812a896',
    startLines: [63, 0],
    endLines: [0, 68]
  },
  'split-to-top-from-bottom': {
    diffId: 'a00c33990655a93aa2c821c4008bbddda812a896',
    startLines: [0, 63],
    endLines: [67, 0]
  }
};

let diffData;
let swh;

describe('Test Revision View', function() {

  it('should add/remove #swh-revision-changes url fragment when switching tab', function() {
    const url = this.Urls.browse_revision(revision) + `?origin=${origin}`;
    cy.visit(url);
    cy.get('a[data-toggle="tab"]')
      .contains('Changes')
      .click();
    cy.hash().should('be.equal', '#swh-revision-changes');
    cy.get('a[data-toggle="tab"]')
      .contains('Files')
      .click();
    cy.hash().should('be.equal', '');
  });

  it('should display Changes tab by default when url ends with #swh-revision-changes', function() {
    const url = this.Urls.browse_revision(revision) + `?origin=${origin}`;
    cy.visit(url + '#swh-revision-changes');
    cy.get('#swh-revision-changes-list')
      .should('be.visible');
  });
});

describe('Test Diffs View', function() {

  beforeEach(function() {
    const url = this.Urls.browse_revision(revision) + `?origin=${origin}`;
    cy.visit(url);
    cy.window().then(win => {
      swh = win.swh;
      cy.request(win.diffRevUrl)
        .then(res => {
          diffData = res.body;
        });
    });
    cy.get('a[data-toggle="tab"]')
      .contains('Changes')
      .click();
  });

  it('should list all files with changes', function() {
    let files = new Set([]);
    for (let change of diffData.changes) {
      files.add(change.from_path);
      files.add(change.to_path);
    }
    for (let file of files) {
      cy.get('#swh-revision-changes-list a')
        .contains(file)
        .should('be.visible');
    }
  });

  it('should load diffs when scrolled down', function() {
    cy.get('#swh-revision-changes-list a')
      .each($el => {
        cy.get($el.attr('href'))
          .scrollIntoView()
          .find('.swh-content')
          .should('be.visible');
      });
  });

  it('should compute all diffs when selected', function() {
    cy.get('#swh-compute-all-diffs')
      .click();
    cy.get('#swh-revision-changes-list a')
      .each($el => {
        cy.get($el.attr('href'))
          .find('.swh-content')
          .should('be.visible');
      });
  });

  it('should have correct links in diff file names', function() {
    for (let change of diffData.changes) {
      cy.get(`#swh-revision-changes-list a[href="#diff_${change.id}"`)
        .should('be.visible');
    }
  });

  it('should load unified diff by default', function() {
    cy.get('#swh-compute-all-diffs')
      .click();
    for (let change of diffData.changes) {
      cy.get(`#${change.id}-unified-diff`)
        .should('be.visible');
      cy.get(`#${change.id}-split-diff`)
        .should('not.be.visible');
    }
  });

  it('should switch between unified and side-by-side diff when selected', function() {
    // Test for first diff
    const id = diffData.changes[0].id;
    cy.get(`#diff_${id}`)
      .contains('label', 'Side-by-side')
      .click();
    cy.get(`#${id}-split-diff`)
      .should('be.visible')
      .get(`#${id}-unified-diff`)
      .should('not.be.visible');
  });

  function checkDiffHighlighted(diffId, start, end) {
    cy.get(`#${diffId} .hljs-ln-line`)
      .then(lines => {
        let inHighlightedRange = false;
        for (let line of lines) {
          const lnNumber = $(line).data('line-number');
          if (lnNumber === start || lnNumber === end) {
            inHighlightedRange = true;
          }
          const backgroundColor = $(line).css('background-color');
          const mixBlendMode = $(line).css('mix-blend-mode');
          if (inHighlightedRange && parseInt(lnNumber)) {
            assert.equal(mixBlendMode, 'multiply');
            assert.notEqual(backgroundColor, 'rgba(0, 0, 0, 0)');
          } else {
            assert.equal(mixBlendMode, 'normal');
            assert.equal(backgroundColor, 'rgba(0, 0, 0, 0)');
          }
          if (lnNumber === end) {
            inHighlightedRange = false;
          }
        }
      });
  }

  function unifiedDiffHighlightingTest(diffId, startLines, endLines) {
    // render diff
    cy.get(`#diff_${diffId}`)
      .scrollIntoView()
      .get(`#${diffId}-unified-diff`)
      .should('be.visible')
      // ensure all asynchronous treatments in the page have been performed
      // before testing diff highlighting
      .then(() => {

        let startLinesStr = swh.revision.formatDiffLineNumbers(diffId, startLines[0], startLines[1]);
        let endLinesStr = swh.revision.formatDiffLineNumbers(diffId, endLines[0], endLines[1]);

        // highlight a range of lines
        let startElt = `#${diffId}-unified-diff .hljs-ln-numbers[data-line-number="${startLinesStr}"]`;
        let endElt = `#${diffId}-unified-diff .hljs-ln-numbers[data-line-number="${endLinesStr}"]`;
        cy.get(startElt).click();
        cy.get(endElt).click({shiftKey: true});

        // check URL fragment has been updated
        const selectedLinesFragment =
          swh.revision.selectedDiffLinesToFragment(startLines, endLines, true);
        cy.hash().should('be.equal', `#diff_${diffId}+${selectedLinesFragment}`);

        if ($(endElt).position().top < $(startElt).position().top) {
          [startLinesStr, endLinesStr] = [endLinesStr, startLinesStr];
        }

        // check lines range is highlighted
        checkDiffHighlighted(`${diffId}-unified-diff`, startLinesStr, endLinesStr);

        // check selected diff lines get highlighted when reloading page
        // with highlighting info in URL fragment
        cy.reload();
        cy.get(`#diff_${diffId}`)
          .get(`#${diffId}-unified-diff`)
          .should('be.visible');

        checkDiffHighlighted(`${diffId}-unified-diff`, startLinesStr, endLinesStr);
      });
  }

  it('should highlight unified diff lines when selecting them from top to bottom', function() {

    const diffHighlightingData = diffsHighlightingData['unified'];
    const diffId = diffHighlightingData.diffId;
    let startLines = diffHighlightingData.startLines;
    let endLines = diffHighlightingData.endLines;

    unifiedDiffHighlightingTest(diffId, startLines, endLines);

  });

  it('should highlight unified diff lines when selecting them from bottom to top', function() {

    const diffHighlightingData = diffsHighlightingData['unified'];
    const diffId = diffHighlightingData.diffId;
    let startLines = diffHighlightingData.startLines;
    let endLines = diffHighlightingData.endLines;

    unifiedDiffHighlightingTest(diffId, endLines, startLines);

  });

  function singleSpitDiffHighlightingTest(diffId, startLines, endLines, to) {

    let singleDiffId = `${diffId}-from`;
    if (to) {
      singleDiffId = `${diffId}-to`;
    }

    let startLine = startLines[0] || startLines[1];
    let endLine = endLines[0] || endLines[1];

    // render diff
    cy.get(`#diff_${diffId}`)
      .scrollIntoView()
      .get(`#${diffId}-unified-diff`)
      .should('be.visible');

    cy.get(`#diff_${diffId}`)
      .contains('label', 'Side-by-side')
      .click()
      // ensure all asynchronous treatments in the page have been performed
      // before testing diff highlighting
      .then(() => {
        // highlight a range of lines
        let startElt = `#${singleDiffId} .hljs-ln-numbers[data-line-number="${startLine}"]`;
        let endElt = `#${singleDiffId} .hljs-ln-numbers[data-line-number="${endLine}"]`;
        cy.get(startElt).click();
        cy.get(endElt).click({shiftKey: true});

        const selectedLinesFragment =
          swh.revision.selectedDiffLinesToFragment(startLines, endLines, false);

        // check URL fragment has been updated
        cy.hash().should('be.equal', `#diff_${diffId}+${selectedLinesFragment}`);

        if ($(endElt).position().top < $(startElt).position().top) {
          [startLine, endLine] = [endLine, startLine];
        }

        // check lines range is highlighted
        checkDiffHighlighted(`${singleDiffId}`, startLine, endLine);

        // check selected diff lines get highlighted when reloading page
        // with highlighting info in URL fragment
        cy.reload();
        cy.get(`#diff_${diffId}`)
          .get(`#${diffId}-split-diff`)
          .get(`#${singleDiffId}`)
          .should('be.visible');
        checkDiffHighlighted(`${singleDiffId}`, startLine, endLine);
      });
  }

  it('should highlight split diff from lines when selecting them from top to bottom', function() {
    const diffHighlightingData = diffsHighlightingData['split-from'];
    const diffId = diffHighlightingData.diffId;
    let startLines = diffHighlightingData.startLines;
    let endLines = diffHighlightingData.endLines;

    singleSpitDiffHighlightingTest(diffId, startLines, endLines, false);
  });

  it('should highlight split diff from lines when selecting them from bottom to top', function() {
    const diffHighlightingData = diffsHighlightingData['split-from'];
    const diffId = diffHighlightingData.diffId;
    let startLines = diffHighlightingData.startLines;
    let endLines = diffHighlightingData.endLines;

    singleSpitDiffHighlightingTest(diffId, endLines, startLines, false);
  });

  it('should highlight split diff to lines when selecting them from top to bottom', function() {
    const diffHighlightingData = diffsHighlightingData['split-to'];
    const diffId = diffHighlightingData.diffId;
    let startLines = diffHighlightingData.startLines;
    let endLines = diffHighlightingData.endLines;

    singleSpitDiffHighlightingTest(diffId, startLines, endLines, true);
  });

  it('should highlight split diff to lines when selecting them from bottom to top', function() {

    const diffHighlightingData = diffsHighlightingData['split-to'];
    const diffId = diffHighlightingData.diffId;
    let startLines = diffHighlightingData.startLines;
    let endLines = diffHighlightingData.endLines;

    singleSpitDiffHighlightingTest(diffId, endLines, startLines, true);
  });

  function checkSplitDiffHighlighted(diffId, startLines, endLines) {
    let left, right;
    if (startLines[0] && endLines[1]) {
      left = startLines[0];
      right = endLines[1];
    } else {
      left = endLines[0];
      right = startLines[1];
    }

    cy.get(`#${diffId}-from .hljs-ln-line`)
      .then(fromLines => {
        cy.get(`#${diffId}-to .hljs-ln-line`)
          .then(toLines => {
            const leftLine = $(`#${diffId}-from .hljs-ln-line[data-line-number="${left}"]`);
            const rightLine = $(`#${diffId}-to .hljs-ln-line[data-line-number="${right}"]`);
            const leftLineAbove = $(leftLine).position().top < $(rightLine).position().top;
            let inHighlightedRange = false;
            for (let i = 0; i < Math.max(fromLines.length, toLines.length); ++i) {
              const fromLn = fromLines[i];
              const toLn = toLines[i];
              const fromLnNumber = $(fromLn).data('line-number');
              const toLnNumber = $(toLn).data('line-number');

              if ((leftLineAbove && fromLnNumber === left) ||
                  (!leftLineAbove && toLnNumber === right) ||
                  (leftLineAbove && toLnNumber === right) ||
                  (!leftLineAbove && fromLnNumber === left)) {
                inHighlightedRange = true;
              }

              if (fromLn) {
                const fromBackgroundColor = $(fromLn).css('background-color');
                const fromMixBlendMode = $(fromLn).css('mix-blend-mode');
                if (inHighlightedRange && fromLnNumber) {
                  assert.equal(fromMixBlendMode, 'multiply');
                  assert.notEqual(fromBackgroundColor, 'rgba(0, 0, 0, 0)');
                } else {
                  assert.equal(fromMixBlendMode, 'normal');
                  assert.equal(fromBackgroundColor, 'rgba(0, 0, 0, 0)');
                }
              }

              if (toLn) {
                const toBackgroundColor = $(toLn).css('background-color');
                const toMixBlendMode = $(toLn).css('mix-blend-mode');
                if (inHighlightedRange && toLnNumber) {
                  assert.equal(toMixBlendMode, 'multiply');
                  assert.notEqual(toBackgroundColor, 'rgba(0, 0, 0, 0)');
                } else {
                  assert.equal(toMixBlendMode, 'normal');
                  assert.equal(toBackgroundColor, 'rgba(0, 0, 0, 0)');
                }
              }

              if ((leftLineAbove && toLnNumber === right) ||
                  (!leftLineAbove && fromLnNumber === left)) {
                inHighlightedRange = false;
              }
            }
          });
      });
  }

  function splitDiffHighlightingTest(diffId, startLines, endLines) {
    // render diff
    cy.get(`#diff_${diffId}`)
      .scrollIntoView()
      .find(`#${diffId}-unified-diff`)
      .should('be.visible');

    cy.get(`#diff_${diffId}`)
      .contains('label', 'Side-by-side')
      .click()
      // ensure all asynchronous treatments in the page have been performed
      // before testing diff highlighting
      .then(() => {

        // select lines range in diff
        let startElt;
        if (startLines[0]) {
          startElt = `#${diffId}-from .hljs-ln-numbers[data-line-number="${startLines[0]}"]`;
        } else {
          startElt = `#${diffId}-to .hljs-ln-numbers[data-line-number="${startLines[1]}"]`;
        }
        let endElt;
        if (endLines[0]) {
          endElt = `#${diffId}-from .hljs-ln-numbers[data-line-number="${endLines[0]}"]`;
        } else {
          endElt = `#${diffId}-to .hljs-ln-numbers[data-line-number="${endLines[1]}"]`;
        }

        cy.get(startElt).click();
        cy.get(endElt).click({shiftKey: true});

        const selectedLinesFragment =
            swh.revision.selectedDiffLinesToFragment(startLines, endLines, false);

        // check URL fragment has been updated
        cy.hash().should('be.equal', `#diff_${diffId}+${selectedLinesFragment}`);

        // check lines range is highlighted
        checkSplitDiffHighlighted(diffId, startLines, endLines);

        // check selected diff lines get highlighted when reloading page
        // with highlighting info in URL fragment
        cy.reload();
        cy.get(`#diff_${diffId}`)
            .get(`#${diffId}-split-diff`)
            .get(`#${diffId}-to`)
            .should('be.visible');

        checkSplitDiffHighlighted(diffId, startLines, endLines);
      });
  }

  it('should highlight split diff from and to lines when selecting them from top-left to bottom-right', function() {
    const diffHighlightingData = diffsHighlightingData['split-from-top-to-bottom'];
    const diffId = diffHighlightingData.diffId;
    let startLines = diffHighlightingData.startLines;
    let endLines = diffHighlightingData.endLines;

    splitDiffHighlightingTest(diffId, startLines, endLines);
  });

  it('should highlight split diff from and to lines when selecting them from bottom-right to top-left', function() {
    const diffHighlightingData = diffsHighlightingData['split-from-top-to-bottom'];
    const diffId = diffHighlightingData.diffId;
    let startLines = diffHighlightingData.startLines;
    let endLines = diffHighlightingData.endLines;

    splitDiffHighlightingTest(diffId, endLines, startLines);
  });

  it('should highlight split diff from and to lines when selecting them from top-right to bottom-left', function() {
    const diffHighlightingData = diffsHighlightingData['split-to-top-from-bottom'];
    const diffId = diffHighlightingData.diffId;
    let startLines = diffHighlightingData.startLines;
    let endLines = diffHighlightingData.endLines;

    splitDiffHighlightingTest(diffId, startLines, endLines);
  });

  it('should highlight split diff from and to lines when selecting them from bottom-left to top-right', function() {
    const diffHighlightingData = diffsHighlightingData['split-to-top-from-bottom'];
    const diffId = diffHighlightingData.diffId;
    let startLines = diffHighlightingData.startLines;
    let endLines = diffHighlightingData.endLines;

    splitDiffHighlightingTest(diffId, endLines, startLines);
  });

  it('should highlight diff lines properly when a content is browsed in the Files tab', function() {
    const url = this.Urls.browse_revision(revision) + `?origin=${origin}&path=README.md`;
    cy.visit(url);
    cy.get('a[data-toggle="tab"]')
      .contains('Changes')
      .click();
    const diffHighlightingData = diffsHighlightingData['unified'];
    const diffId = diffHighlightingData.diffId;
    let startLines = diffHighlightingData.startLines;
    let endLines = diffHighlightingData.endLines;

    unifiedDiffHighlightingTest(diffId, startLines, endLines);

  });

});
