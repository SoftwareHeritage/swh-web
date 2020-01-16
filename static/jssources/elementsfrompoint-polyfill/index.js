/**
 * Safari 11.0 doesn't support document.elementsFromPoint, only document.elementFromPoint
 * https://developer.mozilla.org/en-US/docs/Web/API/DocumentOrShadowRoot/elementsFromPoint
 * Polyfill is based on https://gist.github.com/iddan/54d5d9e58311b0495a91bf06de661380
 */

if (typeof document !== 'undefined' && typeof document.elementsFromPoint === 'undefined') {
    document.elementsFromPoint = elementsFromPointPolyfill;
}

function elementsFromPointPolyfill(x, y) {
    var elements = [];
    var pointerEvents =[];
    var el;

    do {
        if (el !== document.elementFromPoint(x, y)) {
            el = document.elementFromPoint(x, y);
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
