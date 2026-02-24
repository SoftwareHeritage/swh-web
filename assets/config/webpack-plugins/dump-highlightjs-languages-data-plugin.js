/**
 * Copyright (C) 2020-2026  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

'use strict';

const fs = require('fs');
const path = require('path');
global.hljs = require('highlight.js');
global.window = {};
require('highlightjs-4d/dist/4d.min');
require('highlightjs-sap-abap/dist/abap.min');
require('highlightjs-abc/dist/abc.min');
require('highlightjs-aiken/dist/aiken.min');
require('highlightjs-alan/dist/alan.min');
require('highlightjs-apex/dist/apex.min');
require('@ballerina/highlightjs-ballerina/dist/ballerina.min');
require('highlightjs-bicep/src/highlightjs/dist/bicep.min');
require('highlightjs-blade/dist/blade.min');
require('highlightjs-bqn/dist/bqn.min');
require('c3/dist/c3.min');
require('highlightjs-cairo')(hljs);
require('highlightjs-cedar/dist/hljs-cedar.min.js');
hljs.registerLanguage('cedar', window.hljsCedar);
require('highlightjs-chaos/dist/chaos.min');
require('highlightjs-chapel/dist/chapel.min');
require('highlightjs-cshtml-razor/dist/cshtml-razor.min');
require('highlightjs-cpcdos/dist/cpc-highlight.min');
require('highlightjs-cobol/dist/cobol.min');
require('highlightjs-codeowners/dist/codeowners.min');
require('highlightjs-cypher/dist/cypher.min');
require('highlightjs-dafny/dist/dafny.min');
require('highlightjs-dylan/dist/dylan.min');
require('highlightjs-eta/dist/eta.min');
require('highlightjs-extempore/dist/extempore.min');
require('highlightjs-flix/dist/flix.min');
import('highlightjs-func/dist/fift.min.js');
import('highlightjs-func/dist/func.min.js');
import('highlightjs-func/dist/tlb.min.js');
hljs.registerLanguage('gdscript', require('highlightjs-gdscript/dist/gdscript.min'));
require('highlightjs-gf/dist/gf.min');
hljs.registerLanguage('gleam', require('@gleam-lang/highlight.js-gleam'));
require('highlightjs-gsql/dist/gsql.min');
require('highlightjs-hlsl/dist/hlsl.min');
require('highlightjs-jsonata/dist/jsonata.min');
require('highlightjs-jolie/dist/jolie.min');
require('highlightjs-l4/dist/l4.min');
require('highlightjs-lang/dist/lang.min');
hljs.registerLanguage('lean', require('highlightjs-lean'));
require('highlightjs-liquid/dist/liquid.min');
require('highlightjs-lookml/dist/lookml.min');
require('highlightjs-luau/dist/luau.min');
hljs.registerLanguage('lox', require('highlightjs-lox'));
require('highlightjs-macaulay2/dist/macaulay2.min');
require('highlightjs-magik/dist/magik.min');
import('highlightjs-mint/dist/mint.min.js');
require('highlightjs-mirc/mirc')(hljs);
require('mirth/dist/mirth.min');
import('highlightjs-mlir/dist/mlir.min.js');
hljs.registerLanguage('modelica', require('highlightjs-modelica'));
require('highlightjs-motoko')(hljs);
require('highlightjs-never/dist/never.min');
require('highlightjs-oak/dist/oak.min');
import('highlightjs-ocl/dist/ocl.min.js');
hljs.registerLanguage('octave', require('highlightjs-octave').default);
require('highlightjs-oz/dist/oz.min');
require('hightlightjs-papyrus/dist/papyrus.min');
require('highlightjs-phix/src/languages/phix')(hljs);
require('highlightjs-poweron/dist/poweron.min');
require('highlightjs-prisma/dist/prisma.min');
require('highlightjs-qsharp/dist/qsharp.min');
require('highlightjs-redbol/dist/redbol.min');
import('highlightjs-rescript/dist/rescript.min.js');
require('highlightjs-robot')(hljs);
require('highlightjs-robots-txt/dist/robots-txt.min');
require('highlightjs-rpm-specfile')(hljs);
require('highlightjs-sclang/dist/sclang.min');
require('highlightjs-sdml/src/language/sdml');
hljs.registerLanguage('sdml', global.sdml);
require('highlightjs-sfz/dist/sfz.min');
require('highlightjs-solidity/dist/solidity.min');
hljs.registerLanguage('iecst', require('highlightjs-structured-text/dist/iecst.min'));
import('highlight.svelte').then(svelte => {
  hljs.registerLanguage('svelte', svelte.default);
});
require('highlightjs-terraform')(hljs);
require('highlight.js-tsql/dist/tsql.min');
require('highlightjs-unison/dist/unison.min');
require('highlightjs-vba/dist/vba.min');
require('highlightjs-voltscript/dist/voltscript.min');
require('highlightjs-wgsl/dist/wgsl.min');
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
      const languages = hljs.listLanguages().concat(['odin', 'ttcn3', 'typst']).sort();
      const hljsLanguagesData = {'languages': languages};
      const languageAliases = {};
      for (const language of languages) {
        const languageData = hljs.getLanguage(language);
        if (languageData === undefined || !languageData.hasOwnProperty('aliases')) {
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
