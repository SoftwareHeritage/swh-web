/**
 * Copyright (C) 2018  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

// http://dsernst.com/2014/12/14/heaps-permutation-algorithm-in-javascript/

function swap(array, pos1, pos2) {
  let temp = array[pos1];
  array[pos1] = array[pos2];
  array[pos2] = temp;
}

export function heapsPermute(array, output, n) {
  n = n || array.length; // set n default to array.length
  if (n === 1) {
    output(array);
  } else {
    for (let i = 1; i <= n; i += 1) {
      heapsPermute(array, output, n - 1);
      let j;
      if (n % 2) {
        j = 1;
      } else {
        j = i;
      }
      swap(array, j - 1, n - 1); // -1 to account for javascript zero-indexing
    }
  }
}
