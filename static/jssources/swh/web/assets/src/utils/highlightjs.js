/**
 * Copyright (C) 2018-2020  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

// highlightjs chunk that will be lazily loaded

import 'highlight.js';
import 'highlightjs-line-numbers.js';
import 'highlight.js/styles/github.css';
import './highlightjs.css';

// define a synchronous version of hljs.lineNumbersBlock
hljs.lineNumbersBlockSync = function(block) {
  block.innerHTML = hljs.lineNumbersValue(block.innerHTML);
};
