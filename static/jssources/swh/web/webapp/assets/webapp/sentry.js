/**
 * Copyright (C) 2019  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import * as Sentry from '@sentry/browser';

// Called by a <script> object in the header, after the configuration is
// loaded.
export function sentryInit(sentryDsn) {
  if (sentryDsn !== undefined) {
    Sentry.init({dsn: sentryDsn});
  }
}

// May be used in other scripts to report exceptions.
export function sentryCaptureException(exc) {
  Sentry.captureException(exc);
}
