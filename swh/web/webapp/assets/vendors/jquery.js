/**
 * Copyright (C) 2026  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import {jQuery} from 'jquery';

globalThis.$ = jQuery;
globalThis.jQuery = jQuery;

// add some polyfills to functions removed in jQuery 4.0 but
// still used by some dependencies like chosen-js or waypoints
$.trim = function(string) {
  return string.trim();
};

$.isFunction = function(x) {
  return typeof x === 'function';
};
