/**
 * Copyright (C) 2019  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import * as d3 from 'd3-format';

const d3Format = d3.format;

// Override d3.format in order to use B for denoting billions instead of G
function customD3Format() {
  const ret = d3Format.apply(d3, arguments);
  return (function(args) {
    return function() {
      return args.apply(d3, arguments).replace(/G/, 'B');
    };
  })(ret);
}

export {customD3Format as format};
