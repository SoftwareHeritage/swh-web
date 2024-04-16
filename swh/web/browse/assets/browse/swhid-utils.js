/**
 * Copyright (C) 2018-2024  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import ClipboardJS from 'clipboard';
import 'thirdparty/jquery.tabSlideOut/jquery.tabSlideOut';
import 'thirdparty/jquery.tabSlideOut/jquery.tabSlideOut.css';

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

function addLinesInfo() {
  const swhIdElt = $('#swhid-tab-content').find('.swhid');
  let currentSwhId = swhIdElt.text().replace(/;\n/g, ';');
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

  const contextOptionCheckBox = $('#swhid-context-option-content');
  if (contextOptionCheckBox.prop('checked')) {
    let swhIdWithContextUrl = contextOptionCheckBox.data('swhid-with-context-url');
    currentSwhId = currentSwhId.replace(/;lines=\d+-*\d*/g, '');
    if (lines.length > 0) {
      currentSwhId += linesPart;
      swhIdWithContextUrl += linesPart;
    }

    swhIdElt.text(currentSwhId.replace(/;/g, ';\n'));
    swhIdElt.attr('href', swhIdWithContextUrl);
  }
}

function updateSWHIDsTabSize() {
  // update tab width based on browser windows width
  $('#swh-identifiers').css('width', Math.min(window.innerWidth - 45, 1000) + 'px');
  // update tab anchor top position based on browser windows height
  const top = window.innerHeight >= 700 ? 250 : 35;
  $('#swh-identifiers').css('top', top + 'px');
  // backup current display state for tab content
  const currentDisplay = $('#swh-identifiers-content').css('display');
  // reset tab height to be automatically computed
  $('#swh-identifiers').css('height', 'auto');
  // ensure tab content is displayed for current height computation
  $('#swh-identifiers-content').css('display', 'block');
  // update tab height to fit in the screen (its content is scrollable in case of overflow)
  if (top + $('#swh-identifiers').height() > window.innerHeight) {
    $('#swh-identifiers').css('height', (window.innerHeight - top - 5) + 'px');
  }
  // hide badges and iframes links on display with small height
  $('#swh-identifiers .swh-badges-iframe').css('display', window.innerHeight >= 700 ? 'flex' : 'none');
  // hide badges and iframes links on display with small width
  $('#swh-identifiers .swh-badges-iframe').css('display', window.innerWidth >= 700 ? 'flex' : 'none');
  // restore current display state for tab content
  $('#swh-identifiers-content').css('display', currentDisplay);
}

$(document).ready(() => {
  new ClipboardJS('.btn-swhid-copy', {
    text: trigger => {
      const swhId = $(trigger).closest('.swhid-ui').find('.swhid').text();
      return swhId.replace(/;\n/g, ';');
    }
  });

  new ClipboardJS('.btn-swhid-url-copy', {
    text: trigger => {
      const swhIdUrl = $(trigger).closest('.swhid-ui').find('.swhid').attr('href');
      return window.location.origin + swhIdUrl;
    }
  });

  // prevent automatic closing of SWHIDs tab during guided tour
  // as it is displayed programmatically
  function clickScreenToCloseFilter() {
    return $('.introjs-overlay').length > 0;
  }

  const tabSlideOptions = {
    tabLocation: 'right',
    clickScreenToCloseFilters: [clickScreenToCloseFilter, '.ui-slideouttab-panel', '.modal'],
    onBeforeOpen: function() {
      $('#swh-identifiers-content').css('display', 'block');
      return true;
    },
    onOpen: function() {
      $('#swhids-handle').attr('aria-expanded', 'true');
      $('#swhids-handle').attr('aria-label', 'Collapse permalinks tab');
    },
    onClose: function() {
      $('#swhids-handle').attr('aria-expanded', 'false');
      $('#swhids-handle').attr('aria-label', 'Expand permalinks tab');
      setTimeout(() => {
        // ensure elements in closed SWHIDs tab are not keyboard focusable
        $('#swh-identifiers-content').css('display', 'none');
      }, 500);
    }
  };

  // initiate the sliding identifiers tab
  $('#swh-identifiers').tabSlideOut(tabSlideOptions);

  // ensure qualified SWHIDs are displayed by default
  $('.swhid-context-option').each(function(i, elt) {
    updateDisplayedSWHID(elt);
  });

  updateSWHIDsTabSize();

  // highlighted code lines changed
  $(window).on('hashchange', () => {
    addLinesInfo();
  });

  // highlighted code lines removed
  $('body').click(() => {
    addLinesInfo();
  });

  $(window).on('resize', () => {
    updateSWHIDsTabSize();
  });

});
