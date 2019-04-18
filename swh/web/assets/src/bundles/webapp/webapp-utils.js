import objectFitImages from 'object-fit-images';
import {Layout} from 'admin-lte';
import {selectText} from 'utils/functions';

let collapseSidebar = false;
let previousSidebarState = localStorage.getItem('swh-sidebar-collapsed');
if (previousSidebarState !== undefined) {
  collapseSidebar = JSON.parse(previousSidebarState);
}

// adapt implementation of fixLayoutHeight from admin-lte
Layout.prototype.fixLayoutHeight = () => {
  let heights = {
    window: $(window).height(),
    header: $('.main-header').outerHeight(),
    footer: $('.footer').outerHeight(),
    sidebar: $('.main-sidebar').height(),
    topbar: $('.swh-top-bar').height()
  };
  let offset = 10;
  $('.content-wrapper').css('min-height', heights.window - heights.topbar - heights.header - heights.footer - offset);
  $('.main-sidebar').css('min-height', heights.window - heights.topbar - heights.header - heights.footer - offset);
};

$(document).on('DOMContentLoaded', () => {
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
  if ($('body').width() > 980) {
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
    if ($('body').hasClass('sidebar-collapse') && $('body').width() > 980) {
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

let swhObjectIcons;

export function setSwhObjectIcons(icons) {
  swhObjectIcons = icons;
}

export function getSwhObjectIcon(swhObjectType) {
  return swhObjectIcons[swhObjectType];
}

let reCaptchaActivated;

export function setReCaptchaActivated(activated) {
  reCaptchaActivated = activated;
}

export function isReCaptchaActivated() {
  return reCaptchaActivated;
}

let browsedSwhObjectMetadata = {};

export function setBrowsedSwhObjectMetadata(metadata) {
  browsedSwhObjectMetadata = metadata;
}

export function getBrowsedSwhObjectMetadata() {
  return browsedSwhObjectMetadata;
}
