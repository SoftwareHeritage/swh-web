/**
 * Copyright (C) 2018-2021  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import objectFitImages from 'object-fit-images';
import {selectText} from 'utils/functions';
import {BREAKPOINT_MD} from 'utils/constants';

let collapseSidebar = false;
let previousSidebarState = localStorage.getItem('remember.lte.pushmenu');
if (previousSidebarState !== undefined) {
  collapseSidebar = previousSidebarState === 'sidebar-collapse';
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

  const mainSideBar = $('.main-sidebar');

  function updateSidebarState() {
    const body = $('body');
    if (body.hasClass('sidebar-collapse') &&
        !mainSideBar.hasClass('swh-sidebar-collapsed')) {
      mainSideBar.removeClass('swh-sidebar-expanded');
      mainSideBar.addClass('swh-sidebar-collapsed');
      $('.swh-words-logo-swh').css('visibility', 'visible');
    } else if (!body.hasClass('sidebar-collapse') &&
               !mainSideBar.hasClass('swh-sidebar-expanded')) {
      mainSideBar.removeClass('swh-sidebar-collapsed');
      mainSideBar.addClass('swh-sidebar-expanded');
      $('.swh-words-logo-swh').css('visibility', 'hidden');
    }
    // ensure correct sidebar state when loading a page
    if (body.hasClass('hold-transition')) {
      setTimeout(() => {
        updateSidebarState();
      });
    }
  }

  // set sidebar state after collapse / expand animation
  mainSideBar.on('transitionend', evt => {
    updateSidebarState();
  });

  updateSidebarState();

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

  // navbar search form submission callback
  $('#swh-origins-search-top').submit(event => {
    event.preventDefault();
    if (event.target.checkValidity()) {
      $(event.target).removeClass('was-validated');
      let searchQueryText = $('#swh-origins-search-top-input').val().trim();
      let queryParameters = new URLSearchParams();
      queryParameters.append('q', searchQueryText);
      queryParameters.append('with_visit', true);
      queryParameters.append('with_content', true);
      window.location = `${Urls.browse_search()}?${queryParameters.toString()}`;
    } else {
      $(event.target).addClass('was-validated');
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
        if (data.stat_counters && !$.isEmptyObject(data.stat_counters)) {
          for (let objectType of ['content', 'revision', 'origin', 'directory', 'person', 'release']) {
            const count = data.stat_counters[objectType];
            if (count !== undefined) {
              $(`#swh-${objectType}-count`).html(count.toLocaleString());
            } else {
              $(`#swh-${objectType}-count`).closest('.swh-counter-container').hide();
            }
          }
        } else {
          $('.swh-counter').html('0');
        }
        if (data.stat_counters_history && !$.isEmptyObject(data.stat_counters_history)) {
          for (let objectType of ['content', 'revision', 'origin']) {
            const history = data.stat_counters_history[objectType];
            if (history) {
              swh.webapp.drawHistoryCounterGraph(`#swh-${objectType}-count-history`, history);
            } else {
              $(`#swh-${objectType}-count-history`).hide();
            }

          }
        } else {
          $('.swh-counter-history').hide();
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

export function showModalHtml(title, html) {
  $('#swh-web-modal-html .modal-title').text(title);
  $('#swh-web-modal-html .modal-body').html(html);
  $('#swh-web-modal-html').modal('show');
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

// This will contain a mapping between an archived object type
// and its related SWHID metadata for each object reachable from
// the current browse view.
// SWHID metadata contain the following keys:
//   * object_type: type of archived object
//   * object_id: sha1 object identifier
//   * swhid: SWHID without contextual info
//   * swhid_url: URL to resolve SWHID without contextual info
//   * context: object describing SWHID context
//   * swhid_with_context: SWHID with contextual info
//   * swhid_with_context_url: URL to resolve SWHID with contextual info
let swhidsContext_ = {};

export function setSwhIdsContext(swhidsContext) {
  swhidsContext_ = {};
  for (let swhidContext of swhidsContext) {
    swhidsContext_[swhidContext.object_type] = swhidContext;
  }
}

export function getSwhIdsContext() {
  return swhidsContext_;
}

function setFullWidth(fullWidth) {
  if (fullWidth) {
    $('#swh-web-content').removeClass('container');
    $('#swh-web-content').addClass('container-fluid');
  } else {
    $('#swh-web-content').removeClass('container-fluid');
    $('#swh-web-content').addClass('container');
  }
  localStorage.setItem('swh-web-full-width', JSON.stringify(fullWidth));
  $('#swh-full-width-switch').prop('checked', fullWidth);
}

export function fullWidthToggled(event) {
  setFullWidth($(event.target).prop('checked'));
}

export function setContainerFullWidth() {
  let previousFullWidthState = JSON.parse(localStorage.getItem('swh-web-full-width'));
  if (previousFullWidthState !== null) {
    setFullWidth(previousFullWidthState);
  }
}

export async function validateSWHIDInput(swhidInputElt) {
  const swhidInput = swhidInputElt.value.trim();
  let customValidity = '';
  if (swhidInput.startsWith('swh:')) {
    const resolveSWHIDUrl = Urls.api_1_resolve_swhid(swhidInput);
    const response = await fetch(resolveSWHIDUrl);
    const responseData = await response.json();
    if (responseData.hasOwnProperty('exception')) {
      customValidity = responseData.reason;
    }
  }
  swhidInputElt.setCustomValidity(customValidity);
  $(swhidInputElt).siblings('.invalid-feedback').text(customValidity);
}
