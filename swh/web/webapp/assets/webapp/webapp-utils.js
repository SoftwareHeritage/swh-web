/**
 * Copyright (C) 2018-2024  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import objectFitImages from 'object-fit-images';
import {selectText} from 'utils/functions';
import Cookies from 'js-cookie';
import iframeResize from '@iframe-resizer/parent';

$(document).ready(() => {
  // redirect to last browse page if any when clicking on the 'Browse' entry
  // in the sidebar
  $(`.swh-browse-link`).click(event => {
    const lastBrowsePage = sessionStorage.getItem('last-browse-page');
    if (lastBrowsePage) {
      event.preventDefault();
      window.location = lastBrowsePage;
    }
  });

  const mainSideBar = $('.app-sidebar');
  const body = $('body');

  function updateSidebarState() {
    if (body.hasClass('sidebar-collapse') &&
        !mainSideBar.hasClass('swh-sidebar-collapsed')) {
      mainSideBar.addClass('swh-sidebar-collapsed');
      Cookies.set('sidebar-state', 'collapsed');
      $('.swh-push-menu').attr('aria-expanded', 'false');
      $('.swh-push-menu').attr('aria-label', 'Expand sidebar');
    } else if (!body.hasClass('sidebar-collapse')) {
      mainSideBar.removeClass('swh-sidebar-collapsed');
      Cookies.set('sidebar-state', 'expanded');
      $('.swh-push-menu').attr('aria-expanded', 'true');
      $('.swh-push-menu').attr('aria-label', 'Collapse sidebar');
    }
  }

  $('.swh-push-menu').on('collapse.lte.push-menu', event => {
    if (body.attr('class').indexOf('sidebar-closed') !== -1) {
      // do not display sidebar when closed but no longer visible,
      // typically when browser zoom level is >= 200%,
      // in order to make it non keyboard focusable
      mainSideBar.css('display', 'none');
    }
  });

  // set sidebar state after collapse / expand animation
  mainSideBar.on('transitionend', evt => {
    updateSidebarState();
  });

  // ensure correct sidebar state when loading a page
  setTimeout(() => {
    updateSidebarState();
  });

  // activate css polyfill 'object-fit: contain' in old browsers
  objectFitImages();

  // reparent the modals to the top navigation div in order to be able
  // to display them
  $('.swh-browse-top-navigation').append($('.modal'));

  let selectedCode = null;

  function getCodeOrPreEltUnderPointer(e) {
    if (e.clientX && e.clientY) {
      const elts = document.elementsFromPoint(e.clientX, e.clientY);
      for (const elt of elts) {
        if (elt.nodeName === 'CODE' || elt.nodeName === 'PRE') {
          return elt;
        }
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
      const hljsLnCodeElts = $(selectedCode).find('.hljs-ln-code');
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
      const searchQueryText = $('#swh-origins-search-top-input').val().trim();
      const queryParameters = new URLSearchParams();
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
  $(document).ready(async() => {
    // mirror version of swh-web does not have coverage widget and counters
    // in the homepage
    if (Object.keys(swh.webapp.mirrorConfig()).length === 0) {
      iframeResize({license: 'GPLv3', heightCalculationMethod: 'taggedElement'}, '.swh-coverage-iframe');
      const response = await fetch(Urls.stat_counters());
      const data = await response.json();

      if (data.stat_counters && !$.isEmptyObject(data.stat_counters)) {
        for (const objectType of ['content', 'revision', 'origin', 'directory', 'person', 'release']) {
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
        for (const objectType of ['content', 'revision', 'origin']) {
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
    }
    swh.webapp.addHeadingAnchors();
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

export function showModalHtml(title, html, width = '500px') {
  $('#swh-web-modal-html .modal-title').text(title);
  $('#swh-web-modal-html .modal-body').html(html);
  $('#swh-web-modal-html .modal-dialog').css('max-width', width);
  $('#swh-web-modal-html .modal-dialog').css('width', width);
  $('#swh-web-modal-html').modal('show');
}

export function addJumpToPagePopoverToDataTable(dataTableElt) {
  const ellipsisButtonSelector = '.dt-paging-button.page-item:contains("…")';
  dataTableElt.on('draw.dt', function() {
    setTimeout(() => {
      $(ellipsisButtonSelector).removeClass('disabled');
      $(ellipsisButtonSelector).css('cursor', 'pointer');
      $(ellipsisButtonSelector).attr('title', 'Jump to page');
      $(ellipsisButtonSelector).on('click', event => {
        $('.popover').remove();
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
          $(ellipsisButtonSelector).popover('hide');
          const pageNumber = parseInt($(this).val()) - 1;
          dataTableElt.page(pageNumber).draw('page');
        });
      });
    }, 10);
  });
  dataTableElt.on('preXhr.dt', () => {
    $('.popover').remove();
  });
  $('body').on('click', e => {
    if ($(e.target).text() !== '…' && $(e.target).parents('.popover').length === 0) {
      $('.popover').remove();
    }
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
  for (const swhidContext of swhidsContext) {
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
  const previousFullWidthState = JSON.parse(localStorage.getItem('swh-web-full-width'));
  if (previousFullWidthState !== null) {
    setFullWidth(previousFullWidthState);
  }
}

function coreSWHIDIsLowerCase(swhid) {
  const qualifiersPos = swhid.indexOf(';');
  let coreSWHID = swhid;
  if (qualifiersPos !== -1) {
    coreSWHID = swhid.slice(0, qualifiersPos);
  }
  return coreSWHID.toLowerCase() === coreSWHID;
}

export async function validateSWHIDInput(swhidInputElt) {
  const swhidInput = swhidInputElt.value.trim();
  let customValidity = '';
  if (swhidInput.toLowerCase().startsWith('swh:')) {
    if (coreSWHIDIsLowerCase(swhidInput)) {
      const resolveSWHIDUrl = Urls.api_1_resolve_swhid(swhidInput);
      const response = await fetch(resolveSWHIDUrl);
      const responseData = await response.json();
      if (responseData.hasOwnProperty('exception')) {
        customValidity = responseData.reason;
      }
    } else {
      const qualifiersPos = swhidInput.indexOf(';');
      if (qualifiersPos === -1) {
        customValidity = 'Invalid SWHID: all characters must be in lowercase. ';
        customValidity += `Valid SWHID is ${swhidInput.toLowerCase()}`;
      } else {
        customValidity = 'Invalid SWHID: the core part must be in lowercase. ';
        const coreSWHID = swhidInput.slice(0, qualifiersPos);
        customValidity += `Valid SWHID is ${swhidInput.replace(coreSWHID, coreSWHID.toLowerCase())}`;
      }
    }
  }
  swhidInputElt.setCustomValidity(customValidity);
  $(swhidInputElt).siblings('.invalid-feedback').text(customValidity);
}

export function isUserLoggedIn() {
  return JSON.parse($('#swh_user_logged_in').text());
}

export function isStaffUser() {
  return JSON.parse($('#swh_user_is_staff').text());
}

export function isAmbassadorUser() {
  return JSON.parse($('#swh_user_is_ambassador').text());
}

export function mirrorConfig() {
  return JSON.parse($('#swh_mirror_config').text());
}
