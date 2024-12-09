/**
 * Copyright (C) 2018-2024  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import ClipboardJS from 'clipboard';
import {handleFetchError} from 'utils/functions';
import 'thirdparty/jquery.tabSlideOut/jquery.tabSlideOut';
import 'thirdparty/jquery.tabSlideOut/jquery.tabSlideOut.css';
import Prism from 'prismjs';
import 'prismjs/themes/prism-coy.css';
import 'prismjs-bibtex';

export function swhIdObjectTypeToggled(event) {
  event.preventDefault();
  $(event.target).tab('show');
}

function updateDisplayedSWHID(contextOptionCheckBox) {
  const swhIdElt = $(contextOptionCheckBox).closest('.swhid-ui').find('.swhid');
  const swhIdWithContext = $(contextOptionCheckBox).data('swhid-with-context');
  const swhIdWithContextUrl = $(contextOptionCheckBox).data('swhid-with-context-url');
  let currentSwhId = swhIdElt.text();
  if ($(contextOptionCheckBox).prop('checked')) {
    swhIdElt.attr('href', swhIdWithContextUrl);
    currentSwhId = swhIdWithContext.replace(/;/g, ';\n');
  } else {
    const pos = currentSwhId.indexOf(';');
    if (pos !== -1) {
      currentSwhId = currentSwhId.slice(0, pos);
    }
    swhIdElt.attr('href', '/' + currentSwhId);
  }
  swhIdElt.text(currentSwhId);

  addLinesInfo();
}

export function swhIdContextOptionToggled(event) {
  event.stopPropagation();
  updateDisplayedSWHID(event.target);
}

function computeLinesQualifier() {
  const lines = [];
  let linesPart = ';lines=';
  const linesRegexp = new RegExp(/L(\d+)/g);
  let line = linesRegexp.exec(window.location.hash);
  while (line) {
    lines.push(parseInt(line[1]));
    line = linesRegexp.exec(window.location.hash);
  }
  if (lines.length > 0) {
    linesPart += lines[0];
  }
  if (lines.length > 1) {
    linesPart += '-' + lines[1];
  }
  if (lines.length > 0) {
    return linesPart;
  } else {
    return null;
  }
}

function addLinesInfo() {
  const swhIdElt = $('#swhid-tab-content').find('.swhid');
  let currentSwhId = swhIdElt.text().replace(/;\n/g, ';');

  const linesPart = computeLinesQualifier();

  const contextOptionCheckBox = $('#swhid-context-option-content');
  if (contextOptionCheckBox.prop('checked')) {
    let swhIdWithContextUrl = contextOptionCheckBox.data('swhid-with-context-url');
    currentSwhId = currentSwhId.replace(/;lines=\d+-*\d*/g, '');
    if (linesPart) {
      currentSwhId += linesPart;
      swhIdWithContextUrl += linesPart;
    }

    swhIdElt.text(currentSwhId.replace(/;/g, ';\n'));
    swhIdElt.attr('href', swhIdWithContextUrl);
  }
}

function updateTabsSize() {
  // update tabs width based on browser windows width
  $('.swh-side-tab').css('width', Math.min(window.innerWidth - 45, 1000) + 'px');
  // update tabs anchor top position based on browser windows height
  const top = window.innerHeight >= 700 ? 250 : 35;
  $('.swh-side-tab').css('top', top + 'px');
  // move citations tab handle below the permalinks one
  $('#swh-citations .handle').css('top', '105px');

  // backup current display states for tab contents
  const currentSWHIDsDisplay = $('#swh-identifiers-content').css('display');
  const currentCitationsDisplay = $('#swh-citations-content').css('display');

  // reset tabs height to be automatically computed
  $('.swh-side-tab').css('height', 'auto');
  // ensure tabs content are displayed for current height computation
  $('.swh-tab-side-content').css('display', 'block');

  // update tabs height to fit in the screen (its content is scrollable in case of overflow)
  function updateTabHeight(tabId) {
    if (top + $(tabId).height() > window.innerHeight) {
      $(tabId).css('height', (window.innerHeight - top - 5) + 'px');
    }
  }
  updateTabHeight('#swh-identifiers');
  updateTabHeight('#swh-citations');

  // hide badges and iframes links on display with small height
  $('#swh-identifiers .swh-badges-iframe').css('display', window.innerHeight >= 700 ? 'flex' : 'none');
  // hide badges and iframes links on display with small width
  $('#swh-identifiers .swh-badges-iframe').css('display', window.innerWidth >= 700 ? 'flex' : 'none');
  // restore current display state for tab content
  $('#swh-identifiers-content').css('display', currentSWHIDsDisplay);
  $('#swh-citations-content').css('display', currentCitationsDisplay);
}

function activateCitationsUI() {
  return JSON.parse($('#activate_citations_ui').text());
}

