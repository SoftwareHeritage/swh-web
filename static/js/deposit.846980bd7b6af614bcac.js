/*! For license information please see deposit.846980bd7b6af614bcac.js.LICENSE.txt */
!function(){try{var t="undefined"!=typeof window?window:"undefined"!=typeof global?global:"undefined"!=typeof self?self:{},e=(new Error).stack;e&&(t._sentryDebugIds=t._sentryDebugIds||{},t._sentryDebugIds[e]="837d1cdc-5e0a-4757-a662-3b9704295194",t._sentryDebugIdIdentifier="sentry-dbid-837d1cdc-5e0a-4757-a662-3b9704295194")}catch(t){}}();var _global="undefined"!=typeof window?window:"undefined"!=typeof global?global:"undefined"!=typeof self?self:{};_global.SENTRY_RELEASE={id:"0.2.27"},function(t,e){"object"==typeof exports&&"object"==typeof module?module.exports=e():"function"==typeof define&&define.amd?define([],e):"object"==typeof exports?exports.swh=e():(t.swh=t.swh||{},t.swh.deposit=e())}(self,(function(){return function(){var t={87757:function(t,e,r){r(35666)},59537:function(t,e,r){"use strict";r.d(e,{Jp:function(){return n},_3:function(){return o}});r(87757),r(31955);function n(t){return new Date(t).toLocaleString()}function o(t,e,r,n){if(void 0===r&&(r=!1),void 0===n&&(n=""),"display"===e&&t){var o=encodeURI(t);n||(n=o);var i="";return r&&(i='target="_blank" rel="noopener noreferrer"'),'<a href="'+o+'" '+i+">"+n+"</a>"}return t}},35666:function(t){var e=function(t){"use strict";var e,r=Object.prototype,n=r.hasOwnProperty,o=Object.defineProperty||function(t,e,r){t[e]=r.value},i="function"==typeof Symbol?Symbol:{},a=i.iterator||"@@iterator",c=i.asyncIterator||"@@asyncIterator",u=i.toStringTag||"@@toStringTag";function s(t,e,r){return Object.defineProperty(t,e,{value:r,enumerable:!0,configurable:!0,writable:!0}),t[e]}try{s({},"")}catch(t){s=function(t,e,r){return t[e]=r}}function l(t,e,r,n){var i=e&&e.prototype instanceof m?e:m,a=Object.create(i.prototype),c=new I(n||[]);return o(a,"_invoke",{value:O(t,r,c)}),a}function d(t,e,r){try{return{type:"normal",arg:t.call(e,r)}}catch(t){return{type:"throw",arg:t}}}t.wrap=l;var f="suspendedStart",h="suspendedYield",p="executing",v="completed",y={};function m(){}function w(){}function g(){}var b={};s(b,a,(function(){return this}));var x=Object.getPrototypeOf,_=x&&x(x(T([])));_&&_!==r&&n.call(_,a)&&(b=_);var E=g.prototype=m.prototype=Object.create(b);function L(t){["next","throw","return"].forEach((function(e){s(t,e,(function(t){return this._invoke(e,t)}))}))}function j(t,e){function r(o,i,a,c){var u=d(t[o],t,i);if("throw"!==u.type){var s=u.arg,l=s.value;return l&&"object"==typeof l&&n.call(l,"__await")?e.resolve(l.__await).then((function(t){r("next",t,a,c)}),(function(t){r("throw",t,a,c)})):e.resolve(l).then((function(t){s.value=t,a(s)}),(function(t){return r("throw",t,a,c)}))}c(u.arg)}var i;o(this,"_invoke",{value:function(t,n){function o(){return new e((function(e,o){r(t,n,e,o)}))}return i=i?i.then(o,o):o()}})}function O(t,e,r){var n=f;return function(o,i){if(n===p)throw new Error("Generator is already running");if(n===v){if("throw"===o)throw i;return $()}for(r.method=o,r.arg=i;;){var a=r.delegate;if(a){var c=k(a,r);if(c){if(c===y)continue;return c}}if("next"===r.method)r.sent=r._sent=r.arg;else if("throw"===r.method){if(n===f)throw n=v,r.arg;r.dispatchException(r.arg)}else"return"===r.method&&r.abrupt("return",r.arg);n=p;var u=d(t,e,r);if("normal"===u.type){if(n=r.done?v:h,u.arg===y)continue;return{value:u.arg,done:r.done}}"throw"===u.type&&(n=v,r.method="throw",r.arg=u.arg)}}}function k(t,r){var n=r.method,o=t.iterator[n];if(o===e)return r.delegate=null,"throw"===n&&t.iterator.return&&(r.method="return",r.arg=e,k(t,r),"throw"===r.method)||"return"!==n&&(r.method="throw",r.arg=new TypeError("The iterator does not provide a '"+n+"' method")),y;var i=d(o,t.iterator,r.arg);if("throw"===i.type)return r.method="throw",r.arg=i.arg,r.delegate=null,y;var a=i.arg;return a?a.done?(r[t.resultName]=a.value,r.next=t.nextLoc,"return"!==r.method&&(r.method="next",r.arg=e),r.delegate=null,y):a:(r.method="throw",r.arg=new TypeError("iterator result is not an object"),r.delegate=null,y)}function S(t){var e={tryLoc:t[0]};1 in t&&(e.catchLoc=t[1]),2 in t&&(e.finallyLoc=t[2],e.afterLoc=t[3]),this.tryEntries.push(e)}function C(t){var e=t.completion||{};e.type="normal",delete e.arg,t.completion=e}function I(t){this.tryEntries=[{tryLoc:"root"}],t.forEach(S,this),this.reset(!0)}function T(t){if(t){var r=t[a];if(r)return r.call(t);if("function"==typeof t.next)return t;if(!isNaN(t.length)){var o=-1,i=function r(){for(;++o<t.length;)if(n.call(t,o))return r.value=t[o],r.done=!1,r;return r.value=e,r.done=!0,r};return i.next=i}}return{next:$}}function $(){return{value:e,done:!0}}return w.prototype=g,o(E,"constructor",{value:g,configurable:!0}),o(g,"constructor",{value:w,configurable:!0}),w.displayName=s(g,u,"GeneratorFunction"),t.isGeneratorFunction=function(t){var e="function"==typeof t&&t.constructor;return!!e&&(e===w||"GeneratorFunction"===(e.displayName||e.name))},t.mark=function(t){return Object.setPrototypeOf?Object.setPrototypeOf(t,g):(t.__proto__=g,s(t,u,"GeneratorFunction")),t.prototype=Object.create(E),t},t.awrap=function(t){return{__await:t}},L(j.prototype),s(j.prototype,c,(function(){return this})),t.AsyncIterator=j,t.async=function(e,r,n,o,i){void 0===i&&(i=Promise);var a=new j(l(e,r,n,o),i);return t.isGeneratorFunction(r)?a:a.next().then((function(t){return t.done?t.value:a.next()}))},L(E),s(E,u,"Generator"),s(E,a,(function(){return this})),s(E,"toString",(function(){return"[object Generator]"})),t.keys=function(t){var e=Object(t),r=[];for(var n in e)r.push(n);return r.reverse(),function t(){for(;r.length;){var n=r.pop();if(n in e)return t.value=n,t.done=!1,t}return t.done=!0,t}},t.values=T,I.prototype={constructor:I,reset:function(t){if(this.prev=0,this.next=0,this.sent=this._sent=e,this.done=!1,this.delegate=null,this.method="next",this.arg=e,this.tryEntries.forEach(C),!t)for(var r in this)"t"===r.charAt(0)&&n.call(this,r)&&!isNaN(+r.slice(1))&&(this[r]=e)},stop:function(){this.done=!0;var t=this.tryEntries[0].completion;if("throw"===t.type)throw t.arg;return this.rval},dispatchException:function(t){if(this.done)throw t;var r=this;function o(n,o){return c.type="throw",c.arg=t,r.next=n,o&&(r.method="next",r.arg=e),!!o}for(var i=this.tryEntries.length-1;i>=0;--i){var a=this.tryEntries[i],c=a.completion;if("root"===a.tryLoc)return o("end");if(a.tryLoc<=this.prev){var u=n.call(a,"catchLoc"),s=n.call(a,"finallyLoc");if(u&&s){if(this.prev<a.catchLoc)return o(a.catchLoc,!0);if(this.prev<a.finallyLoc)return o(a.finallyLoc)}else if(u){if(this.prev<a.catchLoc)return o(a.catchLoc,!0)}else{if(!s)throw new Error("try statement without catch or finally");if(this.prev<a.finallyLoc)return o(a.finallyLoc)}}}},abrupt:function(t,e){for(var r=this.tryEntries.length-1;r>=0;--r){var o=this.tryEntries[r];if(o.tryLoc<=this.prev&&n.call(o,"finallyLoc")&&this.prev<o.finallyLoc){var i=o;break}}i&&("break"===t||"continue"===t)&&i.tryLoc<=e&&e<=i.finallyLoc&&(i=null);var a=i?i.completion:{};return a.type=t,a.arg=e,i?(this.method="next",this.next=i.finallyLoc,y):this.complete(a)},complete:function(t,e){if("throw"===t.type)throw t.arg;return"break"===t.type||"continue"===t.type?this.next=t.arg:"return"===t.type?(this.rval=this.arg=t.arg,this.method="return",this.next="end"):"normal"===t.type&&e&&(this.next=e),y},finish:function(t){for(var e=this.tryEntries.length-1;e>=0;--e){var r=this.tryEntries[e];if(r.finallyLoc===t)return this.complete(r.completion,r.afterLoc),C(r),y}},catch:function(t){for(var e=this.tryEntries.length-1;e>=0;--e){var r=this.tryEntries[e];if(r.tryLoc===t){var n=r.completion;if("throw"===n.type){var o=n.arg;C(r)}return o}}throw new Error("illegal catch attempt")},delegateYield:function(t,r,n){return this.delegate={iterator:T(t),resultName:r,nextLoc:n},"next"===this.method&&(this.arg=e),y}},t}(t.exports);try{regeneratorRuntime=e}catch(t){"object"==typeof globalThis?globalThis.regeneratorRuntime=e:Function("r","regeneratorRuntime = r")(e)}},31955:function(t,e,r){"use strict";function n(t){for(var e=1;e<arguments.length;e++){var r=arguments[e];for(var n in r)t[n]=r[n]}return t}(function t(e,r){function o(t,o,i){if("undefined"!=typeof document){"number"==typeof(i=n({},r,i)).expires&&(i.expires=new Date(Date.now()+864e5*i.expires)),i.expires&&(i.expires=i.expires.toUTCString()),t=encodeURIComponent(t).replace(/%(2[346B]|5E|60|7C)/g,decodeURIComponent).replace(/[()]/g,escape);var a="";for(var c in i)i[c]&&(a+="; "+c,!0!==i[c]&&(a+="="+i[c].split(";")[0]));return document.cookie=t+"="+e.write(o,t)+a}}return Object.create({set:o,get:function(t){if("undefined"!=typeof document&&(!arguments.length||t)){for(var r=document.cookie?document.cookie.split("; "):[],n={},o=0;o<r.length;o++){var i=r[o].split("="),a=i.slice(1).join("=");try{var c=decodeURIComponent(i[0]);if(n[c]=e.read(a,c),t===c)break}catch(t){}}return t?n[t]:n}},remove:function(t,e){o(t,"",n({},e,{expires:-1}))},withAttributes:function(e){return t(this.converter,n({},this.attributes,e))},withConverter:function(e){return t(n({},this.converter,e),this.attributes)}},{attributes:{value:Object.freeze(r)},converter:{value:Object.freeze(e)}})})({read:function(t){return'"'===t[0]&&(t=t.slice(1,-1)),t.replace(/(%[\dA-F]{2})+/gi,decodeURIComponent)},write:function(t){return encodeURIComponent(t).replace(/%(2[346BF]|3[AC-F]|40|5[BDE]|60|7[BCD])/g,decodeURIComponent)}},{path:"/"})}},e={};function r(n){var o=e[n];if(void 0!==o)return o.exports;var i=e[n]={exports:{}};return t[n](i,i.exports,r),i.exports}r.n=function(t){var e=t&&t.__esModule?function(){return t.default}:function(){return t};return r.d(e,{a:e}),e},r.d=function(t,e){for(var n in e)r.o(e,n)&&!r.o(t,n)&&Object.defineProperty(t,n,{enumerable:!0,get:e[n]})},r.o=function(t,e){return Object.prototype.hasOwnProperty.call(t,e)},r.r=function(t){"undefined"!=typeof Symbol&&Symbol.toStringTag&&Object.defineProperty(t,Symbol.toStringTag,{value:"Module"}),Object.defineProperty(t,"__esModule",{value:!0})};var n={};return function(){"use strict";r.r(n),r.d(n,{initDepositAdmin:function(){return o}});var t=r(59537);function e(t,e,r){if(void 0===r&&(r=""),"display"===e&&t&&t.startsWith("swh")){var n=Urls.browse_swhid(t),o=t.replace(/;/g,";<br/>");return r||(r=o),'<a href="'+n+'">'+r+"</a>"}return t}function o(r,n){var o;$(document).ready((function(){$.fn.dataTable.ext.errMode="none",o=$("#swh-admin-deposit-list").on("error.dt",(function(t,e,r,n){$("#swh-admin-deposit-list-error").text(n)})).DataTable({serverSide:!0,processing:!0,dom:'<<"d-flex justify-content-between align-items-center"f<"#list-exclude">l>rt<"bottom"ip>>',ajax:{url:Urls.admin_deposit_list(),data:function(t){t.excludePattern=$("#swh-admin-deposit-list-exclude-filter").val()}},columns:[{data:"id",name:"id"},{data:"type",name:"type"},{data:"uri",name:"uri",render:function(r,n,o){var i=$.fn.dataTable.render.text().display(r),a="",c="";return o.swhid_context&&r?a=e(o.swhid_context,n,i):r&&(a=i),r&&(c=(0,t._3)(i,n,!0,'<i class="mdi mdi-open-in-new" aria-hidden="true"></i>')),a+"&nbsp;"+c}},{data:"reception_date",name:"reception_date",render:t.Jp},{data:"status",name:"status"},{data:"raw_metadata",name:"raw_metadata",render:function(t,e,r){return"display"===e&&r.raw_metadata?'<button class="btn btn-default metadata">display</button>':t}},{data:"status_detail",name:"status_detail",render:function(t,e,r){if("display"===e&&t){var n=t;return"object"==typeof t&&(n=JSON.stringify(t,null,4)),'<div style="width: 200px; white-space: pre; overflow-x: auto;">'+n+"</div>"}return t},orderable:!1,visible:!1},{data:"swhid",name:"swhid",render:function(t,r,n){return e(t,r)},orderable:!1,visible:!1},{data:"swhid_context",name:"swhid_context",render:function(t,r,n){return e(t,r)},orderable:!1,visible:!1}],scrollX:!0,scrollY:"50vh",scrollCollapse:!0,order:[[0,"desc"]]}),$("div#list-exclude").html('<div id="swh-admin-deposit-list-exclude-wrapper">\n    <div id="swh-admin-deposit-list-exclude-div-wrapper" class="dataTables_filter">\n      <label>\n        Exclude:<input id="swh-admin-deposit-list-exclude-filter"\n                       type="search"\n                       value="check-deposit"\n                       class="form-control form-control-sm"\n                       placeholder="exclude-pattern" aria-controls="swh-admin-deposit-list">\n          </input>\n      </label>\n    </div>\n  </div>\n'),$("#swh-admin-deposit-list tbody").on("click","tr button.metadata",(function(){var t=o.row(this.parentNode.parentNode).data(),e=t.raw_metadata,r=$("<div/>").text(e).html();swh.webapp.showModalHtml("Metadata of deposit "+t.id,'<pre style="max-height: 75vh;"><code class="xml">'+r+"</code></pre>","90%"),swh.webapp.highlightCode()})),$("#swh-admin-deposit-list-exclude-filter").keyup((function(){o.draw()})),o.draw()})),$("a.toggle-col").on("click",(function(t){t.preventDefault();var e=o.column($(this).attr("data-column"));e.visible(!e.visible()),e.visible()?$(this).removeClass("col-hidden"):$(this).addClass("col-hidden")}))}}(),n}()}));
//# sourceMappingURL=deposit.846980bd7b6af614bcac.js.map