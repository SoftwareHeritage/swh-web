/**
 * Copyright (C) 2018-2019  The Software Heritage developers
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

export function swhIdContextOptionToggled(event) {
  event.stopPropagation();
  let swhIdElt = $(event.target).closest('.swhid-ui').find('.swhid');
  let swhIdWithContext = $(event.target).data('swhid-with-context');
  let swhIdWithContextUrl = $(event.target).data('swhid-with-context-url');
  let currentSwhId = swhIdElt.text();
  if ($(event.target).prop('checked')) {
    swhIdElt.attr('href', swhIdWithContextUrl);
    currentSwhId = swhIdWithContext.replace(/;/g, ';\n');
  } else {
    const pos = currentSwhId.indexOf(';');
    if (pos !== -1) {
      currentSwhId = currentSwhId.slice(0, pos);
    }
    swhIdElt.attr('href', '/' + currentSwhId + '/');
  }
  swhIdElt.text(currentSwhId);

  addLinesInfo();
}

function addLinesInfo() {
  let swhIdElt = $('#swhid-tab-content').find('.swhid');
  let currentSwhId = swhIdElt.text().replace(/;\n/g, ';');
  let lines = [];
  let linesPart = ';lines=';
  let linesRegexp = new RegExp(/L(\d+)/g);
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

  if ($('#swhid-context-option-content').prop('checked')) {
    currentSwhId = currentSwhId.replace(/;lines=\d+-*\d*/g, '');
    if (lines.length > 0) {
      currentSwhId += linesPart;
    }

    swhIdElt.text(currentSwhId.replace(/;/g, ';\n'));
    swhIdElt.attr('href', '/' + currentSwhId + '/');
  }
}

$(document).ready(() => {
  new ClipboardJS('.btn-swhid-copy', {
    text: trigger => {
      let swhId = $(trigger).closest('.swhid-ui').find('.swhid').text();
      return swhId.replace(/;\n/g, ';');
    }
  });

  new ClipboardJS('.btn-swhid-url-copy', {
    text: trigger => {
      let swhIdUrl = $(trigger).closest('.swhid-ui').find('.swhid').attr('href');
      return window.location.origin + swhIdUrl;
    }
  });

  if (window.innerWidth * 0.7 > 1000) {
    $('#swh-identifiers').css('width', '1000px');
  }

  let tabSlideOptions = {
    tabLocation: 'right',
    clickScreenToCloseFilters: ['.ui-slideouttab-panel', '.modal'],
    offset: function() {
      const width = $(window).width();
      if (width < BREAKPOINT_SM) {
        return '250px';
      } else {
        return '200px';
      }
    }
  };
  // ensure tab scrolling on small screens
  if (window.innerHeight < 600 || window.innerWidth < 500) {
    tabSlideOptions['otherOffset'] = '20px';
  }

  // initiate the sliding identifiers tab
  $('#swh-identifiers').tabSlideOut(tabSlideOptions);

  // set the tab visible once the close animation is terminated
  $('#swh-identifiers').css('display', 'block');
  $('.swhid-context-option').trigger('click');

  // highlighted code lines changed
  $(window).on('hashchange', () => {
    addLinesInfo();
  });

  // highlighted code lines removed
  $('body').click(() => {
    addLinesInfo();
  });

});
