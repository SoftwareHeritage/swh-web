/**
 * Copyright (C) 2022  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

// bundle for add forge views

export * from './add-forge.css';
export * from './create-request';
export * from './moderation-dashboard';
export * from './request-dashboard';

export function formatRequestStatusName(status) {
  // Mapping to format the request status to a human readable text
  const statusLabel = {
    'PENDING': 'Pending',
    'WAITING_FOR_FEEDBACK': 'Waiting for feedback',
    'FEEDBACK_TO_HANDLE': 'Feedback to handle',
    'ACCEPTED': 'Accepted',
    'SCHEDULED': 'Scheduled',
    'FIRST_LISTING_DONE': 'First listing done',
    'FIRST_ORIGIN_LOADED': 'First origin loaded',
    'REJECTED': 'Rejected',
    'SUSPENDED': 'Suspended',
    'UNSUCCESSFUL': 'Unsuccessful'
  };
  return status in statusLabel ? statusLabel[status] : status;
}
