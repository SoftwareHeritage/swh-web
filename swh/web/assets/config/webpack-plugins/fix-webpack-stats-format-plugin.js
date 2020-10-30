/**
 * Copyright (C) 2020  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

'use strict';

// Simple webpack plugin that processes the webpack-stats.json file produced by
// the latest version of webpack-bundle-tracker [1] in order to modify the JSON
// schema to the one expected by django-webpack-loader [2].
// TODO: Remove that plugin once a new version of django-webpack-loader
// is released.
// [1] https://github.com/owais/webpack-bundle-tracker
// [2] https://github.com/owais/django-webpack-loader

const fs = require('fs');
const path = require('path');

class FixWebpackStatsFormatPlugin {

  apply(compiler) {
    compiler.hooks.done.tap('FixWebpackStatsFormatPlugin', statsObj => {
      const outputPath = statsObj.compilation.compiler.outputPath;
      const statsFile = path.join(outputPath, 'webpack-stats.json');
      const statsJson = fs.readFileSync(statsFile).toString('utf8');
      const stats = JSON.parse(statsJson);
      const statsFixed = {
        status: stats.status,
        publicPath: stats.publicPath,
        chunks: {}
      };
      Object.keys(stats.chunks).forEach((chunkName) => {
        const chunkAssets = [];
        for (let asset of stats.chunks[chunkName]) {
          const publicPath = stats.assets[asset].publicPath;
          chunkAssets.push({
            name: asset,
            publicPath: publicPath,
            path: path.join(outputPath, asset)
          });
        }
        statsFixed.chunks[chunkName] = chunkAssets;
      });
      fs.writeFileSync(statsFile, JSON.stringify(statsFixed));
    });
  }

};

module.exports = FixWebpackStatsFormatPlugin;
