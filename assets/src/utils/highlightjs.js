/**
 * Copyright (C) 2018-2024  The Software Heritage developers
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
import 'highlightjs-apex/dist/apex.min';
import '@ballerina/highlightjs-ballerina/dist/ballerina.min';
import 'highlightjs-blade/dist/blade.min';
import 'highlightjs-bqn/dist/bqn.min';
import 'c3/dist/c3.min';
import {cairo} from 'highlightjs-cairo';
import 'highlightjs-cedar/dist/hljs-cedar.min';
import 'highlightjs-chaos/dist/chaos.min';
import 'highlightjs-chapel/dist/chapel.min';
import 'highlightjs-cpcdos/dist/cpc-highlight.min';
import 'highlightjs-cshtml-razor/dist/cshtml-razor.min';
import 'highlightjs-cobol/dist/cobol.min';
import 'highlightjs-codeowners/dist/codeowners.min';
import 'highlightjs-cypher/dist/cypher.min';
import 'highlightjs-dafny/dist/dafny.min';
import 'highlightjs-dylan/dist/dylan.min';
import 'highlightjs-eta/dist/eta.min';
import 'highlightjs-extempore/dist/extempore.min';
import 'highlightjs-flix/dist/flix.min';
import 'highlightjs-func/dist/fift.min';
import 'highlightjs-func/dist/func.min';
import 'highlightjs-func/dist/tlb.min';
import 'highlightjs-gdscript/dist/gdscript.min';
import 'highlightjs-gf/dist/gf.min';
import 'highlightjs-gsql/dist/gsql.min';
import 'highlightjs-hlsl/dist/hlsl.min';
import 'highlightjs-jolie/dist/jolie.min';
import 'highlightjs-jsonata/dist/jsonata.min';
import 'highlightjs-lang/dist/lang.min';
import * as hljsDefineLean from 'highlightjs-lean';
import 'highlightjs-liquid/dist/liquid.min';
import 'highlightjs-lookml/dist/lookml.min';
import 'highlightjs-luau/dist/luau.min';
import {default as hljsDefineLox} from 'highlightjs-lox';
import 'highlightjs-macaulay2/dist/macaulay2.min';
import 'highlightjs-mint/dist/mint.min';
import 'script-loader!highlightjs-mirc/mirc';
import 'mirth/dist/mirth.min';
import 'highlightjs-mlir/dist/mlir.min';
import * as hljsDefineModelica from 'highlightjs-modelica';
import {motoko, candid} from 'highlightjs-motoko';
import 'highlightjs-never/dist/never.min';
import 'highlightjs-oak/dist/oak.min';
import 'highlightjs-ocl/dist/ocl.min';
import {default as hljsDefineOctave} from 'highlightjs-octave';
import {default as hljsDefineOdin} from 'highlightjs-odin/dist/odin.min';
import 'highlightjs-oz/dist/oz.min';
import 'hightlightjs-papyrus/dist/papyrus.min';
import 'highlightjs-phix/src/languages/phix';
import 'highlightjs-poweron/dist/poweron.min';
import 'highlightjs-qsharp/dist/qsharp.min';
import 'highlightjs-redbol/dist/redbol.min';
import 'highlightjs-rescript/dist/rescript.min';
import 'script-loader!highlightjs-robot';
import 'highlightjs-robots-txt/dist/robots-txt.min';
import 'script-loader!highlightjs-rpm-specfile';
import 'highlightjs-sclang/dist/sclang.min';
import 'highlightjs-sdml/src/language/sdml';
import 'highlightjs-sfz/dist/sfz.min';
import 'highlightjs-solidity/dist/solidity.min';
import 'highlightjs-structured-text/dist/iecst.min';
import 'highlight.svelte/dist/svelte.min';
import 'script-loader!highlightjs-terraform';
import 'highlight.js-tsql/dist/tsql.min';
import {default as hljsDefineTTCN3} from 'highlightjs-ttcn3';
import 'highlightjs-unison/dist/unison.min';
import 'highlightjs-vba/dist/vba.min';
import 'highlightjs-wgsl/dist/wgsl.min';
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
  $('.hljs-ln').attr('role', 'presentation');
};

hljs.registerLanguage('cairo', cairo);
hljs.registerLanguage('candid', candid);
hljs.registerLanguage('cedar', window.hljsCedar);
hljs.registerLanguage('lean', hljsDefineLean);
hljs.registerLanguage('lox', hljsDefineLox);
hljs.registerLanguage('mirc', window.hljsDefineMIRC);
hljs.registerLanguage('modelica', hljsDefineModelica);
hljs.registerLanguage('motoko', motoko);
hljs.registerLanguage('octave', hljsDefineOctave);
hljs.registerLanguage('odin', hljsDefineOdin);
hljs.registerLanguage('robot', window.hljsDefineRobot);
hljs.registerLanguage('rpm-specfile', window.hljsDefineRpmSpecfile);
hljs.registerLanguage('sdml', window.sdml);
hljs.registerLanguage('terraform', window.hljsDefineTerraform);
hljs.registerLanguage('ttcn3', hljsDefineTTCN3);
