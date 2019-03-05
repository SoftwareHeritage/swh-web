/**
 * Copyright (C) 2019  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

'use strict';

// This plugin modifies the generated asset sourcemaps on the fly
// in order to be successfully loaded by Firefox.
// The following error is reported without that:
// Source map error: TypeError: Invalid URL: webpack://swh.[name]/...

class FixSwhSourceMapsPlugin {

  constructor() {
    this.sourceMapRegexp = /\.map($|\?)/i;
  }

  apply(compiler) {
    compiler.hooks.afterCompile.tap('FixSwhSourceMapsPlugin', compilation => {
      Object.keys(compilation.assets).filter(key => {
        return this.sourceMapRegexp.test(key);
      }).forEach(key => {
        let bundleName = key.replace(/^js\//, '');
        bundleName = bundleName.replace(/^css\//, '');
        let pos = bundleName.indexOf('.');
        bundleName = bundleName.slice(0, pos);
        let asset = compilation.assets[key];
        let source = asset.source().replace(/swh.\[name\]/g, 'swh.' + bundleName);
        compilation.assets[key] = Object.assign(asset, {
          source: () => {
            return source;
          }
        });
      });
    });
  }

};

module.exports = FixSwhSourceMapsPlugin;
