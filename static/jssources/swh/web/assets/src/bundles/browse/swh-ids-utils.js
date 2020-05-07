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
  let swhIdElt = $(event.target).closest('.swh-id-ui').find('.swh-id');
  let swhIdWithContext = $(event.target).data('swhid-with-context');
  let currentSwhId = swhIdElt.text();
  if ($(event.target).prop('checked')) {
    currentSwhId = swhIdWithContext;
  } else {
    const pos = currentSwhId.indexOf(';');
    if (pos !== -1) {
      currentSwhId = currentSwhId.slice(0, pos);
    }
  }
  swhIdElt.text(currentSwhId);
  swhIdElt.attr('href', '/' + currentSwhId + '/');

  addLinesInfo();
}

function addLinesInfo() {
  let swhIdElt = $('#swh-id-tab-content').find('.swh-id');
  let currentSwhId = swhIdElt.text();
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

  if ($('#swh-id-context-option-content').prop('checked')) {
    currentSwhId = currentSwhId.replace(/;lines=\d+-*\d*/g, '');
    if (lines.length > 0) {
      currentSwhId += linesPart;
    }

    swhIdElt.text(currentSwhId);
    swhIdElt.attr('href', '/' + currentSwhId + '/');
  }
}

$(document).ready(() => {
  new ClipboardJS('.btn-swh-id-copy', {
    text: trigger => {
      let swhId = $(trigger).closest('.swh-id-ui').find('.swh-id').text();
      return swhId;
    }
  });

  new ClipboardJS('.btn-swh-id-url-copy', {
    text: trigger => {
      let swhId = $(trigger).closest('.swh-id-ui').find('.swh-id').text();
      return window.location.origin + '/' + swhId + '/';
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
  $('.swh-id-context-option').trigger('click');

  // highlighted code lines changed
  $(window).on('hashchange', () => {
    addLinesInfo();
  });

  // highlighted code lines removed
  $('body').click(() => {
    addLinesInfo();
  });

});
