/*! For license information please see revision.e17cd43c375d7191f9da.js.LICENSE.txt */
!function(e,t){"object"==typeof exports&&"object"==typeof module?module.exports=t():"function"==typeof define&&define.amd?define([],t):"object"==typeof exports?exports.swh=t():(e.swh=e.swh||{},e.swh.revision=t())}(self,(function(){return function(){var __webpack_modules__={87757:function(e,t,n){e.exports=n(35666)},31463:function(e,t,n){"use strict";n.d(t,{OU:function(){return C},sr:function(){return A},S0:function(){return q},EV:function(){return P},n2:function(){return R},Mo:function(){return W},D_:function(){return H},St:function(){return Q},qo:function(){return G}});var r,i=n(15861),o=n(87757),a=n.n(o),s=(n(43511),n(86515)),l=n(59537),c=n(69548),u=n.n(c),f=null,d=0,h=0,p='<span class="no-nl-marker" style="color: red;" title="No newline at end of file"><i class="mdi mdi-rotate-90 mdi-cancel" aria-hidden="true"><i class="mdi mdi-keyboard-return" aria-hidden="true"></span>',_=0,w=0,g={},m={},v=null,y=null,b={},x=null,k="#swh-revision-changes",S="Files";function j(e){var t=$(e).offset().top,n=t+$(e).outerHeight(),r=$(window).scrollTop(),i=r+$(window).height();return n>r&&t<i}function C(e,t,n){for(var r=b[e],i=L(t),o=L(n),a="",s=0;s<r-i.length;++s)a+=" ";a+=i,a+="  ";for(var l=0;l<r-o.length;++l)a+=" ";return a+=o}function T(e){var t,n;if(e.startsWith("@@")){var r=new RegExp(/^@@ -(\d+),(\d+) \+(\d+),(\d+) @@$/gm),i=new RegExp(/^@@ -(\d+) \+(\d+),(\d+) @@$/gm),o=new RegExp(/^@@ -(\d+),(\d+) \+(\d+) @@$/gm),a=new RegExp(/^@@ -(\d+) \+(\d+) @@$/gm),s=r.exec(e),l=i.exec(e),c=o.exec(e),u=a.exec(e);s?(t=parseInt(s[1])-1,n=parseInt(s[3])-1):l?(t=parseInt(l[1])-1,n=parseInt(l[2])-1):c?(t=parseInt(c[1])-1,n=parseInt(c[3])-1):u&&(t=parseInt(u[1])-1,n=parseInt(u[2])-1)}return void 0!==t?[t,n]:null}function E(e){return e?parseInt(e):0}function L(e){return e?e.toString():""}function A(e,t,n){var r;if(t||n){var i=E(e.trim());t?r=[i,0]:n&&(r=[0,i])}else(r=e.replace(/[ ]+/g," ").split(" ")).length>2&&r.shift(),r=r.map((function(e){return E(e)}));return r}function q(e,t,n){var r="";return r+="F"+(e[0]||0),r+="T"+(e[1]||0),r+="-F"+(t[0]||0),r+="T"+(t[1]||0),r+=n?"-unified":"-split"}function P(e){var t=/F([0-9]+)T([0-9]+)-F([0-9]+)T([0-9]+)-([a-z]+)/.exec(e);return 6===t.length?{startLines:[parseInt(t[1]),parseInt(t[2])],endLines:[parseInt(t[3]),parseInt(t[4])],unified:"unified"===t[5]}:null}function F(e,t){var n=$("#"+e+' .hljs-ln-line[data-line-number="'+t+'"]'),r=$("#"+e+' .hljs-ln-numbers[data-line-number="'+t+'"]');return r.css("color","black"),r.css("font-weight","bold"),n.css("background-color","#fdf3da"),n.css("mix-blend-mode","multiply"),n}function O(e){void 0===e&&(e=!0),e&&(x=null,v=null,y=null),$(".hljs-ln-line[data-line-number]").css("background-color","initial"),$(".hljs-ln-line[data-line-number]").css("mix-blend-mode","initial"),$(".hljs-ln-numbers[data-line-number]").css("color","#aaa"),$(".hljs-ln-numbers[data-line-number]").css("font-weight","initial"),"Changes"===S&&window.location.hash!==k&&window.history.replaceState("",document.title,window.location.pathname+window.location.search+k)}function D(e,t,n,r){var i;if(r){var o=C(e,t[0],t[1]),a=C(e,n[0],n[1]),s=$("#"+e+' .hljs-ln-line[data-line-number="'+o+'"]'),l=$("#"+e+' .hljs-ln-line[data-line-number="'+a+'"]');if($(l).position().top<$(s).position().top){var c=[a,o];o=c[0],a=c[1],i=l}else i=s;for(var u=F(e,o),f=$(u).closest("tr"),d=$(f).children(".hljs-ln-line").data("line-number").toString();d!==a;)d.trim()&&F(e,d),f=$(f).next(),d=$(f).children(".hljs-ln-line").data("line-number").toString();F(e,a)}else if(t[0]&&n[0]){for(var h=Math.min(t[0],n[0]),p=Math.max(t[0],n[0]),_=h;_<=p;++_)F(e+"-from",_);i=$("#"+e+'-from .hljs-ln-line[data-line-number="'+h+'"]')}else if(t[1]&&n[1]){for(var w=Math.min(t[1],n[1]),g=Math.max(t[1],n[1]),m=w;m<=g;++m)F(e+"-to",m);i=$("#"+e+'-to .hljs-ln-line[data-line-number="'+w+'"]')}else{var v,y;t[0]&&n[1]?(v=t[0],y=n[1]):(v=n[0],y=t[1]);var b=$("#"+e+'-from .hljs-ln-line[data-line-number="'+v+'"]'),x=$("#"+e+'-to .hljs-ln-line[data-line-number="'+y+'"]'),k=$(b).position().top<$(x).position().top;i=k?b:x;for(var S=$("#"+e+"-from tr").first(),j=$(S).children(".hljs-ln-line").data("line-number"),T=$("#"+e+"-to tr").first(),E=$(T).children(".hljs-ln-line").data("line-number"),L=!1;k&&j===v?L=!0:k||E!==y||(L=!0),L&&j&&F(e+"-from",j),L&&E&&F(e+"-to",E),!(k&&E===y||!k&&j===v);)S=$(S).next(),j=$(S).children(".hljs-ln-line").data("line-number"),T=$(T).next(),E=$(T).children(".hljs-ln-line").data("line-number")}var A=q(t,n,r);return window.location.hash="diff_"+e+"+"+A,i}function R(e){$("#"+e+"-split-diff").css("display","none"),$("#"+e+"-unified-diff").css("display","block")}function W(e){$("#"+e+"-unified-diff").css("display","none"),$("#"+e+"-split-diff").css("display","block")}function H(e,t){return N.apply(this,arguments)}function N(){return(N=(0,i.Z)(a().mark((function e(t,n){var i,o,s,l,c,u,d,m,v,y,x,k,S;return a().wrap((function(e){for(;;)switch(e.prev=e.next){case 0:if(i=function(e,t){$(e).attr("data-line-number",t||""),$(e).children().attr("data-line-number",t||""),$(e).siblings().attr("data-line-number",t||"")},-1!==t.indexOf("force=true")||!g.hasOwnProperty(n)){e.next=4;break}return e.abrupt("return");case 4:return g[n]=!0,$("#"+n+"-loading").css("visibility","visible"),$("#"+n+"-loading").css("display","block"),$("#"+n+"-highlightjs").css("display","none"),e.next=10,fetch(t);case 10:return o=e.sent,e.next=13,o.json();case 13:s=e.sent,++h===f.length&&$("#swh-compute-all-diffs").addClass("active"),0===s.diff_str.indexOf("Large diff")?($("#"+n)[0].innerHTML=s.diff_str+'<br/><button class="btn btn-default btn-sm" type="button"\n           onclick="swh.revision.computeDiff(\''+t+"&force=true', '"+n+"')\">Request diff</button>",I(n)):0!==s.diff_str.indexOf("@@")?($("#"+n).text(s.diff_str),I(n)):($("."+n).removeClass("nohighlight"),$("."+n).addClass(s.language),$("#"+n).text(s.diff_str),$("#"+n).each((function(e,t){hljs.highlightElement(t),hljs.lineNumbersElementSync(t)})),l="",c="",u=[],d=[],m=[],v=0,y="",x="",k=0,$("#"+n+" .hljs-ln-numbers").each((function(e,t){var n=t.nextSibling.innerText,r=T(n),i="",o="";if(r)l=r[0],c=r[1],k=0,y+=n+"\n",x+=n+"\n",d.push(""),m.push("");else if(n.length>0&&"-"===n[0])i=(l+=1).toString(),d.push(i),++w,y+=n+"\n",++k;else if(n.length>0&&"+"===n[0])o=(c+=1).toString(),m.push(o),++_,x+=n+"\n",--k;else{c+=1,i=(l+=1).toString(),o=c.toString();for(var a=0;a<Math.abs(k);++a)k>0?(x+="\n",m.push("")):(y+="\n",d.push(""));k=0,y+=n+"\n",x+=n+"\n",m.push(o),d.push(i)}l||(i=""),c||(o=""),u[e]=[i,o],v=Math.max(v,i.length),v=Math.max(v,o.length)})),b[n]=v,$("#"+n+"-from").text(y),$("#"+n+"-to").text(x),$("#"+n+"-from, #"+n+"-to").each((function(e,t){hljs.highlightElement(t),hljs.lineNumbersElementSync(t)})),$("."+n+" .hljs-ln-numbers").each((function(e,t){var n=t.nextSibling.innerText;if(n.startsWith("@@")){$(t).parent().addClass("swh-diff-lines-info");var r=$(t).parent().find(".hljs-ln-code .hljs-ln-line").text();$(t).parent().find(".hljs-ln-code .hljs-ln-line").children().remove(),$(t).parent().find(".hljs-ln-code .hljs-ln-line").text(""),$(t).parent().find(".hljs-ln-code .hljs-ln-line").append('<span class="hljs-meta">'+r+"</span>")}else n.length>0&&"-"===n[0]?$(t).parent().addClass("swh-diff-removed-line"):n.length>0&&"+"===n[0]&&$(t).parent().addClass("swh-diff-added-line")})),$("#"+n+" .hljs-ln-numbers").each((function(e,t){var r=C(n,u[e][0],u[e][1]);i(t,r)})),$("#"+n+"-from .hljs-ln-numbers").each((function(e,t){i(t,d[e])})),$("#"+n+"-to .hljs-ln-numbers").each((function(e,t){i(t,m[e])})),$("."+n+" .hljs-ln-code").each((function(e,t){if(t.firstChild){if("#text"!==t.firstChild.nodeName){var n=t.firstChild.innerHTML;if("-"===n[0]||"+"===n[0]){t.firstChild.innerHTML=n.substr(1);var r=document.createTextNode(n[0]);$(t).prepend(r)}}$(t).contents().filter((function(e,t){return 3===t.nodeType})).each((function(e,n){var r="[swh-no-nl-marker]";-1!==n.textContent.indexOf(r)&&(n.textContent=n.textContent.replace(r,""),$(t).append($(p)))}))}})),0!==s.diff_str.indexOf("Diffs are not generated for non textual content")&&$("#diff_"+n+" .diff-styles").css("visibility","visible"),I(n),r&&-1!==r.diffPanelId.indexOf(n)&&(r.unified||W(n),S=D(n,r.startLines,r.endLines,r.unified),$("html, body").animate({scrollTop:S.offset().top-50},{duration:500})));case 17:case"end":return e.stop()}}),e)})))).apply(this,arguments)}function I(e){$("#"+e+"-loading").css("display","none"),$("#"+e+"-highlightjs").css("display","block"),$("#swh-revision-lines-added").text(_+" additions"),$("#swh-revision-lines-deleted").text(w+" deletions"),$("#swh-nb-diffs-computed").text(h),Waypoint.refreshAll()}function z(){$(".swh-file-diff-panel").each((function(e,t){if(j(t)){var n=t.id.replace("diff_","");H(m[n],n)}}))}function M(e){var t=e.path;return"rename"===e.type&&(t=e.from_path+" &rarr; "+e.to_path),u()({diffData:e,diffPanelTitle:t,swhSpinnerSrc:s.XC})}function U(){for(var e=0;e<f.length;++e){var t=f[e];$("#diff_"+t.id).waypoint({handler:function(){if(j(this.element)){var e=this.element.id.replace("diff_","");H(m[e],e),this.destroy()}},offset:"100%"}),$("#diff_"+t.id).waypoint({handler:function(){if(j(this.element)){var e=this.element.id.replace("diff_","");H(m[e],e),this.destroy()}},offset:function(){return-$(this.element).height()}})}Waypoint.refreshAll()}function B(e,t){void 0===t&&(t=!0),Waypoint.disableAll(),$("html, body").animate({scrollTop:$(e).offset().top},{duration:500,complete:function(){t&&(window.location.hash=e),Waypoint.enableAll(),z()}})}function Q(e){for(var t in $(e.currentTarget).addClass("active"),m)m.hasOwnProperty(t)&&H(m[t],t);e.stopPropagation()}function G(e,t){return Z.apply(this,arguments)}function Z(){return(Z=(0,i.Z)(a().mark((function e(t,o){return a().wrap((function(e){for(;;)switch(e.prev=e.next){case 0:return e.next=2,n.e(399).then(n.bind(n,68480));case 2:$(document).on("shown.bs.tab",'a[data-toggle="tab"]',function(){var e=(0,i.Z)(a().mark((function e(t){var n,i,s,c,u;return a().wrap((function(e){for(;;)switch(e.prev=e.next){case 0:if("Changes"!==(S=t.currentTarget.text.trim())){e.next=30;break}if(window.location.hash=k,$("#readme-panel").css("display","none"),!f){e.next=6;break}return e.abrupt("return");case 6:return e.next=8,fetch(o);case 8:return n=e.sent,e.next=11,n.json();case 11:for(i=e.sent,f=i.changes,d=i.total_nb_changes,s=d+" changed file",1!==d&&(s+="s"),$("#swh-revision-changed-files").text(s),$("#swh-total-nb-diffs").text(f.length),$("#swh-revision-changes-list pre")[0].innerHTML=i.changes_msg,$("#swh-revision-changes-loading").css("display","none"),$("#swh-revision-changes-list pre").css("display","block"),$("#swh-compute-all-diffs").css("visibility","visible"),$("#swh-revision-changes-list").removeClass("in"),d>f.length&&($("#swh-too-large-revision-diff").css("display","block"),$("#swh-nb-loaded-diffs").text(f.length)),c=0;c<f.length;++c)u=f[c],m[u.id]=u.diff_url,$("#swh-revision-diffs").append(M(u));U(),z(),r&&B(r.diffPanelId,!1),e.next=31;break;case 30:"Files"===S&&((0,l.L3)(),$("#readme-panel").css("display","block"));case 31:case"end":return e.stop()}}),e)})));return function(t){return e.apply(this,arguments)}}()),$(document).ready((function(){t.length>0?$("#swh-revision-message").addClass("in"):$("#swh-collapse-revision-message").attr("data-toggle",""),$('#swh-revision-changes-list a[href^="#"], #back-to-top a[href^="#"]').click((function(e){return B($.attr(e.currentTarget,"href")),!1})),$("body").click((function(e){if("Changes"===S)if(e.target.classList.contains("hljs-ln-n")){var t=$(e.target).closest("code").prop("id"),n=-1!==t.indexOf("-from"),r=-1!==t.indexOf("-to"),i=$(e.target).data("line-number").toString(),o=t.replace("-from","").replace("-to","");e.shiftKey&&o===x&&i.trim()||(O(),x=o),o===x&&i.trim()&&(e.shiftKey?v&&(O(!1),y=A(i,n,r),D(o,v,y,!n&&!r)):D(o,v=A(i,n,r),v,!n&&!r))}else O()}));var e=window.location.hash;if(e){var n=e.split("+");2===n.length&&(r=P(n[1]))&&(r.diffPanelId=n[0],$('.nav-tabs a[href="#swh-revision-changes"]').tab("show")),e===k&&$('.nav-tabs a[href="#swh-revision-changes"]').tab("show")}}));case 4:case"end":return e.stop()}}),e)})))).apply(this,arguments)}},54087:function(e,t,n){"use strict";function r(e){var t=new URLSearchParams(window.location.search);$(e.target).val()?t.set("revs_ordering",$(e.target).val()):t.has("revs_ordering")&&t.delete("revs_ordering"),window.location.search=t.toString()}function i(){$(document).ready((function(){var e=new URLSearchParams(window.location.search).get("revs_ordering");e&&$(':input[value="'+e+'"]').prop("checked",!0)}))}n.d(t,{i:function(){return r},o:function(){return i}})},86515:function(e,t,n){"use strict";n.d(t,{XC:function(){return r}});var r=(0,n(59537).TT)("img/swh-spinner.gif")},59537:function(e,t,n){"use strict";n.d(t,{TT:function(){return r},L3:function(){return i}});n(87757),n(31955);function r(e){return"/static/"+e}function i(){history.replaceState("",document.title,window.location.pathname+window.location.search)}},69548:function(module){module.exports=function anonymous(locals,escapeFn,include,rethrow){escapeFn=escapeFn||function(e){return null==e?"":String(e).replace(_MATCH_HTML,encode_char)};var _ENCODE_HTML_RULES={"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&#34;","'":"&#39;"},_MATCH_HTML=/[&<>'"]/g;function encode_char(e){return _ENCODE_HTML_RULES[e]||e}var __output="";function __append(e){null!=e&&(__output+=e)}with(locals||{})__append('\n<div id="diff_'),__append(escapeFn(diffData.id)),__append('" class="card swh-file-diff-panel">\n  <div class="card-header bg-gray-light border-bottom-0">\n    <a data-toggle="collapse" href="#diff_'),__append(escapeFn(diffData.id)),__append('_content">\n      <div class="float-left swh-title-color">\n        <strong>'),__append(escapeFn(diffPanelTitle)),__append('</strong>\n      </div>\n    </a>\n    <div class="ml-auto float-right">\n      <div class="btn-group btn-group-toggle diff-styles" data-toggle="buttons" style="visibility: hidden;">\n        <label class="btn btn-default btn-sm form-check-label active unified-diff-button" onclick="swh.revision.showUnifiedDiff(\''),__append(escapeFn(diffData.id)),__append('\')">\n          <input type="radio" name="diffs-switch" id="unified" autocomplete="off" checked="checked"> Unified\n        </label>\n        <label class="btn btn-default btn-sm form-check-label split-diff-button" onclick="swh.revision.showSplitDiff(\''),__append(escapeFn(diffData.id)),__append('\')">\n          <input type="radio" name="diffs-switch" id="side-by-side" autocomplete="off"> Side-by-side\n        </label>\n      </div>\n      <a href="'),__append(escapeFn(diffData.content_url)),__append('" class="btn btn-default btn-sm" role="button">View file</a>\n    </div>\n    <div class="clearfix"></div>\n  </div>\n  <div id="diff_'),__append(escapeFn(diffData.id)),__append('_content" class="collapse show">\n    <div class="swh-diff-loading text-center" id="'),__append(escapeFn(diffData.id)),__append('-loading" style="visibility: hidden;">\n      <img src="'),__append(escapeFn(swhSpinnerSrc)),__append('">\n      <p>Loading diff ...</p>\n    </div>\n    <div class="highlightjs swh-content" style="display: none;" id="'),__append(escapeFn(diffData.id)),__append('-highlightjs">\n      <div id="'),__append(escapeFn(diffData.id)),__append('-unified-diff">\n        <pre><code class="'),__append(escapeFn(diffData.id)),__append('" id="'),__append(escapeFn(diffData.id)),__append('"></code></pre>\n      </div>\n      <div style="width: 100%; display: none;" id="'),__append(escapeFn(diffData.id)),__append('-split-diff">\n        <pre class="float-left" style="width: 50%;"><code class="'),__append(escapeFn(diffData.id)),__append('" id="'),__append(escapeFn(diffData.id)),__append('-from"></code></pre>\n        <pre style="width: 50%;"><code class="'),__append(escapeFn(diffData.id)),__append('" id="'),__append(escapeFn(diffData.id)),__append('-to"></code></pre>\n      </div>\n    </div>\n  </div>\n</div>');return __output}},35666:function(e){var t=function(e){"use strict";var t,n=Object.prototype,r=n.hasOwnProperty,i="function"==typeof Symbol?Symbol:{},o=i.iterator||"@@iterator",a=i.asyncIterator||"@@asyncIterator",s=i.toStringTag||"@@toStringTag";function l(e,t,n){return Object.defineProperty(e,t,{value:n,enumerable:!0,configurable:!0,writable:!0}),e[t]}try{l({},"")}catch(e){l=function(e,t,n){return e[t]=n}}function c(e,t,n,r){var i=t&&t.prototype instanceof w?t:w,o=Object.create(i.prototype),a=new T(r||[]);return o._invoke=function(e,t,n){var r=f;return function(i,o){if(r===h)throw new Error("Generator is already running");if(r===p){if("throw"===i)throw o;return L()}for(n.method=i,n.arg=o;;){var a=n.delegate;if(a){var s=S(a,n);if(s){if(s===_)continue;return s}}if("next"===n.method)n.sent=n._sent=n.arg;else if("throw"===n.method){if(r===f)throw r=p,n.arg;n.dispatchException(n.arg)}else"return"===n.method&&n.abrupt("return",n.arg);r=h;var l=u(e,t,n);if("normal"===l.type){if(r=n.done?p:d,l.arg===_)continue;return{value:l.arg,done:n.done}}"throw"===l.type&&(r=p,n.method="throw",n.arg=l.arg)}}}(e,n,a),o}function u(e,t,n){try{return{type:"normal",arg:e.call(t,n)}}catch(e){return{type:"throw",arg:e}}}e.wrap=c;var f="suspendedStart",d="suspendedYield",h="executing",p="completed",_={};function w(){}function g(){}function m(){}var v={};v[o]=function(){return this};var y=Object.getPrototypeOf,b=y&&y(y(E([])));b&&b!==n&&r.call(b,o)&&(v=b);var x=m.prototype=w.prototype=Object.create(v);function k(e){["next","throw","return"].forEach((function(t){l(e,t,(function(e){return this._invoke(t,e)}))}))}function $(e,t){function n(i,o,a,s){var l=u(e[i],e,o);if("throw"!==l.type){var c=l.arg,f=c.value;return f&&"object"==typeof f&&r.call(f,"__await")?t.resolve(f.__await).then((function(e){n("next",e,a,s)}),(function(e){n("throw",e,a,s)})):t.resolve(f).then((function(e){c.value=e,a(c)}),(function(e){return n("throw",e,a,s)}))}s(l.arg)}var i;this._invoke=function(e,r){function o(){return new t((function(t,i){n(e,r,t,i)}))}return i=i?i.then(o,o):o()}}function S(e,n){var r=e.iterator[n.method];if(r===t){if(n.delegate=null,"throw"===n.method){if(e.iterator.return&&(n.method="return",n.arg=t,S(e,n),"throw"===n.method))return _;n.method="throw",n.arg=new TypeError("The iterator does not provide a 'throw' method")}return _}var i=u(r,e.iterator,n.arg);if("throw"===i.type)return n.method="throw",n.arg=i.arg,n.delegate=null,_;var o=i.arg;return o?o.done?(n[e.resultName]=o.value,n.next=e.nextLoc,"return"!==n.method&&(n.method="next",n.arg=t),n.delegate=null,_):o:(n.method="throw",n.arg=new TypeError("iterator result is not an object"),n.delegate=null,_)}function j(e){var t={tryLoc:e[0]};1 in e&&(t.catchLoc=e[1]),2 in e&&(t.finallyLoc=e[2],t.afterLoc=e[3]),this.tryEntries.push(t)}function C(e){var t=e.completion||{};t.type="normal",delete t.arg,e.completion=t}function T(e){this.tryEntries=[{tryLoc:"root"}],e.forEach(j,this),this.reset(!0)}function E(e){if(e){var n=e[o];if(n)return n.call(e);if("function"==typeof e.next)return e;if(!isNaN(e.length)){var i=-1,a=function n(){for(;++i<e.length;)if(r.call(e,i))return n.value=e[i],n.done=!1,n;return n.value=t,n.done=!0,n};return a.next=a}}return{next:L}}function L(){return{value:t,done:!0}}return g.prototype=x.constructor=m,m.constructor=g,g.displayName=l(m,s,"GeneratorFunction"),e.isGeneratorFunction=function(e){var t="function"==typeof e&&e.constructor;return!!t&&(t===g||"GeneratorFunction"===(t.displayName||t.name))},e.mark=function(e){return Object.setPrototypeOf?Object.setPrototypeOf(e,m):(e.__proto__=m,l(e,s,"GeneratorFunction")),e.prototype=Object.create(x),e},e.awrap=function(e){return{__await:e}},k($.prototype),$.prototype[a]=function(){return this},e.AsyncIterator=$,e.async=function(t,n,r,i,o){void 0===o&&(o=Promise);var a=new $(c(t,n,r,i),o);return e.isGeneratorFunction(n)?a:a.next().then((function(e){return e.done?e.value:a.next()}))},k(x),l(x,s,"Generator"),x[o]=function(){return this},x.toString=function(){return"[object Generator]"},e.keys=function(e){var t=[];for(var n in e)t.push(n);return t.reverse(),function n(){for(;t.length;){var r=t.pop();if(r in e)return n.value=r,n.done=!1,n}return n.done=!0,n}},e.values=E,T.prototype={constructor:T,reset:function(e){if(this.prev=0,this.next=0,this.sent=this._sent=t,this.done=!1,this.delegate=null,this.method="next",this.arg=t,this.tryEntries.forEach(C),!e)for(var n in this)"t"===n.charAt(0)&&r.call(this,n)&&!isNaN(+n.slice(1))&&(this[n]=t)},stop:function(){this.done=!0;var e=this.tryEntries[0].completion;if("throw"===e.type)throw e.arg;return this.rval},dispatchException:function(e){if(this.done)throw e;var n=this;function i(r,i){return s.type="throw",s.arg=e,n.next=r,i&&(n.method="next",n.arg=t),!!i}for(var o=this.tryEntries.length-1;o>=0;--o){var a=this.tryEntries[o],s=a.completion;if("root"===a.tryLoc)return i("end");if(a.tryLoc<=this.prev){var l=r.call(a,"catchLoc"),c=r.call(a,"finallyLoc");if(l&&c){if(this.prev<a.catchLoc)return i(a.catchLoc,!0);if(this.prev<a.finallyLoc)return i(a.finallyLoc)}else if(l){if(this.prev<a.catchLoc)return i(a.catchLoc,!0)}else{if(!c)throw new Error("try statement without catch or finally");if(this.prev<a.finallyLoc)return i(a.finallyLoc)}}}},abrupt:function(e,t){for(var n=this.tryEntries.length-1;n>=0;--n){var i=this.tryEntries[n];if(i.tryLoc<=this.prev&&r.call(i,"finallyLoc")&&this.prev<i.finallyLoc){var o=i;break}}o&&("break"===e||"continue"===e)&&o.tryLoc<=t&&t<=o.finallyLoc&&(o=null);var a=o?o.completion:{};return a.type=e,a.arg=t,o?(this.method="next",this.next=o.finallyLoc,_):this.complete(a)},complete:function(e,t){if("throw"===e.type)throw e.arg;return"break"===e.type||"continue"===e.type?this.next=e.arg:"return"===e.type?(this.rval=this.arg=e.arg,this.method="return",this.next="end"):"normal"===e.type&&t&&(this.next=t),_},finish:function(e){for(var t=this.tryEntries.length-1;t>=0;--t){var n=this.tryEntries[t];if(n.finallyLoc===e)return this.complete(n.completion,n.afterLoc),C(n),_}},catch:function(e){for(var t=this.tryEntries.length-1;t>=0;--t){var n=this.tryEntries[t];if(n.tryLoc===e){var r=n.completion;if("throw"===r.type){var i=r.arg;C(n)}return i}}throw new Error("illegal catch attempt")},delegateYield:function(e,n,r){return this.delegate={iterator:E(e),resultName:n,nextLoc:r},"next"===this.method&&(this.arg=t),_}},e}(e.exports);try{regeneratorRuntime=t}catch(e){Function("r","regeneratorRuntime = r")(t)}},43511:function(){!function(){"use strict";var e=0,t={};function n(r){if(!r)throw new Error("No options passed to Waypoint constructor");if(!r.element)throw new Error("No element option passed to Waypoint constructor");if(!r.handler)throw new Error("No handler option passed to Waypoint constructor");this.key="waypoint-"+e,this.options=n.Adapter.extend({},n.defaults,r),this.element=this.options.element,this.adapter=new n.Adapter(this.element),this.callback=r.handler,this.axis=this.options.horizontal?"horizontal":"vertical",this.enabled=this.options.enabled,this.triggerPoint=null,this.group=n.Group.findOrCreate({name:this.options.group,axis:this.axis}),this.context=n.Context.findOrCreateByElement(this.options.context),n.offsetAliases[this.options.offset]&&(this.options.offset=n.offsetAliases[this.options.offset]),this.group.add(this),this.context.add(this),t[this.key]=this,e+=1}n.prototype.queueTrigger=function(e){this.group.queueTrigger(this,e)},n.prototype.trigger=function(e){this.enabled&&this.callback&&this.callback.apply(this,e)},n.prototype.destroy=function(){this.context.remove(this),this.group.remove(this),delete t[this.key]},n.prototype.disable=function(){return this.enabled=!1,this},n.prototype.enable=function(){return this.context.refresh(),this.enabled=!0,this},n.prototype.next=function(){return this.group.next(this)},n.prototype.previous=function(){return this.group.previous(this)},n.invokeAll=function(e){var n=[];for(var r in t)n.push(t[r]);for(var i=0,o=n.length;i<o;i++)n[i][e]()},n.destroyAll=function(){n.invokeAll("destroy")},n.disableAll=function(){n.invokeAll("disable")},n.enableAll=function(){for(var e in n.Context.refreshAll(),t)t[e].enabled=!0;return this},n.refreshAll=function(){n.Context.refreshAll()},n.viewportHeight=function(){return window.innerHeight||document.documentElement.clientHeight},n.viewportWidth=function(){return document.documentElement.clientWidth},n.adapters=[],n.defaults={context:window,continuous:!0,enabled:!0,group:"default",horizontal:!1,offset:0},n.offsetAliases={"bottom-in-view":function(){return this.context.innerHeight()-this.adapter.outerHeight()},"right-in-view":function(){return this.context.innerWidth()-this.adapter.outerWidth()}},window.Waypoint=n}(),function(){"use strict";function e(e){window.setTimeout(e,1e3/60)}var t=0,n={},r=window.Waypoint,i=window.onload;function o(e){this.element=e,this.Adapter=r.Adapter,this.adapter=new this.Adapter(e),this.key="waypoint-context-"+t,this.didScroll=!1,this.didResize=!1,this.oldScroll={x:this.adapter.scrollLeft(),y:this.adapter.scrollTop()},this.waypoints={vertical:{},horizontal:{}},e.waypointContextKey=this.key,n[e.waypointContextKey]=this,t+=1,r.windowContext||(r.windowContext=!0,r.windowContext=new o(window)),this.createThrottledScrollHandler(),this.createThrottledResizeHandler()}o.prototype.add=function(e){var t=e.options.horizontal?"horizontal":"vertical";this.waypoints[t][e.key]=e,this.refresh()},o.prototype.checkEmpty=function(){var e=this.Adapter.isEmptyObject(this.waypoints.horizontal),t=this.Adapter.isEmptyObject(this.waypoints.vertical),r=this.element==this.element.window;e&&t&&!r&&(this.adapter.off(".waypoints"),delete n[this.key])},o.prototype.createThrottledResizeHandler=function(){var e=this;function t(){e.handleResize(),e.didResize=!1}this.adapter.on("resize.waypoints",(function(){e.didResize||(e.didResize=!0,r.requestAnimationFrame(t))}))},o.prototype.createThrottledScrollHandler=function(){var e=this;function t(){e.handleScroll(),e.didScroll=!1}this.adapter.on("scroll.waypoints",(function(){e.didScroll&&!r.isTouch||(e.didScroll=!0,r.requestAnimationFrame(t))}))},o.prototype.handleResize=function(){r.Context.refreshAll()},o.prototype.handleScroll=function(){var e={},t={horizontal:{newScroll:this.adapter.scrollLeft(),oldScroll:this.oldScroll.x,forward:"right",backward:"left"},vertical:{newScroll:this.adapter.scrollTop(),oldScroll:this.oldScroll.y,forward:"down",backward:"up"}};for(var n in t){var r=t[n],i=r.newScroll>r.oldScroll?r.forward:r.backward;for(var o in this.waypoints[n]){var a=this.waypoints[n][o];if(null!==a.triggerPoint){var s=r.oldScroll<a.triggerPoint,l=r.newScroll>=a.triggerPoint;(s&&l||!s&&!l)&&(a.queueTrigger(i),e[a.group.id]=a.group)}}}for(var c in e)e[c].flushTriggers();this.oldScroll={x:t.horizontal.newScroll,y:t.vertical.newScroll}},o.prototype.innerHeight=function(){return this.element==this.element.window?r.viewportHeight():this.adapter.innerHeight()},o.prototype.remove=function(e){delete this.waypoints[e.axis][e.key],this.checkEmpty()},o.prototype.innerWidth=function(){return this.element==this.element.window?r.viewportWidth():this.adapter.innerWidth()},o.prototype.destroy=function(){var e=[];for(var t in this.waypoints)for(var n in this.waypoints[t])e.push(this.waypoints[t][n]);for(var r=0,i=e.length;r<i;r++)e[r].destroy()},o.prototype.refresh=function(){var e,t=this.element==this.element.window,n=t?void 0:this.adapter.offset(),i={};for(var o in this.handleScroll(),e={horizontal:{contextOffset:t?0:n.left,contextScroll:t?0:this.oldScroll.x,contextDimension:this.innerWidth(),oldScroll:this.oldScroll.x,forward:"right",backward:"left",offsetProp:"left"},vertical:{contextOffset:t?0:n.top,contextScroll:t?0:this.oldScroll.y,contextDimension:this.innerHeight(),oldScroll:this.oldScroll.y,forward:"down",backward:"up",offsetProp:"top"}}){var a=e[o];for(var s in this.waypoints[o]){var l,c,u,f,d=this.waypoints[o][s],h=d.options.offset,p=d.triggerPoint,_=0,w=null==p;d.element!==d.element.window&&(_=d.adapter.offset()[a.offsetProp]),"function"==typeof h?h=h.apply(d):"string"==typeof h&&(h=parseFloat(h),d.options.offset.indexOf("%")>-1&&(h=Math.ceil(a.contextDimension*h/100))),l=a.contextScroll-a.contextOffset,d.triggerPoint=Math.floor(_+l-h),c=p<a.oldScroll,u=d.triggerPoint>=a.oldScroll,f=!c&&!u,!w&&(c&&u)?(d.queueTrigger(a.backward),i[d.group.id]=d.group):(!w&&f||w&&a.oldScroll>=d.triggerPoint)&&(d.queueTrigger(a.forward),i[d.group.id]=d.group)}}return r.requestAnimationFrame((function(){for(var e in i)i[e].flushTriggers()})),this},o.findOrCreateByElement=function(e){return o.findByElement(e)||new o(e)},o.refreshAll=function(){for(var e in n)n[e].refresh()},o.findByElement=function(e){return n[e.waypointContextKey]},window.onload=function(){i&&i(),o.refreshAll()},r.requestAnimationFrame=function(t){(window.requestAnimationFrame||window.mozRequestAnimationFrame||window.webkitRequestAnimationFrame||e).call(window,t)},r.Context=o}(),function(){"use strict";function e(e,t){return e.triggerPoint-t.triggerPoint}function t(e,t){return t.triggerPoint-e.triggerPoint}var n={vertical:{},horizontal:{}},r=window.Waypoint;function i(e){this.name=e.name,this.axis=e.axis,this.id=this.name+"-"+this.axis,this.waypoints=[],this.clearTriggerQueues(),n[this.axis][this.name]=this}i.prototype.add=function(e){this.waypoints.push(e)},i.prototype.clearTriggerQueues=function(){this.triggerQueues={up:[],down:[],left:[],right:[]}},i.prototype.flushTriggers=function(){for(var n in this.triggerQueues){var r=this.triggerQueues[n],i="up"===n||"left"===n;r.sort(i?t:e);for(var o=0,a=r.length;o<a;o+=1){var s=r[o];(s.options.continuous||o===r.length-1)&&s.trigger([n])}}this.clearTriggerQueues()},i.prototype.next=function(t){this.waypoints.sort(e);var n=r.Adapter.inArray(t,this.waypoints);return n===this.waypoints.length-1?null:this.waypoints[n+1]},i.prototype.previous=function(t){this.waypoints.sort(e);var n=r.Adapter.inArray(t,this.waypoints);return n?this.waypoints[n-1]:null},i.prototype.queueTrigger=function(e,t){this.triggerQueues[t].push(e)},i.prototype.remove=function(e){var t=r.Adapter.inArray(e,this.waypoints);t>-1&&this.waypoints.splice(t,1)},i.prototype.first=function(){return this.waypoints[0]},i.prototype.last=function(){return this.waypoints[this.waypoints.length-1]},i.findOrCreate=function(e){return n[e.axis][e.name]||new i(e)},r.Group=i}(),function(){"use strict";var e=window.jQuery,t=window.Waypoint;function n(t){this.$element=e(t)}e.each(["innerHeight","innerWidth","off","offset","on","outerHeight","outerWidth","scrollLeft","scrollTop"],(function(e,t){n.prototype[t]=function(){var e=Array.prototype.slice.call(arguments);return this.$element[t].apply(this.$element,e)}})),e.each(["extend","inArray","isEmptyObject"],(function(t,r){n[r]=e[r]})),t.adapters.push({name:"jquery",Adapter:n}),t.Adapter=n}(),function(){"use strict";var e=window.Waypoint;function t(t){return function(){var n=[],r=arguments[0];return t.isFunction(arguments[0])&&((r=t.extend({},arguments[1])).handler=arguments[0]),this.each((function(){var i=t.extend({},r,{element:this});"string"==typeof i.context&&(i.context=t(this).closest(i.context)[0]),n.push(new e(i))})),n}}window.jQuery&&(window.jQuery.fn.waypoint=t(window.jQuery)),window.Zepto&&(window.Zepto.fn.waypoint=t(window.Zepto))}()},15861:function(e,t,n){"use strict";function r(e,t,n,r,i,o,a){try{var s=e[o](a),l=s.value}catch(e){return void n(e)}s.done?t(l):Promise.resolve(l).then(r,i)}function i(e){return function(){var t=this,n=arguments;return new Promise((function(i,o){var a=e.apply(t,n);function s(e){r(a,i,o,s,l,"next",e)}function l(e){r(a,i,o,s,l,"throw",e)}s(void 0)}))}}n.d(t,{Z:function(){return i}})},31955:function(){"use strict";function e(e){for(var t=1;t<arguments.length;t++){var n=arguments[t];for(var r in n)e[r]=n[r]}return e}(function t(n,r){function i(t,i,o){if("undefined"!=typeof document){"number"==typeof(o=e({},r,o)).expires&&(o.expires=new Date(Date.now()+864e5*o.expires)),o.expires&&(o.expires=o.expires.toUTCString()),t=encodeURIComponent(t).replace(/%(2[346B]|5E|60|7C)/g,decodeURIComponent).replace(/[()]/g,escape);var a="";for(var s in o)o[s]&&(a+="; "+s,!0!==o[s]&&(a+="="+o[s].split(";")[0]));return document.cookie=t+"="+n.write(i,t)+a}}return Object.create({set:i,get:function(e){if("undefined"!=typeof document&&(!arguments.length||e)){for(var t=document.cookie?document.cookie.split("; "):[],r={},i=0;i<t.length;i++){var o=t[i].split("="),a=o.slice(1).join("=");try{var s=decodeURIComponent(o[0]);if(r[s]=n.read(a,s),e===s)break}catch(e){}}return e?r[e]:r}},remove:function(t,n){i(t,"",e({},n,{expires:-1}))},withAttributes:function(n){return t(this.converter,e({},this.attributes,n))},withConverter:function(n){return t(e({},this.converter,n),this.attributes)}},{attributes:{value:Object.freeze(r)},converter:{value:Object.freeze(n)}})})({read:function(e){return'"'===e[0]&&(e=e.slice(1,-1)),e.replace(/(%[\dA-F]{2})+/gi,decodeURIComponent)},write:function(e){return encodeURIComponent(e).replace(/%(2[346BF]|3[AC-F]|40|5[BDE]|60|7[BCD])/g,decodeURIComponent)}},{path:"/"})}},__webpack_module_cache__={},inProgress,dataWebpackPrefix,loadStylesheet,installedCssChunks;function __webpack_require__(e){var t=__webpack_module_cache__[e];if(void 0!==t)return t.exports;var n=__webpack_module_cache__[e]={exports:{}};return __webpack_modules__[e](n,n.exports,__webpack_require__),n.exports}__webpack_require__.m=__webpack_modules__,__webpack_require__.n=function(e){var t=e&&e.__esModule?function(){return e.default}:function(){return e};return __webpack_require__.d(t,{a:t}),t},__webpack_require__.d=function(e,t){for(var n in t)__webpack_require__.o(t,n)&&!__webpack_require__.o(e,n)&&Object.defineProperty(e,n,{enumerable:!0,get:t[n]})},__webpack_require__.f={},__webpack_require__.e=function(e){return Promise.all(Object.keys(__webpack_require__.f).reduce((function(t,n){return __webpack_require__.f[n](e,t),t}),[]))},__webpack_require__.u=function(e){return"js/highlightjs.08163204b82028c51462.js"},__webpack_require__.miniCssF=function(e){return"css/highlightjs.ae43064ab38a65a04d81.css"},__webpack_require__.g=function(){if("object"==typeof globalThis)return globalThis;try{return this||new Function("return this")()}catch(e){if("object"==typeof window)return window}}(),__webpack_require__.o=function(e,t){return Object.prototype.hasOwnProperty.call(e,t)},inProgress={},dataWebpackPrefix="swh.[name]:",__webpack_require__.l=function(e,t,n,r){if(inProgress[e])inProgress[e].push(t);else{var i,o;if(void 0!==n)for(var a=document.getElementsByTagName("script"),s=0;s<a.length;s++){var l=a[s];if(l.getAttribute("src")==e||l.getAttribute("data-webpack")==dataWebpackPrefix+n){i=l;break}}i||(o=!0,(i=document.createElement("script")).charset="utf-8",i.timeout=120,__webpack_require__.nc&&i.setAttribute("nonce",__webpack_require__.nc),i.setAttribute("data-webpack",dataWebpackPrefix+n),i.src=e),inProgress[e]=[t];var c=function(t,n){i.onerror=i.onload=null,clearTimeout(u);var r=inProgress[e];if(delete inProgress[e],i.parentNode&&i.parentNode.removeChild(i),r&&r.forEach((function(e){return e(n)})),t)return t(n)},u=setTimeout(c.bind(null,void 0,{type:"timeout",target:i}),12e4);i.onerror=c.bind(null,i.onerror),i.onload=c.bind(null,i.onload),o&&document.head.appendChild(i)}},__webpack_require__.r=function(e){"undefined"!=typeof Symbol&&Symbol.toStringTag&&Object.defineProperty(e,Symbol.toStringTag,{value:"Module"}),Object.defineProperty(e,"__esModule",{value:!0})},__webpack_require__.p="/static/",loadStylesheet=function(e){return new Promise((function(t,n){var r=__webpack_require__.miniCssF(e),i=__webpack_require__.p+r;if(function(e,t){for(var n=document.getElementsByTagName("link"),r=0;r<n.length;r++){var i=(a=n[r]).getAttribute("data-href")||a.getAttribute("href");if("stylesheet"===a.rel&&(i===e||i===t))return a}var o=document.getElementsByTagName("style");for(r=0;r<o.length;r++){var a;if((i=(a=o[r]).getAttribute("data-href"))===e||i===t)return a}}(r,i))return t();!function(e,t,n,r){var i=document.createElement("link");i.rel="stylesheet",i.type="text/css",i.onerror=i.onload=function(o){if(i.onerror=i.onload=null,"load"===o.type)n();else{var a=o&&("load"===o.type?"missing":o.type),s=o&&o.target&&o.target.href||t,l=new Error("Loading CSS chunk "+e+" failed.\n("+s+")");l.code="CSS_CHUNK_LOAD_FAILED",l.type=a,l.request=s,i.parentNode.removeChild(i),r(l)}},i.href=t,document.head.appendChild(i)}(e,i,t,n)}))},installedCssChunks={679:0},__webpack_require__.f.miniCss=function(e,t){installedCssChunks[e]?t.push(installedCssChunks[e]):0!==installedCssChunks[e]&&{399:1}[e]&&t.push(installedCssChunks[e]=loadStylesheet(e).then((function(){installedCssChunks[e]=0}),(function(t){throw delete installedCssChunks[e],t})))},function(){var e={679:0};__webpack_require__.f.j=function(t,n){var r=__webpack_require__.o(e,t)?e[t]:void 0;if(0!==r)if(r)n.push(r[2]);else{var i=new Promise((function(n,i){r=e[t]=[n,i]}));n.push(r[2]=i);var o=__webpack_require__.p+__webpack_require__.u(t),a=new Error;__webpack_require__.l(o,(function(n){if(__webpack_require__.o(e,t)&&(0!==(r=e[t])&&(e[t]=void 0),r)){var i=n&&("load"===n.type?"missing":n.type),o=n&&n.target&&n.target.src;a.message="Loading chunk "+t+" failed.\n("+i+": "+o+")",a.name="ChunkLoadError",a.type=i,a.request=o,r[1](a)}}),"chunk-"+t,t)}};var t=function(t,n){var r,i,o=n[0],a=n[1],s=n[2],l=0;if(o.some((function(t){return 0!==e[t]}))){for(r in a)__webpack_require__.o(a,r)&&(__webpack_require__.m[r]=a[r]);if(s)s(__webpack_require__)}for(t&&t(n);l<o.length;l++)i=o[l],__webpack_require__.o(e,i)&&e[i]&&e[i][0](),e[o[l]]=0},n=self.webpackChunkswh_name_=self.webpackChunkswh_name_||[];n.forEach(t.bind(null,0)),n.push=t.bind(null,n.push.bind(n))}();var __webpack_exports__={};return function(){"use strict";__webpack_require__.r(__webpack_exports__),__webpack_require__.d(__webpack_exports__,{computeAllDiffs:function(){return e.St},computeDiff:function(){return e.D_},formatDiffLineNumbers:function(){return e.OU},fragmentToSelectedDiffLines:function(){return e.EV},initRevisionDiff:function(){return e.qo},parseDiffLineNumbers:function(){return e.sr},selectedDiffLinesToFragment:function(){return e.S0},showSplitDiff:function(){return e.Mo},showUnifiedDiff:function(){return e.n2},initRevisionsLog:function(){return t.o},revsOrderingTypeClicked:function(){return t.i}});var e=__webpack_require__(31463),t=__webpack_require__(54087)}(),__webpack_exports__}()}));
//# sourceMappingURL=revision.e17cd43c375d7191f9da.js.map