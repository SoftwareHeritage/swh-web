/*! For license information please see deposit.b1eaf04149d75110a2e3.js.LICENSE.txt */
!function(){try{var t="undefined"!=typeof window?window:"undefined"!=typeof global?global:"undefined"!=typeof self?self:{},e=(new Error).stack;e&&(t._sentryDebugIds=t._sentryDebugIds||{},t._sentryDebugIds[e]="444947ae-9c8c-4fbf-aad1-726418962c68",t._sentryDebugIdIdentifier="sentry-dbid-444947ae-9c8c-4fbf-aad1-726418962c68")}catch(t){}}();var _global="undefined"!=typeof window?window:"undefined"!=typeof global?global:"undefined"!=typeof self?self:{};_global.SENTRY_RELEASE={id:"0.3.1"},function(t,e){"object"==typeof exports&&"object"==typeof module?module.exports=e():"function"==typeof define&&define.amd?define([],e):"object"==typeof exports?exports.swh=e():(t.swh=t.swh||{},t.swh.deposit=e())}(self,(function(){return function(){var t={59537:function(t,e,r){"use strict";r.d(e,{Jp:function(){return n},_3:function(){return o}});r(64687),r(31955);function n(t){return new Date(t).toLocaleString()}function o(t,e,r,n){if(void 0===r&&(r=!1),void 0===n&&(n=""),"display"===e&&t){var o=encodeURI(t);n||(n=o);var i="";return r&&(i='target="_blank" rel="noopener noreferrer"'),'<a href="'+o+'" '+i+">"+n+"</a>"}return t}},17061:function(t,e,r){var n=r(18698).default;function o(){"use strict";t.exports=o=function(){return r},t.exports.__esModule=!0,t.exports.default=t.exports;var e,r={},i=Object.prototype,a=i.hasOwnProperty,c=Object.defineProperty||function(t,e,r){t[e]=r.value},u="function"==typeof Symbol?Symbol:{},s=u.iterator||"@@iterator",l=u.asyncIterator||"@@asyncIterator",d=u.toStringTag||"@@toStringTag";function f(t,e,r){return Object.defineProperty(t,e,{value:r,enumerable:!0,configurable:!0,writable:!0}),t[e]}try{f({},"")}catch(e){f=function(t,e,r){return t[e]=r}}function p(t,e,r,n){var o=e&&e.prototype instanceof b?e:b,i=Object.create(o.prototype),a=new D(n||[]);return c(i,"_invoke",{value:T(t,r,a)}),i}function h(t,e,r){try{return{type:"normal",arg:t.call(e,r)}}catch(t){return{type:"throw",arg:t}}}r.wrap=p;var y="suspendedStart",v="suspendedYield",m="executing",w="completed",g={};function b(){}function x(){}function _(){}var E={};f(E,s,(function(){return this}));var L=Object.getPrototypeOf,j=L&&L(L(N([])));j&&j!==i&&a.call(j,s)&&(E=j);var O=_.prototype=b.prototype=Object.create(E);function S(t){["next","throw","return"].forEach((function(e){f(t,e,(function(t){return this._invoke(e,t)}))}))}function k(t,e){function r(o,i,c,u){var s=h(t[o],t,i);if("throw"!==s.type){var l=s.arg,d=l.value;return d&&"object"==n(d)&&a.call(d,"__await")?e.resolve(d.__await).then((function(t){r("next",t,c,u)}),(function(t){r("throw",t,c,u)})):e.resolve(d).then((function(t){l.value=t,c(l)}),(function(t){return r("throw",t,c,u)}))}u(s.arg)}var o;c(this,"_invoke",{value:function(t,n){function i(){return new e((function(e,o){r(t,n,e,o)}))}return o=o?o.then(i,i):i()}})}function T(t,r,n){var o=y;return function(i,a){if(o===m)throw new Error("Generator is already running");if(o===w){if("throw"===i)throw a;return{value:e,done:!0}}for(n.method=i,n.arg=a;;){var c=n.delegate;if(c){var u=C(c,n);if(u){if(u===g)continue;return u}}if("next"===n.method)n.sent=n._sent=n.arg;else if("throw"===n.method){if(o===y)throw o=w,n.arg;n.dispatchException(n.arg)}else"return"===n.method&&n.abrupt("return",n.arg);o=m;var s=h(t,r,n);if("normal"===s.type){if(o=n.done?w:v,s.arg===g)continue;return{value:s.arg,done:n.done}}"throw"===s.type&&(o=w,n.method="throw",n.arg=s.arg)}}}function C(t,r){var n=r.method,o=t.iterator[n];if(o===e)return r.delegate=null,"throw"===n&&t.iterator.return&&(r.method="return",r.arg=e,C(t,r),"throw"===r.method)||"return"!==n&&(r.method="throw",r.arg=new TypeError("The iterator does not provide a '"+n+"' method")),g;var i=h(o,t.iterator,r.arg);if("throw"===i.type)return r.method="throw",r.arg=i.arg,r.delegate=null,g;var a=i.arg;return a?a.done?(r[t.resultName]=a.value,r.next=t.nextLoc,"return"!==r.method&&(r.method="next",r.arg=e),r.delegate=null,g):a:(r.method="throw",r.arg=new TypeError("iterator result is not an object"),r.delegate=null,g)}function I(t){var e={tryLoc:t[0]};1 in t&&(e.catchLoc=t[1]),2 in t&&(e.finallyLoc=t[2],e.afterLoc=t[3]),this.tryEntries.push(e)}function $(t){var e=t.completion||{};e.type="normal",delete e.arg,t.completion=e}function D(t){this.tryEntries=[{tryLoc:"root"}],t.forEach(I,this),this.reset(!0)}function N(t){if(t||""===t){var r=t[s];if(r)return r.call(t);if("function"==typeof t.next)return t;if(!isNaN(t.length)){var o=-1,i=function r(){for(;++o<t.length;)if(a.call(t,o))return r.value=t[o],r.done=!1,r;return r.value=e,r.done=!0,r};return i.next=i}}throw new TypeError(n(t)+" is not iterable")}return x.prototype=_,c(O,"constructor",{value:_,configurable:!0}),c(_,"constructor",{value:x,configurable:!0}),x.displayName=f(_,d,"GeneratorFunction"),r.isGeneratorFunction=function(t){var e="function"==typeof t&&t.constructor;return!!e&&(e===x||"GeneratorFunction"===(e.displayName||e.name))},r.mark=function(t){return Object.setPrototypeOf?Object.setPrototypeOf(t,_):(t.__proto__=_,f(t,d,"GeneratorFunction")),t.prototype=Object.create(O),t},r.awrap=function(t){return{__await:t}},S(k.prototype),f(k.prototype,l,(function(){return this})),r.AsyncIterator=k,r.async=function(t,e,n,o,i){void 0===i&&(i=Promise);var a=new k(p(t,e,n,o),i);return r.isGeneratorFunction(e)?a:a.next().then((function(t){return t.done?t.value:a.next()}))},S(O),f(O,d,"Generator"),f(O,s,(function(){return this})),f(O,"toString",(function(){return"[object Generator]"})),r.keys=function(t){var e=Object(t),r=[];for(var n in e)r.push(n);return r.reverse(),function t(){for(;r.length;){var n=r.pop();if(n in e)return t.value=n,t.done=!1,t}return t.done=!0,t}},r.values=N,D.prototype={constructor:D,reset:function(t){if(this.prev=0,this.next=0,this.sent=this._sent=e,this.done=!1,this.delegate=null,this.method="next",this.arg=e,this.tryEntries.forEach($),!t)for(var r in this)"t"===r.charAt(0)&&a.call(this,r)&&!isNaN(+r.slice(1))&&(this[r]=e)},stop:function(){this.done=!0;var t=this.tryEntries[0].completion;if("throw"===t.type)throw t.arg;return this.rval},dispatchException:function(t){if(this.done)throw t;var r=this;function n(n,o){return c.type="throw",c.arg=t,r.next=n,o&&(r.method="next",r.arg=e),!!o}for(var o=this.tryEntries.length-1;o>=0;--o){var i=this.tryEntries[o],c=i.completion;if("root"===i.tryLoc)return n("end");if(i.tryLoc<=this.prev){var u=a.call(i,"catchLoc"),s=a.call(i,"finallyLoc");if(u&&s){if(this.prev<i.catchLoc)return n(i.catchLoc,!0);if(this.prev<i.finallyLoc)return n(i.finallyLoc)}else if(u){if(this.prev<i.catchLoc)return n(i.catchLoc,!0)}else{if(!s)throw new Error("try statement without catch or finally");if(this.prev<i.finallyLoc)return n(i.finallyLoc)}}}},abrupt:function(t,e){for(var r=this.tryEntries.length-1;r>=0;--r){var n=this.tryEntries[r];if(n.tryLoc<=this.prev&&a.call(n,"finallyLoc")&&this.prev<n.finallyLoc){var o=n;break}}o&&("break"===t||"continue"===t)&&o.tryLoc<=e&&e<=o.finallyLoc&&(o=null);var i=o?o.completion:{};return i.type=t,i.arg=e,o?(this.method="next",this.next=o.finallyLoc,g):this.complete(i)},complete:function(t,e){if("throw"===t.type)throw t.arg;return"break"===t.type||"continue"===t.type?this.next=t.arg:"return"===t.type?(this.rval=this.arg=t.arg,this.method="return",this.next="end"):"normal"===t.type&&e&&(this.next=e),g},finish:function(t){for(var e=this.tryEntries.length-1;e>=0;--e){var r=this.tryEntries[e];if(r.finallyLoc===t)return this.complete(r.completion,r.afterLoc),$(r),g}},catch:function(t){for(var e=this.tryEntries.length-1;e>=0;--e){var r=this.tryEntries[e];if(r.tryLoc===t){var n=r.completion;if("throw"===n.type){var o=n.arg;$(r)}return o}}throw new Error("illegal catch attempt")},delegateYield:function(t,r,n){return this.delegate={iterator:N(t),resultName:r,nextLoc:n},"next"===this.method&&(this.arg=e),g}},r}t.exports=o,t.exports.__esModule=!0,t.exports.default=t.exports},18698:function(t){function e(r){return t.exports=e="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},t.exports.__esModule=!0,t.exports.default=t.exports,e(r)}t.exports=e,t.exports.__esModule=!0,t.exports.default=t.exports},64687:function(t,e,r){var n=r(17061)();t.exports=n;try{regeneratorRuntime=n}catch(t){"object"==typeof globalThis?globalThis.regeneratorRuntime=n:Function("r","regeneratorRuntime = r")(n)}},31955:function(t,e,r){"use strict";function n(t){for(var e=1;e<arguments.length;e++){var r=arguments[e];for(var n in r)t[n]=r[n]}return t}(function t(e,r){function o(t,o,i){if("undefined"!=typeof document){"number"==typeof(i=n({},r,i)).expires&&(i.expires=new Date(Date.now()+864e5*i.expires)),i.expires&&(i.expires=i.expires.toUTCString()),t=encodeURIComponent(t).replace(/%(2[346B]|5E|60|7C)/g,decodeURIComponent).replace(/[()]/g,escape);var a="";for(var c in i)i[c]&&(a+="; "+c,!0!==i[c]&&(a+="="+i[c].split(";")[0]));return document.cookie=t+"="+e.write(o,t)+a}}return Object.create({set:o,get:function(t){if("undefined"!=typeof document&&(!arguments.length||t)){for(var r=document.cookie?document.cookie.split("; "):[],n={},o=0;o<r.length;o++){var i=r[o].split("="),a=i.slice(1).join("=");try{var c=decodeURIComponent(i[0]);if(n[c]=e.read(a,c),t===c)break}catch(t){}}return t?n[t]:n}},remove:function(t,e){o(t,"",n({},e,{expires:-1}))},withAttributes:function(e){return t(this.converter,n({},this.attributes,e))},withConverter:function(e){return t(n({},this.converter,e),this.attributes)}},{attributes:{value:Object.freeze(r)},converter:{value:Object.freeze(e)}})})({read:function(t){return'"'===t[0]&&(t=t.slice(1,-1)),t.replace(/(%[\dA-F]{2})+/gi,decodeURIComponent)},write:function(t){return encodeURIComponent(t).replace(/%(2[346BF]|3[AC-F]|40|5[BDE]|60|7[BCD])/g,decodeURIComponent)}},{path:"/"})}},e={};function r(n){var o=e[n];if(void 0!==o)return o.exports;var i=e[n]={exports:{}};return t[n](i,i.exports,r),i.exports}r.n=function(t){var e=t&&t.__esModule?function(){return t.default}:function(){return t};return r.d(e,{a:e}),e},r.d=function(t,e){for(var n in e)r.o(e,n)&&!r.o(t,n)&&Object.defineProperty(t,n,{enumerable:!0,get:e[n]})},r.o=function(t,e){return Object.prototype.hasOwnProperty.call(t,e)},r.r=function(t){"undefined"!=typeof Symbol&&Symbol.toStringTag&&Object.defineProperty(t,Symbol.toStringTag,{value:"Module"}),Object.defineProperty(t,"__esModule",{value:!0})};var n={};return function(){"use strict";r.r(n),r.d(n,{initDepositAdmin:function(){return o}});var t=r(59537);function e(t,e,r){if(void 0===r&&(r=""),"display"===e&&t&&t.startsWith("swh")){var n=Urls.browse_swhid(t),o=t.replace(/;/g,";<br/>");return r||(r=o),'<a href="'+n+'">'+r+"</a>"}return t}function o(r,n){var o;$(document).ready((function(){$.fn.dataTable.ext.errMode="none",o=$("#swh-admin-deposit-list").on("error.dt",(function(t,e,r,n){$("#swh-admin-deposit-list-error").text(n)})).DataTable({serverSide:!0,processing:!0,dom:'<<"d-flex justify-content-between align-items-center"f<"#list-exclude">l>rt<"bottom"ip>>',ajax:{url:Urls.admin_deposit_list(),data:function(t){t.excludePattern=$("#swh-admin-deposit-list-exclude-filter").val()}},columns:[{data:"id",name:"id"},{data:"type",name:"type"},{data:"uri",name:"uri",render:function(r,n,o){var i=$.fn.dataTable.render.text().display(r),a="",c="";return o.swhid_context&&r?a=e(o.swhid_context,n,i):r&&(a=i),r&&(c=(0,t._3)(i,n,!0,'<i class="mdi mdi-open-in-new" aria-hidden="true"></i>')),a+"&nbsp;"+c}},{data:"reception_date",name:"reception_date",render:t.Jp},{data:"status",name:"status"},{data:"raw_metadata",name:"raw_metadata",render:function(t,e,r){return"display"===e&&r.raw_metadata?'<button class="btn btn-default metadata">display</button>':t}},{data:"status_detail",name:"status_detail",render:function(t,e,r){if("display"===e&&t){var n=t;return"object"==typeof t&&(n=JSON.stringify(t,null,4)),'<div style="width: 200px; white-space: pre; overflow-x: auto;">'+n+"</div>"}return t},orderable:!1,visible:!1},{data:"swhid",name:"swhid",render:function(t,r,n){return e(t,r)},orderable:!1,visible:!1},{data:"swhid_context",name:"swhid_context",render:function(t,r,n){return e(t,r)},orderable:!1,visible:!1}],scrollX:!0,scrollY:"50vh",scrollCollapse:!0,order:[[0,"desc"]]}),$("div#list-exclude").html('<div id="swh-admin-deposit-list-exclude-wrapper">\n    <div id="swh-admin-deposit-list-exclude-div-wrapper" class="dataTables_filter">\n      <label>\n        Exclude:<input id="swh-admin-deposit-list-exclude-filter"\n                       type="search"\n                       value="check-deposit"\n                       class="form-control form-control-sm"\n                       placeholder="exclude-pattern" aria-controls="swh-admin-deposit-list">\n          </input>\n      </label>\n    </div>\n  </div>\n'),$("#swh-admin-deposit-list tbody").on("click","tr button.metadata",(function(){var t=o.row(this.parentNode.parentNode).data(),e=t.raw_metadata,r=$("<div/>").text(e).html();swh.webapp.showModalHtml("Metadata of deposit "+t.id,'<pre style="max-height: 75vh;"><code class="xml">'+r+"</code></pre>","90%"),swh.webapp.highlightCode()})),$("#swh-admin-deposit-list-exclude-filter").keyup((function(){o.draw()})),o.draw()})),$("a.toggle-col").on("click",(function(t){t.preventDefault();var e=o.column($(this).attr("data-column"));e.visible(!e.visible()),e.visible()?$(this).removeClass("col-hidden"):$(this).addClass("col-hidden")}))}}(),n}()}));
//# sourceMappingURL=deposit.b1eaf04149d75110a2e3.js.map