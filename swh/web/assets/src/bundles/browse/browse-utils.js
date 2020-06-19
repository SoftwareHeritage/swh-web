/**
 * Copyright (C) 2018-2020  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import {BREAKPOINT_SM} from 'utils/constants';

$(document).ready(() => {

  $('.dropdown-submenu a.dropdown-item').on('click', e => {
    $(e.target).next('div').toggle();
    if ($(e.target).next('div').css('display') !== 'none') {
      $(e.target).focus();
    } else {
      $(e.target).blur();
    }
    e.stopPropagation();
    e.preventDefault();
  });

  $('.swh-popover-toggler').popover({
    boundary: 'viewport',
    container: 'body',
    html: true,
    placement: function() {
      const width = $(window).width();
      if (width < BREAKPOINT_SM) {
        return 'top';
      } else {
        return 'right';
      }
    },
    template: `<div class="popover" role="tooltip">
                 <div class="arrow"></div>
                 <h3 class="popover-header"></h3>
                 <div class="popover-body swh-popover"></div>
               </div>`,
    content: function() {
      var content = $(this).attr('data-popover-content');
      return $(content).children('.popover-body').remove().html();
    },
    title: function() {
      var title = $(this).attr('data-popover-content');
      return $(title).children('.popover-heading').html();
    },
    offset: '50vh',
    sanitize: false
  });

  $('.swh-vault-menu a.dropdown-item').on('click', e => {
    $('.swh-popover-toggler').popover('hide');
  });

  $('.swh-popover-toggler').on('show.bs.popover', (e) => {
    $(`.swh-popover-toggler:not(#${e.currentTarget.id})`).popover('hide');
    $('.swh-vault-menu .dropdown-menu').hide();
  });

  $('.swh-actions-dropdown').on('hide.bs.dropdown', () => {
    $('.swh-vault-menu .dropdown-menu').hide();
    $('.swh-popover-toggler').popover('hide');
  });

  $('body').on('click', e => {
    if ($(e.target).parents('.swh-popover').length) {
      e.stopPropagation();
    }
  });

});

export function initBrowseNavbar() {
  if (window.location.pathname === Urls.browse_origin_visits()) {
    $('#swh-browse-origin-visits-nav-link').addClass('active');
  } else if (window.location.pathname === Urls.browse_origin_branches() ||
    window.location.pathname === Urls.browse_snapshot_branches()) {
    $('#swh-browse-snapshot-branches-nav-link').addClass('active');
  } else if (window.location.pathname === Urls.browse_origin_releases() ||
             window.location.pathname === Urls.browse_snapshot_releases()) {
    $('#swh-browse-snapshot-releases-nav-link').addClass('active');
  } else {
    $('#swh-browse-code-nav-link').addClass('active');
  }
}
