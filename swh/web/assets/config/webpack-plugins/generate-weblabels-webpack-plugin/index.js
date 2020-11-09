/**
 * Copyright (C) 2019  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

// This is a plugin for webpack >= 4 enabling to generate a Web Labels page intended
// to be consume by the LibreJS Firefox plugin (https://www.gnu.org/software/librejs/).
// See README.md for its complete documentation.

const ejs = require('ejs');
const fs = require('fs');
const log = require('webpack-log');
const path = require('path');
const schema = require('./plugin-options-schema.json');
const spdxParse = require('spdx-expression-parse');
const spdxLicensesMapping = require('./spdx-licenses-mapping');
const {validate} = require('schema-utils');

const pluginName = 'GenerateWebLabelsPlugin';

class GenerateWebLabelsPlugin {

  constructor(opts) {
    // check that provided options match JSON schema
    validate(schema, opts, pluginName);
    this.options = opts || {};
    this.weblabelsDirName = this.options['outputDir'] || 'jssources';
    this.outputType = this.options['outputType'] || 'html';
    // source file extension handled by webpack and compiled to js
    this.srcExts = ['js', 'ts', 'coffee', 'lua'];
    this.srcExtsRegexp = new RegExp('^.*.(' + this.srcExts.join('|') + ')$');
    this.chunkNameToJsAsset = {};
    this.chunkJsAssetToSrcFiles = {};
    this.srcIdsInChunkJsAsset = {};
    this.packageJsonCache = {};
    this.packageLicenseFile = {};
    this.exclude = [];
    this.copiedFiles = new Set();
    this.logger = log({name: pluginName});
    // populate module prefix patterns to exclude
    if (Array.isArray(this.options['exclude'])) {
      this.options['exclude'].forEach(toExclude => {
        if (!toExclude.startsWith('.')) {
          this.exclude.push('./' + path.join('node_modules', toExclude));
        } else {
          this.exclude.push(toExclude);
        }
      });
    }
  }

  apply(compiler) {
    compiler.hooks.done.tap(pluginName, statsObj => {

      // get the stats object in JSON format
      let stats = statsObj.toJson();
      this.stats = stats;

      // set output folder
      this.weblabelsOutputDir = path.join(stats.outputPath, this.weblabelsDirName);
      this.recursiveMkdir(this.weblabelsOutputDir);

      // map each generated webpack chunk to its js asset
      Object.keys(stats.assetsByChunkName).forEach((chunkName, i) => {
        if (Array.isArray(stats.assetsByChunkName[chunkName])) {
          for (let asset of stats.assetsByChunkName[chunkName]) {
            if (asset.endsWith('.js')) {
              this.chunkNameToJsAsset[chunkName] = asset;
              this.chunkNameToJsAsset[i] = asset;
              break;
            }
          }
        } else if (stats.assetsByChunkName[chunkName].endsWith('.js')) {
          this.chunkNameToJsAsset[chunkName] = stats.assetsByChunkName[chunkName];
          this.chunkNameToJsAsset[i] = stats.assetsByChunkName[chunkName];
        }
      });

      // iterate on all bundled webpack modules
      stats.modules.forEach(mod => {

        let srcFilePath = mod.name;

        // do not process non js related modules
        if (!this.srcExtsRegexp.test(srcFilePath)) {
          return;
        }

        // do not process modules unrelated to a source file
        if (!srcFilePath.startsWith('./')) {
          return;
        }

        // do not process modules in the exclusion list
        for (let toExclude of this.exclude) {
          if (srcFilePath.startsWith(toExclude)) {
            return;
          }
        }

        // remove webpack loader call if any
        let loaderEndPos = srcFilePath.indexOf('!');
        if (loaderEndPos !== -1) {
          srcFilePath = srcFilePath.slice(loaderEndPos + 1);
        }

        // iterate on all chunks containing the module
        mod.chunks.forEach(chunk => {

          let chunkJsAsset = stats.publicPath + this.chunkNameToJsAsset[chunk];

          // init the chunk to source files mapping if needed
          if (!this.chunkJsAssetToSrcFiles.hasOwnProperty(chunkJsAsset)) {
            this.chunkJsAssetToSrcFiles[chunkJsAsset] = [];
            this.srcIdsInChunkJsAsset[chunkJsAsset] = new Set();
          }
          // check if the source file needs to be replaces
          if (this.options['srcReplace'] && this.options['srcReplace'].hasOwnProperty(srcFilePath)) {
            srcFilePath = this.options['srcReplace'][srcFilePath];
          }

          // init source file metadata
          let srcFileData = {'id': this.cleanupPath(srcFilePath)};

          // find and parse the corresponding package.json file
          let packageJsonPath;
          let nodeModule = srcFilePath.startsWith('./node_modules/');
          if (nodeModule) {
            packageJsonPath = this.findPackageJsonPath(srcFilePath);
          } else {
            packageJsonPath = './package.json';
          }
          let packageJson = this.parsePackageJson(packageJsonPath);

          // extract license information, overriding it if needed
          let licenseOverridden = false;
          let licenseFilePath;
          if (this.options['licenseOverride']) {
            for (let srcFilePrefixKey of Object.keys(this.options['licenseOverride'])) {
              let srcFilePrefix = srcFilePrefixKey;
              if (!srcFilePrefixKey.startsWith('.')) {
                srcFilePrefix = './' + path.join('node_modules', srcFilePrefixKey);
              }
              if (srcFilePath.startsWith(srcFilePrefix)) {
                let spdxLicenseExpression = this.options['licenseOverride'][srcFilePrefixKey]['spdxLicenseExpression'];
                licenseFilePath = this.options['licenseOverride'][srcFilePrefixKey]['licenseFilePath'];
                let parsedSpdxLicenses = this.parseSpdxLicenseExpression(spdxLicenseExpression, `file ${srcFilePath}`);
                srcFileData['licenses'] = this.spdxToWebLabelsLicenses(parsedSpdxLicenses);
                licenseOverridden = true;
                break;
              }
            }
          }

          if (!licenseOverridden) {
            srcFileData['licenses'] = this.extractLicenseInformation(packageJson);
            let licenseDir = path.join(...packageJsonPath.split('/').slice(0, -1));
            licenseFilePath = this.findLicenseFile(licenseDir);
          }

          // copy original license file and get its url
          let licenseCopyUrl = this.copyLicenseFile(licenseFilePath);
          srcFileData['licenses'].forEach(license => {
            license['copy_url'] = licenseCopyUrl;
          });

          // generate url for downloading non-minified source code
          srcFileData['src_url'] = stats.publicPath + path.join(this.weblabelsDirName, srcFileData['id']);

          // add source file metadata to the webpack chunk
          this.addSrcFileDataToJsChunkAsset(chunkJsAsset, srcFileData);
          // copy non-minified source to output folder
          this.copyFileToOutputPath(srcFilePath);
        });
      });

      // process additional scripts if needed
      if (this.options['additionalScripts']) {
        for (let script of Object.keys(this.options['additionalScripts'])) {
          let scriptFilesData = this.options['additionalScripts'][script];
          if (script.indexOf('://') === -1 && !script.startsWith('/')) {
            script = stats.publicPath + script;
          }
          this.chunkJsAssetToSrcFiles[script] = [];
          this.srcIdsInChunkJsAsset[script] = new Set();
          for (let scriptSrc of scriptFilesData) {
            let scriptSrcData = {'id': scriptSrc['id']};
            let licenceFilePath = scriptSrc['licenseFilePath'];
            let parsedSpdxLicenses = this.parseSpdxLicenseExpression(scriptSrc['spdxLicenseExpression'],
                                                                     `file ${scriptSrc['path']}`);
            scriptSrcData['licenses'] = this.spdxToWebLabelsLicenses(parsedSpdxLicenses);
            if (licenceFilePath.indexOf('://') === -1 && !licenceFilePath.startsWith('/')) {
              let licenseCopyUrl = this.copyLicenseFile(licenceFilePath);
              scriptSrcData['licenses'].forEach(license => {
                license['copy_url'] = licenseCopyUrl;
              });
            } else {
              scriptSrcData['licenses'].forEach(license => {
                license['copy_url'] = licenceFilePath;
              });
            }
            if (scriptSrc['path'].indexOf('://') === -1 && !scriptSrc['path'].startsWith('/')) {
              scriptSrcData['src_url'] = stats.publicPath + path.join(this.weblabelsDirName, scriptSrc['id']);
            } else {
              scriptSrcData['src_url'] = scriptSrc['path'];
            }
            this.addSrcFileDataToJsChunkAsset(script, scriptSrcData);
            this.copyFileToOutputPath(scriptSrc['path']);
          }
        }
      }

      for (let srcFiles of Object.values(this.chunkJsAssetToSrcFiles)) {
        srcFiles.sort((a, b) => a.id.localeCompare(b.id));
      }

      if (this.outputType === 'json') {
        // generate the jslicenses.json file
        let weblabelsData = JSON.stringify(this.chunkJsAssetToSrcFiles);
        let weblabelsJsonFile = path.join(this.weblabelsOutputDir, 'jslicenses.json');
        fs.writeFileSync(weblabelsJsonFile, weblabelsData);
      } else {
        // generate the jslicenses.html file
        let weblabelsPageFile = path.join(this.weblabelsOutputDir, 'jslicenses.html');
        ejs.renderFile(path.join(__dirname, 'jslicenses.ejs'),
                       {'jslicenses_data': this.chunkJsAssetToSrcFiles},
                       {'rmWhitespace': true},
                       (e, str) => {
                         fs.writeFileSync(weblabelsPageFile, str);
                       });
      }
    });
  }

  addSrcFileDataToJsChunkAsset(chunkJsAsset, srcFileData) {
    if (!this.srcIdsInChunkJsAsset[chunkJsAsset].has(srcFileData['id'])) {
      this.chunkJsAssetToSrcFiles[chunkJsAsset].push(srcFileData);
      this.srcIdsInChunkJsAsset[chunkJsAsset].add(srcFileData['id']);
    }
  }

  cleanupPath(moduleFilePath) {
    return moduleFilePath.replace(/^[./]*node_modules\//, '').replace(/^.\//, '');
  }

  findPackageJsonPath(srcFilePath) {
    let pathSplit = srcFilePath.split('/');
    let packageJsonPath;
    for (let i = 3; i < pathSplit.length; ++i) {
      packageJsonPath = path.join(...pathSplit.slice(0, i), 'package.json');
      if (fs.existsSync(packageJsonPath)) {
        break;
      }
    }
    return packageJsonPath;
  }

  findLicenseFile(packageJsonDir) {
    if (!this.packageLicenseFile.hasOwnProperty(packageJsonDir)) {
      let foundLicenseFile;
      fs.readdirSync(packageJsonDir).forEach(file => {
        if (foundLicenseFile) {
          return;
        }
        if (file.toLowerCase().startsWith('license')) {
          foundLicenseFile = path.join(packageJsonDir, file);
        }
      });
      this.packageLicenseFile[packageJsonDir] = foundLicenseFile;
    }
    return this.packageLicenseFile[packageJsonDir];
  }

  copyLicenseFile(licenseFilePath) {
    let licenseCopyPath = '';
    if (licenseFilePath && fs.existsSync(licenseFilePath)) {
      let ext = '';
      // add a .txt extension in order to serve license file with text/plain
      // content type to client browsers
      if (licenseFilePath.toLowerCase().indexOf('license.') === -1) {
        ext = '.txt';
      }
      this.copyFileToOutputPath(licenseFilePath, ext);
      licenseFilePath = this.cleanupPath(licenseFilePath);
      licenseCopyPath = this.stats.publicPath + path.join(this.weblabelsDirName, licenseFilePath + ext);
    }
    return licenseCopyPath;
  }

  parsePackageJson(packageJsonPath) {
    if (!this.packageJsonCache.hasOwnProperty(packageJsonPath)) {
      let packageJsonStr = fs.readFileSync(packageJsonPath).toString('utf8');
      this.packageJsonCache[packageJsonPath] = JSON.parse(packageJsonStr);
    }
    return this.packageJsonCache[packageJsonPath];
  }

  parseSpdxLicenseExpression(spdxLicenseExpression, context) {
    let parsedLicense;
    try {
      parsedLicense = spdxParse(spdxLicenseExpression);
      if (spdxLicenseExpression.indexOf('AND') !== -1) {
        this.logger.warn(`The SPDX license expression '${spdxLicenseExpression}' associated to ${context} ` +
                         'contains an AND operator, this is currently not properly handled and erroneous ' +
                         'licenses information may be provided to LibreJS');
      }
    } catch (e) {
      this.logger.warn(`Unable to parse the SPDX license expression '${spdxLicenseExpression}' associated to ${context}.`);
      this.logger.warn('Some generated JavaScript assets may be blocked by LibreJS due to missing license information.');
      parsedLicense = {'license': spdxLicenseExpression};
    }
    return parsedLicense;
  }

  spdxToWebLabelsLicense(spdxLicenceId) {
    for (let i = 0; i < spdxLicensesMapping.length; ++i) {
      if (spdxLicensesMapping[i]['spdx_ids'].indexOf(spdxLicenceId) !== -1) {
        let licenseData = Object.assign({}, spdxLicensesMapping[i]);
        delete licenseData['spdx_ids'];
        delete licenseData['magnet_link'];
        licenseData['copy_url'] = '';
        return licenseData;
      }
    }
    this.logger.warn(`Unable to associate the SPDX license identifier '${spdxLicenceId}' to a LibreJS supported license.`);
    this.logger.warn('Some generated JavaScript assets may be blocked by LibreJS due to missing license information.');
    return {
      'name': spdxLicenceId,
      'url': '',
      'copy_url': ''
    };
  }

  spdxToWebLabelsLicenses(spdxLicenses) {
    // This method simply extracts all referenced licenses in the SPDX expression
    // regardless of their combinations.
    // TODO: Handle licenses combination properly once LibreJS has a spec for it.
    let ret = [];
    if (spdxLicenses.hasOwnProperty('license')) {
      ret.push(this.spdxToWebLabelsLicense(spdxLicenses['license']));
    } else if (spdxLicenses.hasOwnProperty('left')) {
      if (spdxLicenses['left'].hasOwnProperty('license')) {
        let licenseData = this.spdxToWebLabelsLicense(spdxLicenses['left']['license']);
        ret.push(licenseData);
      } else {
        ret = ret.concat(this.spdxToWebLabelsLicenses(spdxLicenses['left']));
      }
      ret = ret.concat(this.spdxToWebLabelsLicenses(spdxLicenses['right']));
    }
    return ret;
  }

  extractLicenseInformation(packageJson) {
    let spdxLicenseExpression;
    if (packageJson.hasOwnProperty('license')) {
      spdxLicenseExpression = packageJson['license'];
    } else if (packageJson.hasOwnProperty('licenses')) {
      // for node packages using deprecated licenses property
      let licenses = packageJson['licenses'];
      if (Array.isArray(licenses)) {
        let l = [];
        licenses.forEach(license => {
          l.push(license['type']);
        });
        spdxLicenseExpression = l.join(' OR ');
      } else {
        spdxLicenseExpression = licenses['type'];
      }
    }
    let parsedSpdxLicenses = this.parseSpdxLicenseExpression(spdxLicenseExpression,
                                                             `module ${packageJson['name']}`);
    return this.spdxToWebLabelsLicenses(parsedSpdxLicenses);
  }

  copyFileToOutputPath(srcFilePath, ext = '') {
    if (this.copiedFiles.has(srcFilePath) || srcFilePath.indexOf('://') !== -1 ||
        !fs.existsSync(srcFilePath)) {
      return;
    }
    let destPath = this.cleanupPath(srcFilePath);
    let destDir = path.join(this.weblabelsOutputDir, ...destPath.split('/').slice(0, -1));
    this.recursiveMkdir(destDir);
    destPath = path.join(this.weblabelsOutputDir, destPath + ext);
    fs.copyFileSync(srcFilePath, destPath);
    this.copiedFiles.add(srcFilePath);
  }

  recursiveMkdir(destPath) {
    let destPathSplit = destPath.split('/');
    for (let i = 1; i < destPathSplit.length; ++i) {
      let currentPath = path.join('/', ...destPathSplit.slice(0, i + 1));
      if (!fs.existsSync(currentPath)) {
        fs.mkdirSync(currentPath);
      }
    }
  }

};

module.exports = GenerateWebLabelsPlugin;
