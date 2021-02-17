/*! For license information please see revision.94a002d24a26693a274d.js.LICENSE.txt */
!function(e,t){"object"==typeof exports&&"object"==typeof module?module.exports=t():"function"==typeof define&&define.amd?define([],t):"object"==typeof exports?exports.swh=t():(e.swh=e.swh||{},e.swh.revision=t())}(self,(function(){return function(){var __webpack_modules__={48926:function(e){function t(e,t,n,i,r,o,a){try{var s=e[o](a),l=s.value}catch(e){return void n(e)}s.done?t(l):Promise.resolve(l).then(i,r)}e.exports=function(e){return function(){var n=this,i=arguments;return new Promise((function(r,o){var a=e.apply(n,i);function s(e){t(a,r,o,s,l,"next",e)}function l(e){t(a,r,o,s,l,"throw",e)}s(void 0)}))}}},78279:function(e,t,n){var i=function(){return this||"object"==typeof self&&self}()||Function("return this")(),r=i.regeneratorRuntime&&Object.getOwnPropertyNames(i).indexOf("regeneratorRuntime")>=0,o=r&&i.regeneratorRuntime;if(i.regeneratorRuntime=void 0,e.exports=n(61553),r)i.regeneratorRuntime=o;else try{delete i.regeneratorRuntime}catch(e){i.regeneratorRuntime=void 0}},61553:function(e){!function(t){"use strict";var n,i=Object.prototype,r=i.hasOwnProperty,o="function"==typeof Symbol?Symbol:{},a=o.iterator||"@@iterator",s=o.asyncIterator||"@@asyncIterator",l=o.toStringTag||"@@toStringTag",c=t.regeneratorRuntime;if(c)e.exports=c;else{(c=t.regeneratorRuntime=e.exports).wrap=v;var u="suspendedStart",f="suspendedYield",d="executing",h="completed",p={},_={};_[a]=function(){return this};var w=Object.getPrototypeOf,g=w&&w(w(E([])));g&&g!==i&&r.call(g,a)&&(_=g);var m=k.prototype=b.prototype=Object.create(_);x.prototype=m.constructor=k,k.constructor=x,k[l]=x.displayName="GeneratorFunction",c.isGeneratorFunction=function(e){var t="function"==typeof e&&e.constructor;return!!t&&(t===x||"GeneratorFunction"===(t.displayName||t.name))},c.mark=function(e){return Object.setPrototypeOf?Object.setPrototypeOf(e,k):(e.__proto__=k,l in e||(e[l]="GeneratorFunction")),e.prototype=Object.create(m),e},c.awrap=function(e){return{__await:e}},$(S.prototype),S.prototype[s]=function(){return this},c.AsyncIterator=S,c.async=function(e,t,n,i){var r=new S(v(e,t,n,i));return c.isGeneratorFunction(t)?r:r.next().then((function(e){return e.done?e.value:r.next()}))},$(m),m[l]="Generator",m[a]=function(){return this},m.toString=function(){return"[object Generator]"},c.keys=function(e){var t=[];for(var n in e)t.push(n);return t.reverse(),function n(){for(;t.length;){var i=t.pop();if(i in e)return n.value=i,n.done=!1,n}return n.done=!0,n}},c.values=E,L.prototype={constructor:L,reset:function(e){if(this.prev=0,this.next=0,this.sent=this._sent=n,this.done=!1,this.delegate=null,this.method="next",this.arg=n,this.tryEntries.forEach(T),!e)for(var t in this)"t"===t.charAt(0)&&r.call(this,t)&&!isNaN(+t.slice(1))&&(this[t]=n)},stop:function(){this.done=!0;var e=this.tryEntries[0].completion;if("throw"===e.type)throw e.arg;return this.rval},dispatchException:function(e){if(this.done)throw e;var t=this;function i(i,r){return s.type="throw",s.arg=e,t.next=i,r&&(t.method="next",t.arg=n),!!r}for(var o=this.tryEntries.length-1;o>=0;--o){var a=this.tryEntries[o],s=a.completion;if("root"===a.tryLoc)return i("end");if(a.tryLoc<=this.prev){var l=r.call(a,"catchLoc"),c=r.call(a,"finallyLoc");if(l&&c){if(this.prev<a.catchLoc)return i(a.catchLoc,!0);if(this.prev<a.finallyLoc)return i(a.finallyLoc)}else if(l){if(this.prev<a.catchLoc)return i(a.catchLoc,!0)}else{if(!c)throw new Error("try statement without catch or finally");if(this.prev<a.finallyLoc)return i(a.finallyLoc)}}}},abrupt:function(e,t){for(var n=this.tryEntries.length-1;n>=0;--n){var i=this.tryEntries[n];if(i.tryLoc<=this.prev&&r.call(i,"finallyLoc")&&this.prev<i.finallyLoc){var o=i;break}}o&&("break"===e||"continue"===e)&&o.tryLoc<=t&&t<=o.finallyLoc&&(o=null);var a=o?o.completion:{};return a.type=e,a.arg=t,o?(this.method="next",this.next=o.finallyLoc,p):this.complete(a)},complete:function(e,t){if("throw"===e.type)throw e.arg;return"break"===e.type||"continue"===e.type?this.next=e.arg:"return"===e.type?(this.rval=this.arg=e.arg,this.method="return",this.next="end"):"normal"===e.type&&t&&(this.next=t),p},finish:function(e){for(var t=this.tryEntries.length-1;t>=0;--t){var n=this.tryEntries[t];if(n.finallyLoc===e)return this.complete(n.completion,n.afterLoc),T(n),p}},catch:function(e){for(var t=this.tryEntries.length-1;t>=0;--t){var n=this.tryEntries[t];if(n.tryLoc===e){var i=n.completion;if("throw"===i.type){var r=i.arg;T(n)}return r}}throw new Error("illegal catch attempt")},delegateYield:function(e,t,i){return this.delegate={iterator:E(e),resultName:t,nextLoc:i},"next"===this.method&&(this.arg=n),p}}}function v(e,t,n,i){var r=t&&t.prototype instanceof b?t:b,o=Object.create(r.prototype),a=new L(i||[]);return o._invoke=function(e,t,n){var i=u;return function(r,o){if(i===d)throw new Error("Generator is already running");if(i===h){if("throw"===r)throw o;return q()}for(n.method=r,n.arg=o;;){var a=n.delegate;if(a){var s=j(a,n);if(s){if(s===p)continue;return s}}if("next"===n.method)n.sent=n._sent=n.arg;else if("throw"===n.method){if(i===u)throw i=h,n.arg;n.dispatchException(n.arg)}else"return"===n.method&&n.abrupt("return",n.arg);i=d;var l=y(e,t,n);if("normal"===l.type){if(i=n.done?h:f,l.arg===p)continue;return{value:l.arg,done:n.done}}"throw"===l.type&&(i=h,n.method="throw",n.arg=l.arg)}}}(e,n,a),o}function y(e,t,n){try{return{type:"normal",arg:e.call(t,n)}}catch(e){return{type:"throw",arg:e}}}function b(){}function x(){}function k(){}function $(e){["next","throw","return"].forEach((function(t){e[t]=function(e){return this._invoke(t,e)}}))}function S(e){function t(n,i,o,a){var s=y(e[n],e,i);if("throw"!==s.type){var l=s.arg,c=l.value;return c&&"object"==typeof c&&r.call(c,"__await")?Promise.resolve(c.__await).then((function(e){t("next",e,o,a)}),(function(e){t("throw",e,o,a)})):Promise.resolve(c).then((function(e){l.value=e,o(l)}),(function(e){return t("throw",e,o,a)}))}a(s.arg)}var n;this._invoke=function(e,i){function r(){return new Promise((function(n,r){t(e,i,n,r)}))}return n=n?n.then(r,r):r()}}function j(e,t){var i=e.iterator[t.method];if(i===n){if(t.delegate=null,"throw"===t.method){if(e.iterator.return&&(t.method="return",t.arg=n,j(e,t),"throw"===t.method))return p;t.method="throw",t.arg=new TypeError("The iterator does not provide a 'throw' method")}return p}var r=y(i,e.iterator,t.arg);if("throw"===r.type)return t.method="throw",t.arg=r.arg,t.delegate=null,p;var o=r.arg;return o?o.done?(t[e.resultName]=o.value,t.next=e.nextLoc,"return"!==t.method&&(t.method="next",t.arg=n),t.delegate=null,p):o:(t.method="throw",t.arg=new TypeError("iterator result is not an object"),t.delegate=null,p)}function C(e){var t={tryLoc:e[0]};1 in e&&(t.catchLoc=e[1]),2 in e&&(t.finallyLoc=e[2],t.afterLoc=e[3]),this.tryEntries.push(t)}function T(e){var t=e.completion||{};t.type="normal",delete t.arg,e.completion=t}function L(e){this.tryEntries=[{tryLoc:"root"}],e.forEach(C,this),this.reset(!0)}function E(e){if(e){var t=e[a];if(t)return t.call(e);if("function"==typeof e.next)return e;if(!isNaN(e.length)){var i=-1,o=function t(){for(;++i<e.length;)if(r.call(e,i))return t.value=e[i],t.done=!1,t;return t.value=n,t.done=!0,t};return o.next=o}}return{next:q}}function q(){return{value:n,done:!0}}}(function(){return this||"object"==typeof self&&self}()||Function("return this")())},87757:function(e,t,n){e.exports=n(78279)},79700:function(e,t,n){"use strict";n.d(t,{OU:function(){return C},sr:function(){return E},S0:function(){return q},EV:function(){return A},n2:function(){return D},Mo:function(){return R},D_:function(){return M},St:function(){return B},qo:function(){return Q}});var i,r=n(87757),o=n.n(r),a=n(48926),s=n.n(a),l=(n(43511),n(91386)),c=n(45149),u=n(97680),f=n.n(u),d=null,h=0,p=0,_=0,w=0,g={},m={},v=null,y=null,b={},x=null,k="#swh-revision-changes",S="Files";function j(e){var t=$(e).offset().top,n=t+$(e).outerHeight(),i=$(window).scrollTop(),r=i+$(window).height();return n>i&&t<r}function C(e,t,n){for(var i=b[e],r=L(t),o=L(n),a="",s=0;s<i-r.length;++s)a+=" ";a+=r,a+="  ";for(var l=0;l<i-o.length;++l)a+=" ";return a+=o}function T(e){return e?parseInt(e):0}function L(e){return e?e.toString():""}function E(e,t,n){var i;if(t||n){var r=T(e.trim());t?i=[r,0]:n&&(i=[0,r])}else(i=e.replace(/[ ]+/g," ").split(" ")).length>2&&i.shift(),i=i.map((function(e){return T(e)}));return i}function q(e,t,n){var i="";return i+="F"+(e[0]||0),i+="T"+(e[1]||0),i+="-F"+(t[0]||0),i+="T"+(t[1]||0),i+=n?"-unified":"-split"}function A(e){var t=/F([0-9]+)T([0-9]+)-F([0-9]+)T([0-9]+)-([a-z]+)/.exec(e);return 6===t.length?{startLines:[parseInt(t[1]),parseInt(t[2])],endLines:[parseInt(t[3]),parseInt(t[4])],unified:"unified"===t[5]}:null}function P(e,t){var n=$("#"+e+' .hljs-ln-line[data-line-number="'+t+'"]'),i=$("#"+e+' .hljs-ln-numbers[data-line-number="'+t+'"]');return i.css("color","black"),i.css("font-weight","bold"),n.css("background-color","#fdf3da"),n.css("mix-blend-mode","multiply"),n}function F(e){void 0===e&&(e=!0),e&&(x=null,v=null,y=null),$(".hljs-ln-line[data-line-number]").css("background-color","initial"),$(".hljs-ln-line[data-line-number]").css("mix-blend-mode","initial"),$(".hljs-ln-numbers[data-line-number]").css("color","#aaa"),$(".hljs-ln-numbers[data-line-number]").css("font-weight","initial"),"Changes"===S&&window.location.hash!==k&&window.history.replaceState("",document.title,window.location.pathname+window.location.search+k)}function O(e,t,n,i){var r;if(i){var o=C(e,t[0],t[1]),a=C(e,n[0],n[1]),s=$("#"+e+' .hljs-ln-line[data-line-number="'+o+'"]'),l=$("#"+e+' .hljs-ln-line[data-line-number="'+a+'"]');if($(l).position().top<$(s).position().top){var c=[a,o];o=c[0],a=c[1],r=l}else r=s;for(var u=P(e,o),f=$(u).closest("tr"),d=$(f).children(".hljs-ln-line").data("line-number").toString();d!==a;)d.trim()&&P(e,d),f=$(f).next(),d=$(f).children(".hljs-ln-line").data("line-number").toString();P(e,a)}else if(t[0]&&n[0]){for(var h=Math.min(t[0],n[0]),p=Math.max(t[0],n[0]),_=h;_<=p;++_)P(e+"-from",_);r=$("#"+e+'-from .hljs-ln-line[data-line-number="'+h+'"]')}else if(t[1]&&n[1]){for(var w=Math.min(t[1],n[1]),g=Math.max(t[1],n[1]),m=w;m<=g;++m)P(e+"-to",m);r=$("#"+e+'-to .hljs-ln-line[data-line-number="'+w+'"]')}else{var v,y;t[0]&&n[1]?(v=t[0],y=n[1]):(v=n[0],y=t[1]);var b=$("#"+e+'-from .hljs-ln-line[data-line-number="'+v+'"]'),x=$("#"+e+'-to .hljs-ln-line[data-line-number="'+y+'"]'),k=$(b).position().top<$(x).position().top;r=k?b:x;for(var S=$("#"+e+"-from tr").first(),j=$(S).children(".hljs-ln-line").data("line-number"),T=$("#"+e+"-to tr").first(),L=$(T).children(".hljs-ln-line").data("line-number"),E=!1;k&&j===v?E=!0:k||L!==y||(E=!0),E&&j&&P(e+"-from",j),E&&L&&P(e+"-to",L),!(k&&L===y||!k&&j===v);)S=$(S).next(),j=$(S).children(".hljs-ln-line").data("line-number"),T=$(T).next(),L=$(T).children(".hljs-ln-line").data("line-number")}var A=q(t,n,i);return window.location.hash="diff_"+e+"+"+A,r}function D(e){$("#"+e+"-split-diff").css("display","none"),$("#"+e+"-unified-diff").css("display","block")}function R(e){$("#"+e+"-unified-diff").css("display","none"),$("#"+e+"-split-diff").css("display","block")}function M(e,t){function n(e,t){$(e).attr("data-line-number",t||""),$(e).children().attr("data-line-number",t||""),$(e).siblings().attr("data-line-number",t||"")}-1===e.indexOf("force=true")&&g.hasOwnProperty(t)||(g[t]=!0,$("#"+t+"-loading").css("visibility","visible"),$("#"+t+"-loading").css("display","block"),$("#"+t+"-highlightjs").css("display","none"),fetch(e).then((function(e){return e.json()})).then((function(r){if(++p===d.length&&$("#swh-compute-all-diffs").addClass("active"),0===r.diff_str.indexOf("Large diff"))$("#"+t)[0].innerHTML=r.diff_str+'<br/><button class="btn btn-default btn-sm" type="button"\n           onclick="swh.revision.computeDiff(\''+e+"&force=true', '"+t+"')\">Request diff</button>",N(t);else if(0!==r.diff_str.indexOf("@@"))$("#"+t).text(r.diff_str),N(t);else{$("."+t).removeClass("nohighlight"),$("."+t).addClass(r.language),$("#"+t).text(r.diff_str),$("#"+t).each((function(e,t){hljs.highlightBlock(t),hljs.lineNumbersBlockSync(t)}));var o="",a="",s=[],l=[],c=[],u=0,f="",h="",g=0;if($("#"+t+" .hljs-ln-numbers").each((function(e,t){var n=t.nextSibling.innerText,i=function(e){var t,n;if(e.startsWith("@@")){var i=new RegExp(/^@@ -(\d+),(\d+) \+(\d+),(\d+) @@$/gm),r=new RegExp(/^@@ -(\d+) \+(\d+),(\d+) @@$/gm),o=new RegExp(/^@@ -(\d+),(\d+) \+(\d+) @@$/gm),a=new RegExp(/^@@ -(\d+) \+(\d+) @@$/gm),s=i.exec(e),l=r.exec(e),c=o.exec(e),u=a.exec(e);s?(t=parseInt(s[1])-1,n=parseInt(s[3])-1):l?(t=parseInt(l[1])-1,n=parseInt(l[2])-1):c?(t=parseInt(c[1])-1,n=parseInt(c[3])-1):u&&(t=parseInt(u[1])-1,n=parseInt(u[2])-1)}return void 0!==t?[t,n]:null}(n),r="",d="";if(i)o=i[0],a=i[1],g=0,f+=n+"\n",h+=n+"\n",l.push(""),c.push("");else if(n.length>0&&"-"===n[0])r=(o+=1).toString(),l.push(r),++w,f+=n+"\n",++g;else if(n.length>0&&"+"===n[0])d=(a+=1).toString(),c.push(d),++_,h+=n+"\n",--g;else{a+=1,r=(o+=1).toString(),d=a.toString();for(var p=0;p<Math.abs(g);++p)g>0?(h+="\n",c.push("")):(f+="\n",l.push(""));g=0,f+=n+"\n",h+=n+"\n",c.push(d),l.push(r)}o||(r=""),a||(d=""),s[e]=[r,d],u=Math.max(u,r.length),u=Math.max(u,d.length)})),b[t]=u,$("#"+t+"-from").text(f),$("#"+t+"-to").text(h),$("#"+t+"-from, #"+t+"-to").each((function(e,t){hljs.highlightBlock(t),hljs.lineNumbersBlockSync(t)})),$("."+t+" .hljs-ln-numbers").each((function(e,t){var n=t.nextSibling.innerText;if(n.startsWith("@@")){$(t).parent().addClass("swh-diff-lines-info");var i=$(t).parent().find(".hljs-ln-code .hljs-ln-line").text();$(t).parent().find(".hljs-ln-code .hljs-ln-line").children().remove(),$(t).parent().find(".hljs-ln-code .hljs-ln-line").text(""),$(t).parent().find(".hljs-ln-code .hljs-ln-line").append('<span class="hljs-meta">'+i+"</span>")}else n.length>0&&"-"===n[0]?$(t).parent().addClass("swh-diff-removed-line"):n.length>0&&"+"===n[0]&&$(t).parent().addClass("swh-diff-added-line")})),$("#"+t+" .hljs-ln-numbers").each((function(e,i){n(i,C(t,s[e][0],s[e][1]))})),$("#"+t+"-from .hljs-ln-numbers").each((function(e,t){n(t,l[e])})),$("#"+t+"-to .hljs-ln-numbers").each((function(e,t){n(t,c[e])})),$("."+t+" .hljs-ln-code").each((function(e,t){if(t.firstChild){if("#text"!==t.firstChild.nodeName){var n=t.firstChild.innerHTML;if("-"===n[0]||"+"===n[0]){t.firstChild.innerHTML=n.substr(1);var i=document.createTextNode(n[0]);$(t).prepend(i)}}$(t).contents().filter((function(e,t){return 3===t.nodeType})).each((function(e,n){var i="[swh-no-nl-marker]";-1!==n.textContent.indexOf(i)&&(n.textContent=n.textContent.replace(i,""),$(t).append($('<span class="no-nl-marker" title="No newline at end of file"><svg aria-hidden="true" height="16" version="1.1" viewBox="0 0 16 16" width="16"><path fill-rule="evenodd" d="M16 5v3c0 .55-.45 1-1 1h-3v2L9 8l3-3v2h2V5h2zM8 8c0 2.2-1.8 4-4 4s-4-1.8-4-4 1.8-4 4-4 4 1.8 4 4zM1.5 9.66L5.66 5.5C5.18 5.19 4.61 5 4 5 2.34 5 1 6.34 1 8c0 .61.19 1.17.5 1.66zM7 8c0-.61-.19-1.17-.5-1.66L2.34 10.5c.48.31 1.05.5 1.66.5 1.66 0 3-1.34 3-3z"></path></svg></span>')))}))}})),0!==r.diff_str.indexOf("Diffs are not generated for non textual content")&&$("#diff_"+t+" .diff-styles").css("visibility","visible"),N(t),i&&-1!==i.diffPanelId.indexOf(t)){i.unified||R(t);var m=O(t,i.startLines,i.endLines,i.unified);$("html, body").animate({scrollTop:m.offset().top-50},{duration:500})}}})))}function N(e){$("#"+e+"-loading").css("display","none"),$("#"+e+"-highlightjs").css("display","block"),$("#swh-revision-lines-added").text(_+" additions"),$("#swh-revision-lines-deleted").text(w+" deletions"),$("#swh-nb-diffs-computed").text(p),Waypoint.refreshAll()}function W(){$(".swh-file-diff-panel").each((function(e,t){if(j(t)){var n=t.id.replace("diff_","");M(m[n],n)}}))}function H(e){var t=e.path;return"rename"===e.type&&(t=e.from_path+" &rarr; "+e.to_path),f()({diffData:e,diffPanelTitle:t,swhSpinnerSrc:l.XC})}function z(){for(var e=0;e<d.length;++e){var t=d[e];$("#diff_"+t.id).waypoint({handler:function(){if(j(this.element)){var e=this.element.id.replace("diff_","");M(m[e],e),this.destroy()}},offset:"100%"}),$("#diff_"+t.id).waypoint({handler:function(){if(j(this.element)){var e=this.element.id.replace("diff_","");M(m[e],e),this.destroy()}},offset:function(){return-$(this.element).height()}})}Waypoint.refreshAll()}function I(e,t){void 0===t&&(t=!0),Waypoint.disableAll(),$("html, body").animate({scrollTop:$(e).offset().top},{duration:500,complete:function(){t&&(window.location.hash=e),Waypoint.enableAll(),W()}})}function B(e){for(var t in $(e.currentTarget).addClass("active"),m)m.hasOwnProperty(t)&&M(m[t],t);e.stopPropagation()}function Q(e,t){return G.apply(this,arguments)}function G(){return(G=s()(o().mark((function e(t,r){return o().wrap((function(e){for(;;)switch(e.prev=e.next){case 0:return e.next=2,n.e(399).then(n.bind(n,45828));case 2:$(document).on("shown.bs.tab",'a[data-toggle="tab"]',(function(e){if("Changes"===(S=e.currentTarget.text.trim())){if(window.location.hash=k,$("#readme-panel").css("display","none"),d)return;fetch(r).then((function(e){return e.json()})).then((function(e){d=e.changes;var t=(h=e.total_nb_changes)+" changed file";1!==h&&(t+="s"),$("#swh-revision-changed-files").text(t),$("#swh-total-nb-diffs").text(d.length),$("#swh-revision-changes-list pre")[0].innerHTML=e.changes_msg,$("#swh-revision-changes-loading").css("display","none"),$("#swh-revision-changes-list pre").css("display","block"),$("#swh-compute-all-diffs").css("visibility","visible"),$("#swh-revision-changes-list").removeClass("in"),h>d.length&&($("#swh-too-large-revision-diff").css("display","block"),$("#swh-nb-loaded-diffs").text(d.length));for(var n=0;n<d.length;++n){var r=d[n];m[r.id]=r.diff_url,$("#swh-revision-diffs").append(H(r))}z(),W(),i&&I(i.diffPanelId,!1)}))}else"Files"===S&&((0,c.L3)(),$("#readme-panel").css("display","block"))})),$(document).ready((function(){t.length>0?$("#swh-revision-message").addClass("in"):$("#swh-collapse-revision-message").attr("data-toggle",""),$('#swh-revision-changes-list a[href^="#"], #back-to-top a[href^="#"]').click((function(e){return I($.attr(e.currentTarget,"href")),!1})),$("body").click((function(e){if("Changes"===S)if(e.target.classList.contains("hljs-ln-n")){var t=$(e.target).closest("code").prop("id"),n=-1!==t.indexOf("-from"),i=-1!==t.indexOf("-to"),r=$(e.target).data("line-number").toString(),o=t.replace("-from","").replace("-to","");e.shiftKey&&o===x&&r.trim()||(F(),x=o),o===x&&r.trim()&&(e.shiftKey?v&&(F(!1),y=E(r,n,i),O(o,v,y,!n&&!i)):O(o,v=E(r,n,i),v,!n&&!i))}else F()}));var e=window.location.hash;if(e){var n=e.split("+");2===n.length&&(i=A(n[1]))&&(i.diffPanelId=n[0],$('.nav-tabs a[href="#swh-revision-changes"]').tab("show")),e===k&&$('.nav-tabs a[href="#swh-revision-changes"]').tab("show")}}));case 4:case"end":return e.stop()}}),e)})))).apply(this,arguments)}},7416:function(e,t,n){"use strict";function i(e){var t=new URLSearchParams(window.location.search);$(e.target).val()?t.set("revs_ordering",$(e.target).val()):t.has("revs_ordering")&&t.delete("revs_ordering"),window.location.search=t.toString()}function r(){$(document).ready((function(){var e=new URLSearchParams(window.location.search).get("revs_ordering");e&&$(':input[value="'+e+'"]').prop("checked",!0)}))}n.d(t,{i:function(){return i},o:function(){return r}})},91386:function(e,t,n){"use strict";n.d(t,{XC:function(){return i}});var i=(0,n(45149).TT)("img/swh-spinner.gif")},45149:function(e,t,n){"use strict";function i(e){return"/static/"+e}function r(){history.replaceState("",document.title,window.location.pathname+window.location.search)}n.d(t,{TT:function(){return i},L3:function(){return r}})},97680:function(module){module.exports=function anonymous(locals,escapeFn,include,rethrow){escapeFn=escapeFn||function(e){return null==e?"":String(e).replace(_MATCH_HTML,encode_char)};var _ENCODE_HTML_RULES={"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&#34;","'":"&#39;"},_MATCH_HTML=/[&<>'"]/g;function encode_char(e){return _ENCODE_HTML_RULES[e]||e}var __output="";function __append(e){null!=e&&(__output+=e)}with(locals||{})__append('\n<div id="diff_'),__append(escapeFn(diffData.id)),__append('" class="card swh-file-diff-panel">\n  <div class="card-header bg-gray-light border-bottom-0">\n    <a data-toggle="collapse" href="#diff_'),__append(escapeFn(diffData.id)),__append('_content">\n      <div class="float-left swh-title-color">\n        <strong>'),__append(escapeFn(diffPanelTitle)),__append('</strong>\n      </div>\n    </a>\n    <div class="ml-auto float-right">\n      <div class="btn-group btn-group-toggle diff-styles" data-toggle="buttons" style="visibility: hidden;">\n        <label class="btn btn-default btn-sm form-check-label active unified-diff-button" onclick="swh.revision.showUnifiedDiff(\''),__append(escapeFn(diffData.id)),__append('\')">\n          <input type="radio" name="diffs-switch" id="unified" autocomplete="off" checked="checked"> Unified\n        </label>\n        <label class="btn btn-default btn-sm form-check-label split-diff-button" onclick="swh.revision.showSplitDiff(\''),__append(escapeFn(diffData.id)),__append('\')">\n          <input type="radio" name="diffs-switch" id="side-by-side" autocomplete="off"> Side-by-side\n        </label>\n      </div>\n      <a href="'),__append(escapeFn(diffData.content_url)),__append('" class="btn btn-default btn-sm" role="button">View file</a>\n    </div>\n    <div class="clearfix"></div>\n  </div>\n  <div id="diff_'),__append(escapeFn(diffData.id)),__append('_content" class="collapse show">\n    <div class="swh-diff-loading text-center" id="'),__append(escapeFn(diffData.id)),__append('-loading" style="visibility: hidden;">\n      <img src="'),__append(escapeFn(swhSpinnerSrc)),__append('">\n      <p>Loading diff ...</p>\n    </div>\n    <div class="highlightjs swh-content" style="display: none;" id="'),__append(escapeFn(diffData.id)),__append('-highlightjs">\n      <div id="'),__append(escapeFn(diffData.id)),__append('-unified-diff">\n        <pre><code class="'),__append(escapeFn(diffData.id)),__append('" id="'),__append(escapeFn(diffData.id)),__append('"></code></pre>\n      </div>\n      <div style="width: 100%; display: none;" id="'),__append(escapeFn(diffData.id)),__append('-split-diff">\n        <pre class="float-left" style="width: 50%;"><code class="'),__append(escapeFn(diffData.id)),__append('" id="'),__append(escapeFn(diffData.id)),__append('-from"></code></pre>\n        <pre style="width: 50%;"><code class="'),__append(escapeFn(diffData.id)),__append('" id="'),__append(escapeFn(diffData.id)),__append('-to"></code></pre>\n      </div>\n    </div>\n  </div>\n</div>');return __output}},43511:function(){!function(){"use strict";var e=0,t={};function n(i){if(!i)throw new Error("No options passed to Waypoint constructor");if(!i.element)throw new Error("No element option passed to Waypoint constructor");if(!i.handler)throw new Error("No handler option passed to Waypoint constructor");this.key="waypoint-"+e,this.options=n.Adapter.extend({},n.defaults,i),this.element=this.options.element,this.adapter=new n.Adapter(this.element),this.callback=i.handler,this.axis=this.options.horizontal?"horizontal":"vertical",this.enabled=this.options.enabled,this.triggerPoint=null,this.group=n.Group.findOrCreate({name:this.options.group,axis:this.axis}),this.context=n.Context.findOrCreateByElement(this.options.context),n.offsetAliases[this.options.offset]&&(this.options.offset=n.offsetAliases[this.options.offset]),this.group.add(this),this.context.add(this),t[this.key]=this,e+=1}n.prototype.queueTrigger=function(e){this.group.queueTrigger(this,e)},n.prototype.trigger=function(e){this.enabled&&this.callback&&this.callback.apply(this,e)},n.prototype.destroy=function(){this.context.remove(this),this.group.remove(this),delete t[this.key]},n.prototype.disable=function(){return this.enabled=!1,this},n.prototype.enable=function(){return this.context.refresh(),this.enabled=!0,this},n.prototype.next=function(){return this.group.next(this)},n.prototype.previous=function(){return this.group.previous(this)},n.invokeAll=function(e){var n=[];for(var i in t)n.push(t[i]);for(var r=0,o=n.length;r<o;r++)n[r][e]()},n.destroyAll=function(){n.invokeAll("destroy")},n.disableAll=function(){n.invokeAll("disable")},n.enableAll=function(){for(var e in n.Context.refreshAll(),t)t[e].enabled=!0;return this},n.refreshAll=function(){n.Context.refreshAll()},n.viewportHeight=function(){return window.innerHeight||document.documentElement.clientHeight},n.viewportWidth=function(){return document.documentElement.clientWidth},n.adapters=[],n.defaults={context:window,continuous:!0,enabled:!0,group:"default",horizontal:!1,offset:0},n.offsetAliases={"bottom-in-view":function(){return this.context.innerHeight()-this.adapter.outerHeight()},"right-in-view":function(){return this.context.innerWidth()-this.adapter.outerWidth()}},window.Waypoint=n}(),function(){"use strict";function e(e){window.setTimeout(e,1e3/60)}var t=0,n={},i=window.Waypoint,r=window.onload;function o(e){this.element=e,this.Adapter=i.Adapter,this.adapter=new this.Adapter(e),this.key="waypoint-context-"+t,this.didScroll=!1,this.didResize=!1,this.oldScroll={x:this.adapter.scrollLeft(),y:this.adapter.scrollTop()},this.waypoints={vertical:{},horizontal:{}},e.waypointContextKey=this.key,n[e.waypointContextKey]=this,t+=1,i.windowContext||(i.windowContext=!0,i.windowContext=new o(window)),this.createThrottledScrollHandler(),this.createThrottledResizeHandler()}o.prototype.add=function(e){var t=e.options.horizontal?"horizontal":"vertical";this.waypoints[t][e.key]=e,this.refresh()},o.prototype.checkEmpty=function(){var e=this.Adapter.isEmptyObject(this.waypoints.horizontal),t=this.Adapter.isEmptyObject(this.waypoints.vertical),i=this.element==this.element.window;e&&t&&!i&&(this.adapter.off(".waypoints"),delete n[this.key])},o.prototype.createThrottledResizeHandler=function(){var e=this;function t(){e.handleResize(),e.didResize=!1}this.adapter.on("resize.waypoints",(function(){e.didResize||(e.didResize=!0,i.requestAnimationFrame(t))}))},o.prototype.createThrottledScrollHandler=function(){var e=this;function t(){e.handleScroll(),e.didScroll=!1}this.adapter.on("scroll.waypoints",(function(){e.didScroll&&!i.isTouch||(e.didScroll=!0,i.requestAnimationFrame(t))}))},o.prototype.handleResize=function(){i.Context.refreshAll()},o.prototype.handleScroll=function(){var e={},t={horizontal:{newScroll:this.adapter.scrollLeft(),oldScroll:this.oldScroll.x,forward:"right",backward:"left"},vertical:{newScroll:this.adapter.scrollTop(),oldScroll:this.oldScroll.y,forward:"down",backward:"up"}};for(var n in t){var i=t[n],r=i.newScroll>i.oldScroll?i.forward:i.backward;for(var o in this.waypoints[n]){var a=this.waypoints[n][o];if(null!==a.triggerPoint){var s=i.oldScroll<a.triggerPoint,l=i.newScroll>=a.triggerPoint;(s&&l||!s&&!l)&&(a.queueTrigger(r),e[a.group.id]=a.group)}}}for(var c in e)e[c].flushTriggers();this.oldScroll={x:t.horizontal.newScroll,y:t.vertical.newScroll}},o.prototype.innerHeight=function(){return this.element==this.element.window?i.viewportHeight():this.adapter.innerHeight()},o.prototype.remove=function(e){delete this.waypoints[e.axis][e.key],this.checkEmpty()},o.prototype.innerWidth=function(){return this.element==this.element.window?i.viewportWidth():this.adapter.innerWidth()},o.prototype.destroy=function(){var e=[];for(var t in this.waypoints)for(var n in this.waypoints[t])e.push(this.waypoints[t][n]);for(var i=0,r=e.length;i<r;i++)e[i].destroy()},o.prototype.refresh=function(){var e,t=this.element==this.element.window,n=t?void 0:this.adapter.offset(),r={};for(var o in this.handleScroll(),e={horizontal:{contextOffset:t?0:n.left,contextScroll:t?0:this.oldScroll.x,contextDimension:this.innerWidth(),oldScroll:this.oldScroll.x,forward:"right",backward:"left",offsetProp:"left"},vertical:{contextOffset:t?0:n.top,contextScroll:t?0:this.oldScroll.y,contextDimension:this.innerHeight(),oldScroll:this.oldScroll.y,forward:"down",backward:"up",offsetProp:"top"}}){var a=e[o];for(var s in this.waypoints[o]){var l,c,u,f,d=this.waypoints[o][s],h=d.options.offset,p=d.triggerPoint,_=0,w=null==p;d.element!==d.element.window&&(_=d.adapter.offset()[a.offsetProp]),"function"==typeof h?h=h.apply(d):"string"==typeof h&&(h=parseFloat(h),d.options.offset.indexOf("%")>-1&&(h=Math.ceil(a.contextDimension*h/100))),l=a.contextScroll-a.contextOffset,d.triggerPoint=Math.floor(_+l-h),c=p<a.oldScroll,u=d.triggerPoint>=a.oldScroll,f=!c&&!u,!w&&(c&&u)?(d.queueTrigger(a.backward),r[d.group.id]=d.group):(!w&&f||w&&a.oldScroll>=d.triggerPoint)&&(d.queueTrigger(a.forward),r[d.group.id]=d.group)}}return i.requestAnimationFrame((function(){for(var e in r)r[e].flushTriggers()})),this},o.findOrCreateByElement=function(e){return o.findByElement(e)||new o(e)},o.refreshAll=function(){for(var e in n)n[e].refresh()},o.findByElement=function(e){return n[e.waypointContextKey]},window.onload=function(){r&&r(),o.refreshAll()},i.requestAnimationFrame=function(t){(window.requestAnimationFrame||window.mozRequestAnimationFrame||window.webkitRequestAnimationFrame||e).call(window,t)},i.Context=o}(),function(){"use strict";function e(e,t){return e.triggerPoint-t.triggerPoint}function t(e,t){return t.triggerPoint-e.triggerPoint}var n={vertical:{},horizontal:{}},i=window.Waypoint;function r(e){this.name=e.name,this.axis=e.axis,this.id=this.name+"-"+this.axis,this.waypoints=[],this.clearTriggerQueues(),n[this.axis][this.name]=this}r.prototype.add=function(e){this.waypoints.push(e)},r.prototype.clearTriggerQueues=function(){this.triggerQueues={up:[],down:[],left:[],right:[]}},r.prototype.flushTriggers=function(){for(var n in this.triggerQueues){var i=this.triggerQueues[n],r="up"===n||"left"===n;i.sort(r?t:e);for(var o=0,a=i.length;o<a;o+=1){var s=i[o];(s.options.continuous||o===i.length-1)&&s.trigger([n])}}this.clearTriggerQueues()},r.prototype.next=function(t){this.waypoints.sort(e);var n=i.Adapter.inArray(t,this.waypoints);return n===this.waypoints.length-1?null:this.waypoints[n+1]},r.prototype.previous=function(t){this.waypoints.sort(e);var n=i.Adapter.inArray(t,this.waypoints);return n?this.waypoints[n-1]:null},r.prototype.queueTrigger=function(e,t){this.triggerQueues[t].push(e)},r.prototype.remove=function(e){var t=i.Adapter.inArray(e,this.waypoints);t>-1&&this.waypoints.splice(t,1)},r.prototype.first=function(){return this.waypoints[0]},r.prototype.last=function(){return this.waypoints[this.waypoints.length-1]},r.findOrCreate=function(e){return n[e.axis][e.name]||new r(e)},i.Group=r}(),function(){"use strict";var e=window.jQuery,t=window.Waypoint;function n(t){this.$element=e(t)}e.each(["innerHeight","innerWidth","off","offset","on","outerHeight","outerWidth","scrollLeft","scrollTop"],(function(e,t){n.prototype[t]=function(){var e=Array.prototype.slice.call(arguments);return this.$element[t].apply(this.$element,e)}})),e.each(["extend","inArray","isEmptyObject"],(function(t,i){n[i]=e[i]})),t.adapters.push({name:"jquery",Adapter:n}),t.Adapter=n}(),function(){"use strict";var e=window.Waypoint;function t(t){return function(){var n=[],i=arguments[0];return t.isFunction(arguments[0])&&((i=t.extend({},arguments[1])).handler=arguments[0]),this.each((function(){var r=t.extend({},i,{element:this});"string"==typeof r.context&&(r.context=t(this).closest(r.context)[0]),n.push(new e(r))})),n}}window.jQuery&&(window.jQuery.fn.waypoint=t(window.jQuery)),window.Zepto&&(window.Zepto.fn.waypoint=t(window.Zepto))}()}},__webpack_module_cache__={},inProgress,dataWebpackPrefix,loadStylesheet,installedCssChunks;function __webpack_require__(e){if(__webpack_module_cache__[e])return __webpack_module_cache__[e].exports;var t=__webpack_module_cache__[e]={exports:{}};return __webpack_modules__[e](t,t.exports,__webpack_require__),t.exports}__webpack_require__.m=__webpack_modules__,__webpack_require__.n=function(e){var t=e&&e.__esModule?function(){return e.default}:function(){return e};return __webpack_require__.d(t,{a:t}),t},__webpack_require__.d=function(e,t){for(var n in t)__webpack_require__.o(t,n)&&!__webpack_require__.o(e,n)&&Object.defineProperty(e,n,{enumerable:!0,get:t[n]})},__webpack_require__.f={},__webpack_require__.e=function(e){return Promise.all(Object.keys(__webpack_require__.f).reduce((function(t,n){return __webpack_require__.f[n](e,t),t}),[]))},__webpack_require__.u=function(e){return"js/highlightjs.1e0bb235866fc7c30c8f.js"},__webpack_require__.miniCssF=function(e){return"css/highlightjs.7b7705451651153be1c8.css"},__webpack_require__.g=function(){if("object"==typeof globalThis)return globalThis;try{return this||new Function("return this")()}catch(e){if("object"==typeof window)return window}}(),__webpack_require__.o=function(e,t){return Object.prototype.hasOwnProperty.call(e,t)},inProgress={},dataWebpackPrefix="swh.[name]:",__webpack_require__.l=function(e,t,n,i){if(inProgress[e])inProgress[e].push(t);else{var r,o;if(void 0!==n)for(var a=document.getElementsByTagName("script"),s=0;s<a.length;s++){var l=a[s];if(l.getAttribute("src")==e||l.getAttribute("data-webpack")==dataWebpackPrefix+n){r=l;break}}r||(o=!0,(r=document.createElement("script")).charset="utf-8",r.timeout=120,__webpack_require__.nc&&r.setAttribute("nonce",__webpack_require__.nc),r.setAttribute("data-webpack",dataWebpackPrefix+n),r.src=e),inProgress[e]=[t];var c=function(t,n){r.onerror=r.onload=null,clearTimeout(u);var i=inProgress[e];if(delete inProgress[e],r.parentNode&&r.parentNode.removeChild(r),i&&i.forEach((function(e){return e(n)})),t)return t(n)},u=setTimeout(c.bind(null,void 0,{type:"timeout",target:r}),12e4);r.onerror=c.bind(null,r.onerror),r.onload=c.bind(null,r.onload),o&&document.head.appendChild(r)}},__webpack_require__.r=function(e){"undefined"!=typeof Symbol&&Symbol.toStringTag&&Object.defineProperty(e,Symbol.toStringTag,{value:"Module"}),Object.defineProperty(e,"__esModule",{value:!0})},__webpack_require__.p="/static/",loadStylesheet=function(e){return new Promise((function(t,n){var i=__webpack_require__.miniCssF(e),r=__webpack_require__.p+i;if(function(e,t){for(var n=document.getElementsByTagName("link"),i=0;i<n.length;i++){var r=(a=n[i]).getAttribute("data-href")||a.getAttribute("href");if("stylesheet"===a.rel&&(r===e||r===t))return a}var o=document.getElementsByTagName("style");for(i=0;i<o.length;i++){var a;if((r=(a=o[i]).getAttribute("data-href"))===e||r===t)return a}}(i,r))return t();!function(e,t,n,i){var r=document.createElement("link");r.rel="stylesheet",r.type="text/css",r.onerror=r.onload=function(o){if(r.onerror=r.onload=null,"load"===o.type)n();else{var a=o&&("load"===o.type?"missing":o.type),s=o&&o.target&&o.target.href||t,l=new Error("Loading CSS chunk "+e+" failed.\n("+s+")");l.code="CSS_CHUNK_LOAD_FAILED",l.type=a,l.request=s,r.parentNode.removeChild(r),i(l)}},r.href=t,document.head.appendChild(r)}(e,r,t,n)}))},installedCssChunks={679:0},__webpack_require__.f.miniCss=function(e,t){installedCssChunks[e]?t.push(installedCssChunks[e]):0!==installedCssChunks[e]&&{399:1}[e]&&t.push(installedCssChunks[e]=loadStylesheet(e).then((function(){installedCssChunks[e]=0}),(function(t){throw delete installedCssChunks[e],t})))},function(){var e={679:0};__webpack_require__.f.j=function(t,n){var i=__webpack_require__.o(e,t)?e[t]:void 0;if(0!==i)if(i)n.push(i[2]);else{var r=new Promise((function(n,r){i=e[t]=[n,r]}));n.push(i[2]=r);var o=__webpack_require__.p+__webpack_require__.u(t),a=new Error;__webpack_require__.l(o,(function(n){if(__webpack_require__.o(e,t)&&(0!==(i=e[t])&&(e[t]=void 0),i)){var r=n&&("load"===n.type?"missing":n.type),o=n&&n.target&&n.target.src;a.message="Loading chunk "+t+" failed.\n("+r+": "+o+")",a.name="ChunkLoadError",a.type=r,a.request=o,i[1](a)}}),"chunk-"+t,t)}};var t=function(t,n){for(var i,r,o=n[0],a=n[1],s=n[2],l=0,c=[];l<o.length;l++)r=o[l],__webpack_require__.o(e,r)&&e[r]&&c.push(e[r][0]),e[r]=0;for(i in a)__webpack_require__.o(a,i)&&(__webpack_require__.m[i]=a[i]);for(s&&s(__webpack_require__),t&&t(n);c.length;)c.shift()()},n=self.webpackChunkswh_name_=self.webpackChunkswh_name_||[];n.forEach(t.bind(null,0)),n.push=t.bind(null,n.push.bind(n))}();var __webpack_exports__={};return function(){"use strict";__webpack_require__.r(__webpack_exports__),__webpack_require__.d(__webpack_exports__,{computeAllDiffs:function(){return e.St},computeDiff:function(){return e.D_},formatDiffLineNumbers:function(){return e.OU},fragmentToSelectedDiffLines:function(){return e.EV},initRevisionDiff:function(){return e.qo},parseDiffLineNumbers:function(){return e.sr},selectedDiffLinesToFragment:function(){return e.S0},showSplitDiff:function(){return e.Mo},showUnifiedDiff:function(){return e.n2},initRevisionsLog:function(){return t.o},revsOrderingTypeClicked:function(){return t.i}});var e=__webpack_require__(79700),t=__webpack_require__(7416)}(),__webpack_exports__}()}));
//# sourceMappingURL=revision.94a002d24a26693a274d.js.map