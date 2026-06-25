/**
 * Copyright (C) 2022-2026  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import '@iframe-resizer/child';
import 'webapp/assets/webapp/webapp.css';
import './coverage.css';

// FIXME: remove this when merged into bootstrap:
// https://github.com/twbs/bootstrap/issues/41479
// https://codepen.io/wdzajicek/pen/VYZawjX

const enableCollapseFind = () => {
  if (!('onbeforematch' in document.body)) {
    return;
  }
  Array.from(document.querySelectorAll('.collapse')).forEach((item) => {
    const showHideCollapses = (ev) => {
      const focus = Boolean(document.querySelector('.swh-coverage-focus'));
      Array.from(document.querySelectorAll('.collapse')).forEach((item) => {
        if (item === ev.target) {
          $(item).collapse('show');
        } else if (!focus) {
          $(item).collapse('hide');
        }
      });
    };
    const onhide = () => {
      item.hidden = 'until-found';
      item.role = 'region';
    };
    const onshow = () => {
      item.removeAttribute('hidden');
      item.removeAttribute('role');
    };
    if (item.classList.contains('show')) {
      onshow();
    } else {
      onhide();
    }
    item.onbeforematch = showHideCollapses;
    item.addEventListener('show.bs.collapse', onshow);
    item.addEventListener('hidden.bs.collapse', onhide);
  });
};

document.addEventListener('DOMContentLoaded', enableCollapseFind);
