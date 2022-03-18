/**
 * Copyright (C) 2018-2022  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

// highlightjs chunk that will be lazily loaded

// main highlight.js package
import 'highlight.js';

// add highlighting support for languages not included in highlight.js package
import 'highlightjs-4d/dist/4d.min';
import 'highlightjs-sap-abap/dist/abap.min';
import 'highlightjs-alan/dist/alan.min';
import 'highlightjs-blade/dist/blade.min';
import 'highlightjs-chaos/dist/chaos.min';
import 'highlightjs-chapel/dist/chapel.min';
import 'highlightjs-cpcdos/dist/cpc-highlight.min';
import 'highlightjs-cshtml-razor/dist/cshtml-razor.min';
import 'highlightjs-cypher/dist/cypher.min';
import 'highlightjs-dafny/dist/dafny.min';
import 'highlightjs-dylan/dist/dylan.min';
import 'highlightjs-eta/dist/eta.min';
import 'highlightjs-extempore/dist/extempore.min';
import 'highlightjs-gdscript/dist/gdscript.min';
import 'highlightjs-gf/dist/gf.min';
import 'highlightjs-gsql/dist/gsql.min';
import 'highlightjs-hlsl/dist/hlsl.min';
import 'highlightjs-jolie/dist/jolie.min';
import * as hljsDefineLean from 'highlightjs-lean';
import {default as hljsDefineLox} from 'highlightjs-lox';
import 'script-loader!highlightjs-mirc/mirc';
import * as hljsDefineModelica from 'highlightjs-modelica';
import 'highlightjs-never/dist/never.min';
import {default as hljsDefineOctave} from 'highlightjs-octave';
import 'highlightjs-oz/dist/oz.min';
import 'hightlightjs-papyrus/dist/papyrus.min';
import 'highlightjs-qsharp/dist/qsharp.min';
import 'highlightjs-redbol/dist/redbol.min';
import 'script-loader!highlightjs-robot';
import 'highlightjs-robots-txt/dist/robots-txt.min';
import 'script-loader!highlightjs-rpm-specfile';
import 'highlightjs-solidity/dist/solidity.min';
import 'highlightjs-svelte/dist/svelte.min';
import 'script-loader!highlightjs-terraform';
import 'highlightjs-xsharp/dist/xsharp.min';
import 'highlightjs-zenscript/dist/zenscript.min';
import 'highlightjs-zig/dist/zig.min';

// use highlightjs-line-numbers plugin
import 'highlightjs-line-numbers.js';

// custom swh theme for highlightjs
import './hljs-swh-theme.css';

// custom CSS rules related to code block integration
import './highlightjs.css';

// add alias to match hljs 10.7 new naming
hljs.lineNumbersElement = hljs.lineNumbersBlock;

// define a synchronous version of hljs.lineNumbersElement
hljs.lineNumbersElementSync = function(elt) {
  elt.innerHTML = hljs.lineNumbersValue(elt.innerHTML);
};

hljs.registerLanguage('lean', hljsDefineLean);
hljs.registerLanguage('lox', hljsDefineLox);
hljs.registerLanguage('mirc', window.hljsDefineMIRC);
hljs.registerLanguage('modelica', hljsDefineModelica);
hljs.registerLanguage('octave', hljsDefineOctave);
hljs.registerLanguage('robot', window.hljsDefineRobot);
hljs.registerLanguage('rpm-specfile', window.hljsDefineRpmSpecfile);
hljs.registerLanguage('terraform', window.hljsDefineTerraform);
