/**
 * Copyright (C) 2018  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

export function initSnapshotNavigation(snapshotContext, branch) {

  function setBranchesTabActive() {
    $('.swh-releases-switch').removeClass('active');
    $('.swh-branches-switch').addClass('active');
    $('#swh-tab-releases').removeClass('active');
    $('#swh-tab-branches').addClass('active');
  }

  function setReleasesTabActive() {
    $('.swh-branches-switch').removeClass('active');
    $('.swh-releases-switch').addClass('active');
    $('#swh-tab-branches').removeClass('active');
    $('#swh-tab-releases').addClass('active');
  }

  $(document).ready(() => {
    $('.dropdown-menu a.swh-branches-switch').click(e => {
      setBranchesTabActive();
      e.stopPropagation();
    });

    $('.dropdown-menu a.swh-releases-switch').click(e => {
      setReleasesTabActive();
      e.stopPropagation();
    });

    let dropdownResized = false;

    // hack to resize the branches/releases dropdown content,
    // taking icons into account, in order to make the whole names readable
    $('#swh-branches-releases-dd').on('show.bs.dropdown', () => {
      if (dropdownResized) return;
      let dropdownWidth = $('.swh-branches-releases').width();
      $('.swh-branches-releases').width(dropdownWidth + 25);
      dropdownResized = true;
    });

    if (snapshotContext) {
      if (branch) {
        setBranchesTabActive();
      } else {
        setReleasesTabActive();
      }
    }

  });

}
