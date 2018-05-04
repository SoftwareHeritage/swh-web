/**
 * Copyright (C) 2018  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

// utility functions

export function handleFetchError(response) {
  if (!response.ok) {
    throw Error(response.statusText);
  }
  return response;
}

export function handleFetchErrors(responses) {
  for (let i = 0; i < responses.length; ++i) {
    if (!responses[i].ok) {
      throw Error(responses[i].statusText);
    }
  }
  return responses;
}

export function staticAsset(asset) {
  return `${__STATIC__}${asset}`;
}
