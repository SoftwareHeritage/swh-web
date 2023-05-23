/**
 * Copyright (C) 2018-2019  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

// webpack configuration for compiling static assets in production mode

// import required webpack plugins
const TerserPlugin = require('terser-webpack-plugin');
const OptimizeCSSAssetsPlugin = require('optimize-css-assets-webpack-plugin');
const sentryWebpackPlugin = require('@sentry/webpack-plugin').sentryWebpackPlugin;
const shelljs = require('shelljs');

// import webpack development configuration
var webpackProdConfig = require('./webpack.config.development');

// override mode to production
webpackProdConfig.mode = 'production';

// configure minimizer for js and css assets
webpackProdConfig.optimization.minimizer = [
  // use terser for minimizing js and generate source map files
  new TerserPlugin({
    parallel: true
  }),
  // use cssnano for minimizing css and generate source map files
  new OptimizeCSSAssetsPlugin({
    cssProcessorOptions: {
      map: {
        inline: false,
        annotation: true
      },
      minifyFontValues: false,
      discardUnused: false,
      zindex: false
    }
  })
];

// upload js source maps to Sentry for better debugging
webpackProdConfig.plugins.push(sentryWebpackPlugin({
  org: 'swh',
  project: 'swh-webapp',
  url: 'https://sentry.softwareheritage.org/',
  dryRun: process.env.SENTRY_AUTH_TOKEN === undefined,
  sourcemaps: {
    assets: ['static/js/**']
  },
  release: {
    name: shelljs.exec('git describe --abbrev=0', {silent: true}).stdout.slice(1, -1)
  },
  telemetry: false
}));

// prevent modules concatenation for generating weblabels
webpackProdConfig.optimization.concatenateModules = false;

// webpack production configuration
module.exports = webpackProdConfig;
