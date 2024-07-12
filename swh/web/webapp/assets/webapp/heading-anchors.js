/**
 * Copyright (C) 2024  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import AnchorJS from 'anchor-js';
import './heading-anchors.css';

export function addHeadingAnchors(
  cssSelector = '.content h2, .content h3, .content h4, .content h5, .content h6') {
  $(function() {
    const anchors = new AnchorJS({
      class: 'swh-heading-anchor',
      ariaLabel: 'anchor to heading'
    });
    anchors.add(cssSelector);
  });
}
