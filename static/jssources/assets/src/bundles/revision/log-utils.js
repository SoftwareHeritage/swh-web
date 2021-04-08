/**
 * Copyright (C) 2019  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

export function revsOrderingTypeClicked(event) {
  let urlParams = new URLSearchParams(window.location.search);
  let orderingType = $(event.target).val();
  if (orderingType) {
    urlParams.set('revs_ordering', $(event.target).val());
  } else if (urlParams.has('revs_ordering')) {
    urlParams.delete('revs_ordering');
  }
  window.location.search = urlParams.toString();
}

export function initRevisionsLog() {
  $(document).ready(() => {
    let urlParams = new URLSearchParams(window.location.search);
    let revsOrderingType = urlParams.get('revs_ordering');
    if (revsOrderingType) {
      $(`:input[value="${revsOrderingType}"]`).prop('checked', true);
    }
  });
}
