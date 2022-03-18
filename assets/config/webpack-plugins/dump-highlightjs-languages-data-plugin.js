/**
 * Copyright (C) 2020-2022  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

'use strict';

const fs = require('fs');
const path = require('path');
global.hljs = require('highlight.js');
require('highlightjs-4d/dist/4d.min');
require('highlightjs-sap-abap/dist/abap.min');
require('highlightjs-alan/dist/alan.min');
require('highlightjs-blade/dist/blade.min');
require('highlightjs-chaos/dist/chaos.min');
require('highlightjs-chapel/dist/chapel.min');
require('highlightjs-cshtml-razor/dist/cshtml-razor.min');
require('highlightjs-cpcdos/dist/cpc-highlight.min');
require('highlightjs-cypher/dist/cypher.min');
require('highlightjs-dafny/dist/dafny.min');
require('highlightjs-dylan/dist/dylan.min');
require('highlightjs-eta/dist/eta.min');
require('highlightjs-extempore/dist/extempore.min');
require('highlightjs-gdscript/dist/gdscript.min');
require('highlightjs-gf/dist/gf.min');
require('highlightjs-gsql/dist/gsql.min');
require('highlightjs-hlsl/dist/hlsl.min');
require('highlightjs-jolie/dist/jolie.min');
hljs.registerLanguage('lean', require('highlightjs-lean'));
hljs.registerLanguage('lox', require('highlightjs-lox'));
require('highlightjs-mirc/mirc')(hljs);
hljs.registerLanguage('modelica', require('highlightjs-modelica'));
require('highlightjs-never/dist/never.min');
hljs.registerLanguage('octave', require('highlightjs-octave').default);
require('highlightjs-oz/dist/oz.min');
require('hightlightjs-papyrus/dist/papyrus.min');
require('highlightjs-qsharp/dist/qsharp.min');
require('highlightjs-redbol/dist/redbol.min');
require('highlightjs-robot')(hljs);
require('highlightjs-robots-txt/dist/robots-txt.min');
require('highlightjs-rpm-specfile')(hljs);
require('highlightjs-solidity/dist/solidity.min');
require('highlightjs-svelte/dist/svelte.min');
require('highlightjs-terraform')(hljs);
require('highlightjs-xsharp/dist/xsharp.min');
require('highlightjs-zenscript/dist/zenscript.min');
require('highlightjs-zig/dist/zig.min');

const stringify = require('json-stable-stringify');

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
      for (const language of languages) {
        const languageData = hljs.getLanguage(language);
        if (!languageData.hasOwnProperty('aliases')) {
          continue;
        }
        for (const alias of languageData.aliases) {
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
