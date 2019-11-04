/**
 * Copyright (C) 2018-2019  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import objectFitImages from 'object-fit-images';
import {selectText} from 'utils/functions';
import {BREAKPOINT_MD} from 'utils/constants';

let collapseSidebar = false;
let previousSidebarState = localStorage.getItem('swh-sidebar-collapsed');
if (previousSidebarState !== undefined) {
  collapseSidebar = JSON.parse(previousSidebarState);
}

$(document).on('DOMContentLoaded', () => {
  // set state to collapsed on smaller devices
  if ($(window).width() < BREAKPOINT_MD) {
    collapseSidebar = true;
  }

  // restore previous sidebar state (collapsed/expanded)
  if (collapseSidebar) {
    // hack to avoid animated transition for collapsing sidebar
    // when loading a page
    let sidebarTransition = $('.main-sidebar, .main-sidebar:before').css('transition');
    let sidebarEltsTransition = $('.sidebar .nav-link p, .main-sidebar .brand-text, .sidebar .user-panel .info').css('transition');
    $('.main-sidebar, .main-sidebar:before').css('transition', 'none');
    $('.sidebar .nav-link p, .main-sidebar .brand-text, .sidebar .user-panel .info').css('transition', 'none');
    $('body').addClass('sidebar-collapse');
    $('.swh-words-logo-swh').css('visibility', 'visible');
    // restore transitions for user navigation
    setTimeout(() => {
      $('.main-sidebar, .main-sidebar:before').css('transition', sidebarTransition);
      $('.sidebar .nav-link p, .main-sidebar .brand-text, .sidebar .user-panel .info').css('transition', sidebarEltsTransition);
    });
  }
});

$(document).on('collapsed.lte.pushmenu', event => {
  if ($('body').width() >= BREAKPOINT_MD) {
    $('.swh-words-logo-swh').css('visibility', 'visible');
  }
});

$(document).on('shown.lte.pushmenu', event => {
  $('.swh-words-logo-swh').css('visibility', 'hidden');
});

function ensureNoFooterOverflow() {
  $('body').css('padding-bottom', $('footer').outerHeight() + 'px');
}

$(document).ready(() => {
  // redirect to last browse page if any when clicking on the 'Browse' entry
  // in the sidebar
  $(`.swh-browse-link`).click(event => {
    let lastBrowsePage = sessionStorage.getItem('last-browse-page');
    if (lastBrowsePage) {
      event.preventDefault();
      window.location = lastBrowsePage;
    }
  });

  // ensure footer do not overflow main content for mobile devices
  // or after resizing the browser window
  ensureNoFooterOverflow();
  $(window).resize(function() {
    ensureNoFooterOverflow();
    if ($('body').hasClass('sidebar-collapse') && $('body').width() >= BREAKPOINT_MD) {
      $('.swh-words-logo-swh').css('visibility', 'visible');
    }
  });
  // activate css polyfill 'object-fit: contain' in old browsers
  objectFitImages();

  // reparent the modals to the top navigation div in order to be able
  // to display them
  $('.swh-browse-top-navigation').append($('.modal'));

  let selectedCode = null;

  function getCodeOrPreEltUnderPointer(e) {
    let elts = document.elementsFromPoint(e.clientX, e.clientY);
    for (let elt of elts) {
      if (elt.nodeName === 'CODE' || elt.nodeName === 'PRE') {
        return elt;
      }
    }
    return null;
  }

  // click handler to set focus on code block for copy
  $(document).click(e => {
    selectedCode = getCodeOrPreEltUnderPointer(e);
  });

  function selectCode(event, selectedCode) {
    if (selectedCode) {
      let hljsLnCodeElts = $(selectedCode).find('.hljs-ln-code');
      if (hljsLnCodeElts.length) {
        selectText(hljsLnCodeElts[0], hljsLnCodeElts[hljsLnCodeElts.length - 1]);
      } else {
        selectText(selectedCode.firstChild, selectedCode.lastChild);
      }
      event.preventDefault();
    }
  }

  // select the whole text of focused code block when user
  // double clicks or hits Ctrl+A
  $(document).dblclick(e => {
    if ((e.ctrlKey || e.metaKey)) {
      selectCode(e, getCodeOrPreEltUnderPointer(e));
    }
  });

  $(document).keydown(e => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'a') {
      selectCode(e, selectedCode);
    }
  });

  // show/hide back-to-top button
  let scrollThreshold = 0;
  scrollThreshold += $('.swh-top-bar').height() || 0;
  scrollThreshold += $('.navbar').height() || 0;
  $(window).scroll(() => {
    if ($(window).scrollTop() > scrollThreshold) {
      $('#back-to-top').css('display', 'block');
    } else {
      $('#back-to-top').css('display', 'none');
    }
  });
});

export function initPage(page) {

  $(document).ready(() => {
    // set relevant sidebar link to page active
    $(`.swh-${page}-item`).addClass('active');
    $(`.swh-${page}-link`).addClass('active');

    // triggered when unloading the current page
    $(window).on('unload', () => {
      // backup sidebar state (collapsed/expanded)
      let sidebarCollapsed = $('body').hasClass('sidebar-collapse');
      localStorage.setItem('swh-sidebar-collapsed', JSON.stringify(sidebarCollapsed));
      // backup current browse page
      if (page === 'browse') {
        sessionStorage.setItem('last-browse-page', window.location);
      }
    });

  });
}

export function initHomePage() {
  $(document).ready(() => {
    $('.swh-coverage-list').iFrameResize({heightCalculationMethod: 'taggedElement'});
    fetch(Urls.stat_counters())
      .then(response => response.json())
      .then(data => {
        if (data.stat_counters) {
          $('#swh-contents-count').html(data.stat_counters.content.toLocaleString());
          $('#swh-revisions-count').html(data.stat_counters.revision.toLocaleString());
          $('#swh-origins-count').html(data.stat_counters.origin.toLocaleString());
          $('#swh-directories-count').html(data.stat_counters.directory.toLocaleString());
          $('#swh-persons-count').html(data.stat_counters.person.toLocaleString());
          $('#swh-releases-count').html(data.stat_counters.release.toLocaleString());
        }
        if (data.stat_counters_history) {
          swh.webapp.drawHistoryCounterGraph('#swh-contents-count-history', data.stat_counters_history.content);
          swh.webapp.drawHistoryCounterGraph('#swh-revisions-count-history', data.stat_counters_history.revision);
          swh.webapp.drawHistoryCounterGraph('#swh-origins-count-history', data.stat_counters_history.origin);
        }
      });
  });
  initPage('home');
}

export function showModalMessage(title, message) {
  $('#swh-web-modal-message .modal-title').text(title);
  $('#swh-web-modal-message .modal-content p').text(message);
  $('#swh-web-modal-message').modal('show');
}

export function showModalConfirm(title, message, callback) {
  $('#swh-web-modal-confirm .modal-title').text(title);
  $('#swh-web-modal-confirm .modal-content p').text(message);
  $('#swh-web-modal-confirm #swh-web-modal-confirm-ok-btn').bind('click', () => {
    callback();
    $('#swh-web-modal-confirm').modal('hide');
    $('#swh-web-modal-confirm #swh-web-modal-confirm-ok-btn').unbind('click');
  });
  $('#swh-web-modal-confirm').modal('show');
}

export function addJumpToPagePopoverToDataTable(dataTableElt) {
  dataTableElt.on('draw.dt', function() {
    $('.paginate_button.disabled').css('cursor', 'pointer');
    $('.paginate_button.disabled').on('click', event => {
      const pageInfo = dataTableElt.page.info();
      let content = '<select class="jump-to-page">';
      for (let i = 1; i <= pageInfo.pages; ++i) {
        let selected = '';
        if (i === pageInfo.page + 1) {
          selected = 'selected';
        }
        content += `<option value="${i}" ${selected}>${i}</option>`;
      }
      content += `</select><span> / ${pageInfo.pages}</span>`;
      $(event.target).popover({
        'title': 'Jump to page',
        'content': content,
        'html': true,
        'placement': 'top',
        'sanitizeFn': swh.webapp.filterXSS
      });
      $(event.target).popover('show');
      $('.jump-to-page').on('change', function() {
        $('.paginate_button.disabled').popover('hide');
        const pageNumber = parseInt($(this).val()) - 1;
        dataTableElt.page(pageNumber).draw('page');
      });
    });
  });

  dataTableElt.on('preXhr.dt', () => {
    $('.paginate_button.disabled').popover('hide');
  });
}

let swhObjectIcons;

export function setSwhObjectIcons(icons) {
  swhObjectIcons = icons;
}

export function getSwhObjectIcon(swhObjectType) {
  return swhObjectIcons[swhObjectType];
}

let browsedSwhObjectMetadata = {};

export function setBrowsedSwhObjectMetadata(metadata) {
  browsedSwhObjectMetadata = metadata;
}

export function getBrowsedSwhObjectMetadata() {
  return browsedSwhObjectMetadata;
}
