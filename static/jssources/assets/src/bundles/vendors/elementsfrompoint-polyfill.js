/**
 * Copyright (C) 2020  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

/**
 * Some old browsers (Safari 11.0, Firefox 36.0) do not support
 * document.elementsFromPoint, only document.elementFromPoint.
 * https://developer.mozilla.org/en-US/docs/Web/API/DocumentOrShadowRoot/elementsFromPoint
 * Polyfill is based on https://github.com/JSmith01/elementsfrompoint-polyfill (public domain)
 * and fix a bug in that implementation
 */

if (typeof document !== 'undefined' && typeof document.elementsFromPoint === 'undefined') {
  document.elementsFromPoint = elementsFromPointPolyfill;
}

function elementsFromPointPolyfill(x, y) {
  var elements = [];
  var pointerEvents = [];
  var el;

  do {
    var parent = document.elementFromPoint(x, y);
    if (parent) {
      el = parent;
      elements.push(el);
      pointerEvents.push(el.style.pointerEvents);
      el.style.pointerEvents = 'none';
    } else {
      el = null;
    }
  } while (el);

  for (var i = 0; i < elements.length; i++) {
    elements[i].style.pointerEvents = pointerEvents[i];
  }

  return elements;
}
