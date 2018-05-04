/**
 * Copyright (C) 2018  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

// Adapted and ported to Webpack 4 from
// https://github.com/rbarilani/remove-source-map-url-webpack-plugin
// Enable to remove source map url annotation embedded in vendor modules.
// The purpose is to remove warnings in js console after bundling them with webpack.

'use strict';

class RemoveSourceMapURLWebpackPlugin {

  constructor(opts) {
    this.options = opts || {};
    this.options.test = this.options.test || /\.js($|\?)/i;
  }

  testKey(key) {
    if (this.options.test instanceof RegExp) {
      return this.options.test.test(key);
    }

    if (typeof this.options.test === 'string') {
      return this.options.test === key;
    }

    if (typeof this.options.test === 'function') {
      return this.options.test(key);
    }

    throw new Error(`remove-source-map-url: Invalid "test" option. May be a RegExp (tested against asset key), a string containing the key, a function(key): bool`);
  }

  apply(compiler) {
    compiler.hooks.afterCompile.tap('RemoveSourceMapUrlPlugin', compilation => {
      Object.keys(compilation.assets).filter(key => {
        return this.testKey(key);
      }).forEach(key => {
        let asset = compilation.assets[key];
        let source = asset.source().replace(/# sourceMappingURL=(.*\.map)/g, '# $1');
        compilation.assets[key] = Object.assign(asset, {
          source: () => {
            return source;
          }
        });
      });
    });
  }

};

module.exports = RemoveSourceMapURLWebpackPlugin;
