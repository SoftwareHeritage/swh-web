/**
 * Copyright (C) 2019  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import axios from 'axios';

export async function httpGetJson(url) {
  const response = await axios.get(url);
  return response.data;
}