export async function generateCitationFromSWHID(objectType) {
  const swhidsContext = swh.webapp.getSwhIdsContext();
  let qualifiedSWHID = swhidsContext[objectType].swhid;
  if (swhidsContext[objectType].swhid_with_context_url) {
    qualifiedSWHID = swhidsContext[objectType].swhid_with_context_url.slice(1);
  }

  if (objectType === 'content') {
    const linesPart = computeLinesQualifier();
    if (linesPart) {
      qualifiedSWHID += linesPart;
    }
  }
  const citationFormat = $(`#citation-format-option-${objectType}`).val().toLowerCase();
  const citationUrl = Urls.api_1_raw_intrinsic_citation_swhid_get() +
    `?citation_format=${citationFormat}&target_swhid=${qualifiedSWHID}`;

  try {
    const response = await fetch(citationUrl);
    handleFetchError(response);
    // make Citations tab visible when a citation can be successfully generated
    $('#swh-citations').removeClass('d-none');
    const citation = await response.json();
    const html = Prism.highlight(citation.content, Prism.languages.bibtex, 'bibtex');
    $(`#citation-tab-${objectType} .swh-citation`).html(html);
    $(`#citation-tab-${objectType} .btn-citation-copy`).attr('disabled', false);
    $(`#citation-source-${objectType}`).html(
      '<a target="_blank" rel="noopener noreferrer" ' +
      `href="${Urls.browse_swhid(citation.source_swhid)}">Browse citation metadata</a>`);
  } catch (response) {
    const errorData = await response.json();
    $(`#citation-tab-${objectType} .swh-citation`).text(
      'Software citation could not be generated due to the following reason:\n\n' +
      errorData.reason);
    $(`#citation-tab-${objectType} .btn-citation-copy`).attr('disabled', true);
    if (response.status === 400) {
      $(`#citation-source-${objectType}`).html(
        '<a target="_blank" rel="noopener noreferrer" ' +
        `href="${Urls.browse_swhid(errorData.source_swhid)}">Browse citation metadata</a>`);
      // make Citations tab visible when a citation cannot be successfully generated
      // from metadata to give some insights to the user
      $('#swh-citations').removeClass('d-none');
    } else {
      $(`#citation-source-${objectType}`).html('');
    }
  }
};

export async function generateCitationForObjectType(event) {
  await generateCitationFromSWHID($(event.target).text().trim());
};

