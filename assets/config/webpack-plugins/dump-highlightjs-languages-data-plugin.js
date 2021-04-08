/**
 * Copyright (C) 2020  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

'use strict';

const fs = require('fs');
const path = require('path');
const hljs = require('highlight.js');
var stringify = require('json-stable-stringify');

// Simple webpack plugin to dump JSON data related to the set of
// programming languages supported by the highlightjs library.
// The JSON file is saved into swh-web static folder and will
// be consumed by the backend django application.

class DumpHighlightjsLanguagesDataPlugin {

  apply(compiler) {
    compiler.hooks.done.tap('DumpHighlightjsLanguagesDataPlugin', statsObj => {
      const outputPath = statsObj.compilation.compiler.outputPath;
      const hljsDataFile = path.join(outputPath, 'json/highlightjs-languages.json');
      const languages = hljs.listLanguages();
      const hljsLanguagesData = {'languages': languages};
      const languageAliases = {};
      for (let language of languages) {
        const languageData = hljs.getLanguage(language);
        if (!languageData.hasOwnProperty('aliases')) {
          continue;
        }
        for (let alias of languageData.aliases) {
          languageAliases[alias] = language;
          languageAliases[alias.toLowerCase()] = language;
        }
      }
      hljsLanguagesData['languages_aliases'] = languageAliases;
      fs.writeFileSync(hljsDataFile, stringify(hljsLanguagesData, {space: 4}));
    });
  }

};

module.exports = DumpHighlightjsLanguagesDataPlugin;
