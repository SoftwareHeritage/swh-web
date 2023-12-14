/**
 * Copyright (C) 2018-2021  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import ClipboardJS from 'clipboard';
import 'thirdparty/jquery.tabSlideOut/jquery.tabSlideOut';
import 'thirdparty/jquery.tabSlideOut/jquery.tabSlideOut.css';

import {BREAKPOINT_SM} from 'utils/constants';

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

  if (window.innerWidth * 0.7 > 1000) {
    $('#swh-identifiers').css('width', '1000px');
  }

  // prevent automatic closing of SWHIDs tab during guided tour
  // as it is displayed programmatically
  function clickScreenToCloseFilter() {
    return $('.introjs-overlay').length > 0;
  }

  const tabSlideOptions = {
    tabLocation: 'right',
    clickScreenToCloseFilters: [clickScreenToCloseFilter, '.ui-slideouttab-panel', '.modal'],
    offset: function() {
      const width = $(window).width();
      if (width < BREAKPOINT_SM) {
        return '250px';
      } else {
        return '200px';
      }
    },
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
  // ensure tab scrolling on small screens
  if (window.innerHeight < 600 || window.innerWidth < 500) {
    tabSlideOptions['otherOffset'] = '20px';
  }

  // initiate the sliding identifiers tab
  $('#swh-identifiers').tabSlideOut(tabSlideOptions);

  // set the tab visible once the close animation is terminated
  $('#swh-identifiers').addClass('d-none d-sm-block');

  // ensure qualified SWHIDs are displayed by default
  $('.swhid-context-option').each(function(i, elt) {
    updateDisplayedSWHID(elt);
  });

  // highlighted code lines changed
  $(window).on('hashchange', () => {
    addLinesInfo();
  });

  // highlighted code lines removed
  $('body').click(() => {
    addLinesInfo();
  });

});
