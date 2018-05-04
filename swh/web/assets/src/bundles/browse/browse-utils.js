/**
 * Copyright (C) 2018  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

export function initBrowse(page) {

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

    $(`.browse-${page}-item`).addClass('active');
    $(`.browse-${page}-link`).addClass('active');

    $(`.browse-main-link`).click(event => {
      let lastBrowsePage = sessionStorage.getItem('last-browse-page');
      if (lastBrowsePage) {
        event.preventDefault();
        window.location = lastBrowsePage;
      }
    });

    window.onunload = () => {
      if (page === 'main') {
        sessionStorage.setItem('last-browse-page', window.location);
      }
    };

  });

}
