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
