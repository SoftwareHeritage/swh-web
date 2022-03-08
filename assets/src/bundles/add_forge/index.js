/**
 * Copyright (C) 2022  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

export function initAddForge() {
  $(document).ready(() => {
    // populateRequests
    $('#requestForm').submit(function(event) {
      event.preventDefault();

      $.ajax({
        data: $(this).serialize(),
        type: $(this).attr('method'),
        url: $(this).attr('action'),
        success: function(response) {
          $('#userMessage').text('Your request has been submitted');
          $('#userMessage').addClass('badge-success');
        },
        error: function(request, status, error) {
          $('#userMessage').text('Sorry following error happened, ' + error);
          $('#userMessage').addClass('badge-danger');
        }
      });
    });
  });
}
