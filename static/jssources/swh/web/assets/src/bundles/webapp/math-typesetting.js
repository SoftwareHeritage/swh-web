/**
 * Copyright (C) 2020  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import {staticAsset} from 'utils/functions';

export async function typesetMath() {

  window.MathJax = {
    chtml: {
      fontURL: staticAsset('fonts/')
    },
    tex: {
      tags: 'ams',
      useLabelIds: true,
      inlineMath: [ ['$', '$'], ['\\(', '\\)'] ],
      displayMath: [ ['$$', '$$'], ['\\[', '\\]'] ],
      processEscapes: true,
      processEnvironments: true
    }
  };

  await import(/* webpackChunkName: "mathjax" */ 'utils/mathjax');
}
