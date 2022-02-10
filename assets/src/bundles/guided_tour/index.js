/**
 * Copyright (C) 2021  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import introJs from 'intro.js';
import 'intro.js/introjs.css';
import './swh-introjs.css';
import guidedTourSteps from './guided-tour-steps.yaml';
import {disableScrolling, enableScrolling} from 'utils/scrolling';

let guidedTour = [];
let tour = null;
let previousElement = null;
// we use a origin available both in production and swh-web tests
// environment to ease tour testing
const originUrl = 'https://github.com/memononen/libtess2';
// sha1 for the content used
const contentSha1 = 'sha1_git:2d4e23bf1d3f64c1e8b94622178e18d89c653de0';

function openSWHIDsTabBeforeNextStep() {
  window.scrollTo(0, 0);
  if (!$('#swh-identifiers').tabSlideOut('isOpen')) {
    $('.introjs-helperLayer, .introjs-tooltipReferenceLayer').hide();
    $('#swh-identifiers').tabSlideOut('open');
    setTimeout(() => {
      $('.introjs-helperLayer, .introjs-tooltipReferenceLayer').show();
      tour.nextStep();
    }, 500);
    return false;
  }
  return true;
}

// init guided tour configuration when page loads in order
// to hack on it in cypress tests
$(() => {
  // tour is defined by an array of objects containing:
  //   - URL of page to run a tour
  //   - intro.js configuration with tour steps
  //   - optional intro.js callback function for tour interactivity
  guidedTour = [
    {
      url: Urls.swh_web_homepage(),
      introJsOptions: {
        disableInteraction: true,
        scrollToElement: false,
        steps: guidedTourSteps.homepage
      }
    },
    {
      url: `${Urls.browse_origin_directory()}?origin_url=${originUrl}`,
      introJsOptions: {
        disableInteraction: true,
        scrollToElement: false,
        steps: guidedTourSteps.browseOrigin
      },
      onBeforeChange: function(targetElement) {
        // open SWHIDs tab before its tour step
        if (targetElement && targetElement.id === 'swh-identifiers') {
          return openSWHIDsTabBeforeNextStep();
        }
        return true;
      }
    },
    {
      url: `${Urls.browse_content(contentSha1)}?origin_url=${originUrl}&path=Example/example.c`,
      introJsOptions: {
        steps: guidedTourSteps.browseContent
      },
      onBeforeChange: function(targetElement) {
        const lineNumberStart = 11;
        const lineNumberEnd = 17;
        if (targetElement && $(targetElement).hasClass('swhid')) {
          return openSWHIDsTabBeforeNextStep();
        // forbid move to next step until user clicks on line numbers
        } else if (targetElement && targetElement.dataset.lineNumber === `${lineNumberEnd}`) {
          const background = $(`.hljs-ln-numbers[data-line-number="${lineNumberStart}"]`).css('background-color');
          const canGoNext = background !== 'rgba(0, 0, 0, 0)';
          if (!canGoNext && $('#swh-next-step-disabled').length === 0) {
            $('.introjs-tooltiptext').append(
              `<p id="swh-next-step-disabled" style="color: red; font-weight: bold">
                  You need to select the line number before proceeding to<br/>next step.
               </p>`);
          }
          previousElement = targetElement;
          return canGoNext;
        } else if (previousElement && previousElement.dataset.lineNumber === `${lineNumberEnd}`) {
          let canGoNext = true;
          for (let i = lineNumberStart; i <= lineNumberEnd; ++i) {
            const background = $(`.hljs-ln-numbers[data-line-number="${i}"]`).css('background-color');
            canGoNext = canGoNext && background !== 'rgba(0, 0, 0, 0)';
            if (!canGoNext) {
              swh.webapp.resetHighlightedLines();
              swh.webapp.scrollToLine(swh.webapp.highlightLine(lineNumberStart, true));
              if ($('#swh-next-step-disabled').length === 0) {
                $('.introjs-tooltiptext').append(
                  `<p id="swh-next-step-disabled" style="color: red; font-weight: bold">
                      You need to select the line numbers range from ${lineNumberStart}
                      to ${lineNumberEnd} before proceeding to next step.
                  </p>`);
              }
              break;
            }
          }
          return canGoNext;
        }
        previousElement = targetElement;
        return true;
      }
    }
  ];
  // init guided tour on page if guided_tour query parameter is present
  const searchParams = new URLSearchParams(window.location.search);
  if (searchParams && searchParams.has('guided_tour')) {
    initGuidedTour(parseInt(searchParams.get('guided_tour')));
  }
});

export function getGuidedTour() {
  return guidedTour;
}

export function guidedTourButtonClick(event) {
  event.preventDefault();
  initGuidedTour();
}

export function initGuidedTour(page = 0) {
  if (page >= guidedTour.length) {
    return;
  }
  const pageUrl = new URL(window.location.origin + guidedTour[page].url);
  const currentUrl = new URL(window.location.href);
  const guidedTourNext = currentUrl.searchParams.get('guided_tour_next');
  currentUrl.searchParams.delete('guided_tour');
  currentUrl.searchParams.delete('guided_tour_next');
  const pageUrlStr = decodeURIComponent(pageUrl.toString());
  const currentUrlStr = decodeURIComponent(currentUrl.toString());
  if (currentUrlStr !== pageUrlStr) {
    // go to guided tour page URL if current one does not match
    pageUrl.searchParams.set('guided_tour', page);
    if (page === 0) {
      // user will be redirected to the page he was at the end of the tour
      pageUrl.searchParams.set('guided_tour_next', currentUrlStr);
    }
    window.location = decodeURIComponent(pageUrl.toString());
  } else {
    // create intro.js guided tour and configure it
    tour = introJs().setOptions(guidedTour[page].introJsOptions);
    tour.setOptions({
      'exitOnOverlayClick': false,
      'showBullets': false
    });
    if (page < guidedTour.length - 1) {
      // if not on the last page of the tour, rename next button label
      // and schedule next page loading when clicking on it
      tour.setOption('doneLabel', 'Next page')
          .onexit(() => {
            // re-enable page scrolling when exiting tour
            enableScrolling();
          })
          .oncomplete(() => {
            const nextPageUrl = new URL(window.location.origin + guidedTour[page + 1].url);
            nextPageUrl.searchParams.set('guided_tour', page + 1);
            if (guidedTourNext) {
              nextPageUrl.searchParams.set('guided_tour_next', guidedTourNext);
            } else if (page === 0) {
              nextPageUrl.searchParams.set('guided_tour_next', currentUrlStr);
            }
            window.location.href = decodeURIComponent(nextPageUrl.toString());
          });
    } else {
      tour.oncomplete(() => {
        enableScrolling(); // re-enable page scrolling when tour is complete
        if (guidedTourNext) {
          window.location.href = guidedTourNext;
        }
      });
    }
    if (guidedTour[page].hasOwnProperty('onBeforeChange')) {
      tour.onbeforechange(guidedTour[page].onBeforeChange);
    }
    setTimeout(() => {
      // run guided tour with a little delay to ensure every asynchronous operations
      // after page load have been executed
      disableScrolling(); // disable page scrolling with mouse or keyboard while tour runs.
      tour.start();
      window.scrollTo(0, 0);
    }, 500);
  }
};
