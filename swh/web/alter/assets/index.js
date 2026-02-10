/**
 * Copyright (C) 2025-2026  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

// bundle for alter views

export * from './alter.css';

export function initDashboardFilters() {
  const status = document.getElementById('id_status');
  status.addEventListener('change', (event) => {
    event.target.closest('form').submit();
  });
};