export async function initSideTabs() {

  $(document).ready(() => {
    const toggleButtonText = (button, text) => {
      const currentLabel = button.innerHTML;

      if (currentLabel === text) {
        return;
      }

      button.innerHTML = text;
      setTimeout(function() {
        button.innerHTML = currentLabel;
      }, 1000);
    };

    new ClipboardJS('.btn-swhid-copy', {
      text: trigger => {
        const swhId = $(trigger).closest('.swhid-ui').find('.swhid').text();
        return swhId.replace(/;\n/g, ';');
      }
    }).on('success', function(e) {
      toggleButtonText(e.trigger, 'Copied!');
    });

    new ClipboardJS('.btn-swhid-url-copy', {
      text: trigger => {
        const swhIdUrl = $(trigger).closest('.swhid-ui').find('.swhid').attr('href');
        return window.location.origin + swhIdUrl;
      }
    }).on('success', function(e) {
      toggleButtonText(e.trigger, 'Copied!');
    });

    // prevent automatic closing of SWHIDs tab during guided tour
    // as it is displayed programmatically
    function clickScreenToCloseFilter() {
      return $('.introjs-overlay').length > 0;
    }

    function toggleTabContentDisplay(tabId, show) {
      $(`${tabId}-content`).css('display', show ? 'block' : 'none');
      $(tabId).css('z-index', show ? '40000' : '30000');
      $(`${tabId} .handle`).css('padding-bottom', show ? '0.4em' : '0.1em');
    }

    const tabSlideOptionsSWHIDs = {
      tabLocation: 'right',
      action: null, // required to implement custom behavior when clicking on tab handle
      clickScreenToCloseFilters: [clickScreenToCloseFilter, '.ui-slideouttab-panel', '.modal'],
      onBeforeOpen: function() {
        $('#swh-identifiers').data('opening', true);
        if (!$('#swh-citations').data('opening')) {
          // open citations tab along the SWHIDs one
          $('#swh-citations').trigger('open');
        }
        toggleTabContentDisplay('#swh-identifiers', true);
        toggleTabContentDisplay('#swh-citations', false);
        return true;
      },
      onOpen: function() {
        $('#swh-identifiers').data('opening', false);
        $('#swhids-handle').attr('aria-expanded', 'true');
        $('#swhids-handle').attr('aria-label', 'Collapse permalinks tab');
      },
      onBeforeClose: function() {
        $('#swh-identifiers').data('closing', true);
        if (!$('#swh-citations').data('closing')) {
          // close citations tab along the SWHIDs one
          $('#swh-citations').trigger('close');
        }
        return true;
      },
      onClose: function() {
        $('#swh-identifiers').data('closing', false);
        $('#swhids-handle').attr('aria-expanded', 'false');
        $('#swhids-handle').attr('aria-label', 'Expand permalinks tab');
        $('#swhids-handle').css('padding-bottom', '0.1em');
        setTimeout(() => {
          // ensure elements in closed SWHIDs tab are not keyboard focusable
          $('#swh-identifiers-content').css('display', 'none');
        }, 500);
      }
    };

    // initiate the sliding SWHIDs tab
    $('#swh-identifiers').tabSlideOut(tabSlideOptionsSWHIDs);
    // override default behavior when clicking on tab handle
    $('#swh-identifiers .handle').on('click', event => {
      event.preventDefault();
      if ($('#swh-identifiers').tabSlideOut('isOpen')) {
        if ($('#swh-identifiers-content').css('display') === 'none') {
          // display SWHIDs tab content if not visible
          toggleTabContentDisplay('#swh-identifiers', true);
          toggleTabContentDisplay('#swh-citations', false);
        } else {
          $('#swh-identifiers').trigger('close');
        }
      } else {
        $('#swh-identifiers').trigger('open');
      }
    });

    // ensure qualified SWHIDs are displayed by default
    $('.swhid-context-option').each(function(i, elt) {
      updateDisplayedSWHID(elt);
    });

    if (activateCitationsUI() || swh.webapp.isStaffUser() || swh.webapp.isAmbassadorUser()) {

      new ClipboardJS('.btn-citation-copy', {
        text: trigger => {
          const citation = $(trigger).closest('.citation-ui').find('.swh-citation').text();
          return citation;
        }
      }).on('success', function(e) {
        toggleButtonText(e.trigger, 'Copied!');
      });

      const tabSlideOptionsCitations = {
        tabLocation: 'right',
        action: null, // required to implement custom behavior when clicking on tab handle
        clickScreenToCloseFilters: [clickScreenToCloseFilter, '.ui-slideouttab-panel', '.modal'],
        onBeforeOpen: async function() {
          $('#swh-citations').data('opening', true);
          if (!$('#swh-identifiers').data('opening')) {
            // open SWHIDs tab along the citation one
            $('#swh-identifiers').trigger('open');
          }
          const currentObjectType = $('#swh-citations-content .nav-link.active').text().trim();
          const currentObjectCitation = $(`citation-tab-${currentObjectType} pre`).text().trim();
          if (currentObjectCitation === '') {
            generateCitationFromSWHID(currentObjectType);
          }
          toggleTabContentDisplay('#swh-citations', true);
          toggleTabContentDisplay('#swh-identifiers', false);
          return true;
        },
        onOpen: function() {
          $('#swh-citations').data('opening', false);
          $('#citations-handle').attr('aria-expanded', 'true');
          $('#citations-handle').attr('aria-label', 'Collapse citations tab');
        },
        onBeforeClose: function() {
          $('#swh-citations').data('closing', true);
          if (!$('#swh-identifiers').data('closing')) {
            // close SWHIDs tab along the citation one
            $('#swh-identifiers').trigger('close');
          }
          return true;
        },
        onClose: function() {
          $('#swh-citations').data('closing', false);
          $('#citations-handle').attr('aria-expanded', 'false');
          $('#citations-handle').attr('aria-label', 'Expand citations tab');
          $('#citations-handle').css('padding-bottom', '0.1em');
          setTimeout(() => {
            // ensure elements in closed citations tab are not keyboard focusable
            $('#swh-citations-content').css('display', 'none');
          }, 500);
        }
      };

      // initiate the sliding citations tab
      $('#swh-citations').tabSlideOut(tabSlideOptionsCitations);
      // override default behavior when clicking on tab handle
      $('#swh-citations .handle').on('click', event => {
        event.preventDefault();
        if ($('#swh-citations').tabSlideOut('isOpen')) {
          if ($('#swh-citations-content').css('display') === 'none') {
            // display citation tab content if not visible
            toggleTabContentDisplay('#swh-identifiers', false);
            toggleTabContentDisplay('#swh-citations', true);
          } else {
            $('#swh-citations').trigger('close');
          }
        } else {
          $('#swh-citations').trigger('open');
        }
      });

      // check if citation can be generated to activate display of Citations Web UI
      generateCitationFromSWHID(swh.webapp.getBrowsedSwhObjectMetadata().object_type);
    }

    updateTabsSize();

    // highlighted code lines changed
    $(window).on('hashchange', () => {
      addLinesInfo();
    });

    // highlighted code lines removed
    $('body').click(() => {
      addLinesInfo();
    });

    $(window).on('resize', () => {
      updateTabsSize();
    });
  });
}
