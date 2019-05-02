/**
 * Copyright (C) 2019  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

function getLoadedMathJaxJsFilesInfo(mathJaxJsFiles, cdnPrefix, unpackedLocationPrefix) {
  let ret = {};
  for (let mathJaxJsFile of mathJaxJsFiles) {
    ret[cdnPrefix + mathJaxJsFile] = [{
      'id': mathJaxJsFile,
      'path': unpackedLocationPrefix + mathJaxJsFile,
      'spdxLicenseExpression': 'Apache-2.0',
      'licenseFilePath': ''
    }];
  }
  return ret;
}

let cdnPrefix = 'https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.5/';

let unpackedLocationPrefix = 'https://raw.githubusercontent.com/mathjax/MathJax/2.7.5/unpacked/';

let mathJaxJsFiles = [
  'MathJax.js',
  'config/TeX-AMS_HTML.js',
  'extensions/MathMenu.js',
  'jax/element/mml/optable/BasicLatin.js',
  'jax/output/HTML-CSS/jax.js',
  'jax/output/HTML-CSS/fonts/TeX/fontdata.js',
  'jax/output/HTML-CSS/fonts/TeX/AMS/Regular/Main.js',
  'jax/output/HTML-CSS/fonts/TeX/AMS/Regular/BBBold.js',
  'jax/output/HTML-CSS/fonts/TeX/AMS/Regular/GeneralPunctuation.js',
  'jax/output/HTML-CSS/autoload/mtable.js',
  'jax/output/HTML-CSS/fonts/TeX/AMS/Regular/MiscTechnical.js',
  'jax/output/HTML-CSS/fonts/TeX/Typewriter/Regular/Main.js',
  'jax/element/mml/optable/MathOperators.js',
  'jax/output/HTML-CSS/autoload/multiline.js',
  'jax/output/HTML-CSS/fonts/TeX/AMS/Regular/MathOperators.js',
  'jax/element/mml/optable/GeneralPunctuation.js'
];

module.exports = getLoadedMathJaxJsFilesInfo(mathJaxJsFiles, cdnPrefix, unpackedLocationPrefix);
