/*! For license information please see mailmap.bc51519d9b54299cfe5e.js.LICENSE.txt */
!function(){try{var e="undefined"!=typeof window?window:"undefined"!=typeof global?global:"undefined"!=typeof self?self:{},t=(new Error).stack;t&&(e._sentryDebugIds=e._sentryDebugIds||{},e._sentryDebugIds[t]="00c0e1e4-8c28-4230-84ea-f06be38bd9f1",e._sentryDebugIdIdentifier="sentry-dbid-00c0e1e4-8c28-4230-84ea-f06be38bd9f1")}catch(e){}}();var _global="undefined"!=typeof window?window:"undefined"!=typeof global?global:"undefined"!=typeof self?self:{};_global.SENTRY_RELEASE={id:"0.2.36"},function(e,t){"object"==typeof exports&&"object"==typeof module?module.exports=t():"function"==typeof define&&define.amd?define([],t):"object"==typeof exports?exports.swh=t():(e.swh=e.swh||{},e.swh.mailmap=t())}(self,(function(){return function(){var __webpack_modules__={59537:function(e,t,r){"use strict";r.d(t,{e_:function(){return a},ry:function(){return o}});r(64687);var n=r(31955);function o(e){if(!e.ok)throw e;return e}function a(e,t,r){return void 0===t&&(t={}),void 0===r&&(r=null),t["X-CSRFToken"]=n.Z.get("csrftoken"),fetch(e,{credentials:"include",headers:t,method:"POST",body:r})}},82409:function(module){module.exports=function anonymous(locals,escapeFn,include,rethrow){escapeFn=escapeFn||function(e){return null==e?"":String(e).replace(_MATCH_HTML,encode_char)};var _ENCODE_HTML_RULES={"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&#34;","'":"&#39;"},_MATCH_HTML=/[&<>'"]/g;function encode_char(e){return _ENCODE_HTML_RULES[e]||e}var __output="";function __append(e){null!=e&&(__output+=e)}with(locals||{})__append('\n\n<form id="swh-mailmap-form" class="text-left">\n  <div class="form-group">\n    <label for="swh-mailmap-from-email">Email address</label>\n    <input type="email" class="form-control" id="swh-mailmap-from-email" value="'),__append(escapeFn(email)),__append('"\n           '),updateForm&&__append(' readonly="readonly" '),__append(' required>\n  </div>\n  <div class="form-group">\n    <label for="swh-mailmap-display-name">Display name</label>\n    <input class="form-control" id="swh-mailmap-display-name" value="'),__append(escapeFn(displayName)),__append('" placeholder="John Doe <jdoe@example.org>" required>\n  </div>\n  <div class="custom-control custom-checkbox">\n    <input class="custom-control-input" type="checkbox" value="" id="swh-mailmap-display-name-activated"\n           '),displayNameActivated&&__append(' checked="checked" '),__append('>\n    <label class="custom-control-label pt-0" for="swh-mailmap-display-name-activated">Activate display name</label>\n  </div>\n  <div class="d-flex justify-content-center">\n    <input id="swh-mailmap-form-submit" type="submit" value="'),__append(escapeFn(buttonText)),__append('">\n  </div>\n</form>');return __output}},17061:function(e,t,r){var n=r(18698).default;function o(){"use strict";e.exports=o=function(){return t},e.exports.__esModule=!0,e.exports.default=e.exports;var t={},r=Object.prototype,a=r.hasOwnProperty,i=Object.defineProperty||function(e,t,r){e[t]=r.value},c="function"==typeof Symbol?Symbol:{},u=c.iterator||"@@iterator",l=c.asyncIterator||"@@asyncIterator",s=c.toStringTag||"@@toStringTag";function p(e,t,r){return Object.defineProperty(e,t,{value:r,enumerable:!0,configurable:!0,writable:!0}),e[t]}try{p({},"")}catch(e){p=function(e,t,r){return e[t]=r}}function d(e,t,r,n){var o=t&&t.prototype instanceof m?t:m,a=Object.create(o.prototype),c=new O(n||[]);return i(a,"_invoke",{value:E(e,r,c)}),a}function f(e,t,r){try{return{type:"normal",arg:e.call(t,r)}}catch(e){return{type:"throw",arg:e}}}t.wrap=d;var _={};function m(){}function h(){}function v(){}var y={};p(y,u,(function(){return this}));var b=Object.getPrototypeOf,w=b&&b(b(T([])));w&&w!==r&&a.call(w,u)&&(y=w);var g=v.prototype=m.prototype=Object.create(y);function x(e){["next","throw","return"].forEach((function(t){p(e,t,(function(e){return this._invoke(t,e)}))}))}function k(e,t){function r(o,i,c,u){var l=f(e[o],e,i);if("throw"!==l.type){var s=l.arg,p=s.value;return p&&"object"==n(p)&&a.call(p,"__await")?t.resolve(p.__await).then((function(e){r("next",e,c,u)}),(function(e){r("throw",e,c,u)})):t.resolve(p).then((function(e){s.value=e,c(s)}),(function(e){return r("throw",e,c,u)}))}u(l.arg)}var o;i(this,"_invoke",{value:function(e,n){function a(){return new t((function(t,o){r(e,n,t,o)}))}return o=o?o.then(a,a):a()}})}function E(e,t,r){var n="suspendedStart";return function(o,a){if("executing"===n)throw new Error("Generator is already running");if("completed"===n){if("throw"===o)throw a;return M()}for(r.method=o,r.arg=a;;){var i=r.delegate;if(i){var c=L(i,r);if(c){if(c===_)continue;return c}}if("next"===r.method)r.sent=r._sent=r.arg;else if("throw"===r.method){if("suspendedStart"===n)throw n="completed",r.arg;r.dispatchException(r.arg)}else"return"===r.method&&r.abrupt("return",r.arg);n="executing";var u=f(e,t,r);if("normal"===u.type){if(n=r.done?"completed":"suspendedYield",u.arg===_)continue;return{value:u.arg,done:r.done}}"throw"===u.type&&(n="completed",r.method="throw",r.arg=u.arg)}}}function L(e,t){var r=t.method,n=e.iterator[r];if(void 0===n)return t.delegate=null,"throw"===r&&e.iterator.return&&(t.method="return",t.arg=void 0,L(e,t),"throw"===t.method)||"return"!==r&&(t.method="throw",t.arg=new TypeError("The iterator does not provide a '"+r+"' method")),_;var o=f(n,e.iterator,t.arg);if("throw"===o.type)return t.method="throw",t.arg=o.arg,t.delegate=null,_;var a=o.arg;return a?a.done?(t[e.resultName]=a.value,t.next=e.nextLoc,"return"!==t.method&&(t.method="next",t.arg=void 0),t.delegate=null,_):a:(t.method="throw",t.arg=new TypeError("iterator result is not an object"),t.delegate=null,_)}function j(e){var t={tryLoc:e[0]};1 in e&&(t.catchLoc=e[1]),2 in e&&(t.finallyLoc=e[2],t.afterLoc=e[3]),this.tryEntries.push(t)}function S(e){var t=e.completion||{};t.type="normal",delete t.arg,e.completion=t}function O(e){this.tryEntries=[{tryLoc:"root"}],e.forEach(j,this),this.reset(!0)}function T(e){if(e){var t=e[u];if(t)return t.call(e);if("function"==typeof e.next)return e;if(!isNaN(e.length)){var r=-1,n=function t(){for(;++r<e.length;)if(a.call(e,r))return t.value=e[r],t.done=!1,t;return t.value=void 0,t.done=!0,t};return n.next=n}}return{next:M}}function M(){return{value:void 0,done:!0}}return h.prototype=v,i(g,"constructor",{value:v,configurable:!0}),i(v,"constructor",{value:h,configurable:!0}),h.displayName=p(v,s,"GeneratorFunction"),t.isGeneratorFunction=function(e){var t="function"==typeof e&&e.constructor;return!!t&&(t===h||"GeneratorFunction"===(t.displayName||t.name))},t.mark=function(e){return Object.setPrototypeOf?Object.setPrototypeOf(e,v):(e.__proto__=v,p(e,s,"GeneratorFunction")),e.prototype=Object.create(g),e},t.awrap=function(e){return{__await:e}},x(k.prototype),p(k.prototype,l,(function(){return this})),t.AsyncIterator=k,t.async=function(e,r,n,o,a){void 0===a&&(a=Promise);var i=new k(d(e,r,n,o),a);return t.isGeneratorFunction(r)?i:i.next().then((function(e){return e.done?e.value:i.next()}))},x(g),p(g,s,"Generator"),p(g,u,(function(){return this})),p(g,"toString",(function(){return"[object Generator]"})),t.keys=function(e){var t=Object(e),r=[];for(var n in t)r.push(n);return r.reverse(),function e(){for(;r.length;){var n=r.pop();if(n in t)return e.value=n,e.done=!1,e}return e.done=!0,e}},t.values=T,O.prototype={constructor:O,reset:function(e){if(this.prev=0,this.next=0,this.sent=this._sent=void 0,this.done=!1,this.delegate=null,this.method="next",this.arg=void 0,this.tryEntries.forEach(S),!e)for(var t in this)"t"===t.charAt(0)&&a.call(this,t)&&!isNaN(+t.slice(1))&&(this[t]=void 0)},stop:function(){this.done=!0;var e=this.tryEntries[0].completion;if("throw"===e.type)throw e.arg;return this.rval},dispatchException:function(e){if(this.done)throw e;var t=this;function r(r,n){return i.type="throw",i.arg=e,t.next=r,n&&(t.method="next",t.arg=void 0),!!n}for(var n=this.tryEntries.length-1;n>=0;--n){var o=this.tryEntries[n],i=o.completion;if("root"===o.tryLoc)return r("end");if(o.tryLoc<=this.prev){var c=a.call(o,"catchLoc"),u=a.call(o,"finallyLoc");if(c&&u){if(this.prev<o.catchLoc)return r(o.catchLoc,!0);if(this.prev<o.finallyLoc)return r(o.finallyLoc)}else if(c){if(this.prev<o.catchLoc)return r(o.catchLoc,!0)}else{if(!u)throw new Error("try statement without catch or finally");if(this.prev<o.finallyLoc)return r(o.finallyLoc)}}}},abrupt:function(e,t){for(var r=this.tryEntries.length-1;r>=0;--r){var n=this.tryEntries[r];if(n.tryLoc<=this.prev&&a.call(n,"finallyLoc")&&this.prev<n.finallyLoc){var o=n;break}}o&&("break"===e||"continue"===e)&&o.tryLoc<=t&&t<=o.finallyLoc&&(o=null);var i=o?o.completion:{};return i.type=e,i.arg=t,o?(this.method="next",this.next=o.finallyLoc,_):this.complete(i)},complete:function(e,t){if("throw"===e.type)throw e.arg;return"break"===e.type||"continue"===e.type?this.next=e.arg:"return"===e.type?(this.rval=this.arg=e.arg,this.method="return",this.next="end"):"normal"===e.type&&t&&(this.next=t),_},finish:function(e){for(var t=this.tryEntries.length-1;t>=0;--t){var r=this.tryEntries[t];if(r.finallyLoc===e)return this.complete(r.completion,r.afterLoc),S(r),_}},catch:function(e){for(var t=this.tryEntries.length-1;t>=0;--t){var r=this.tryEntries[t];if(r.tryLoc===e){var n=r.completion;if("throw"===n.type){var o=n.arg;S(r)}return o}}throw new Error("illegal catch attempt")},delegateYield:function(e,t,r){return this.delegate={iterator:T(e),resultName:t,nextLoc:r},"next"===this.method&&(this.arg=void 0),_}},t}e.exports=o,e.exports.__esModule=!0,e.exports.default=e.exports},18698:function(e){function t(r){return e.exports=t="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(e){return typeof e}:function(e){return e&&"function"==typeof Symbol&&e.constructor===Symbol&&e!==Symbol.prototype?"symbol":typeof e},e.exports.__esModule=!0,e.exports.default=e.exports,t(r)}e.exports=t,e.exports.__esModule=!0,e.exports.default=e.exports},64687:function(e,t,r){var n=r(17061)();e.exports=n;try{regeneratorRuntime=n}catch(e){"object"==typeof globalThis?globalThis.regeneratorRuntime=n:Function("r","regeneratorRuntime = r")(n)}},15861:function(e,t,r){"use strict";function n(e,t,r,n,o,a,i){try{var c=e[a](i),u=c.value}catch(e){return void r(e)}c.done?t(u):Promise.resolve(u).then(n,o)}function o(e){return function(){var t=this,r=arguments;return new Promise((function(o,a){var i=e.apply(t,r);function c(e){n(i,o,a,c,u,"next",e)}function u(e){n(i,o,a,c,u,"throw",e)}c(void 0)}))}}r.d(t,{Z:function(){return o}})},31955:function(e,t,r){"use strict";function n(e){for(var t=1;t<arguments.length;t++){var r=arguments[t];for(var n in r)e[n]=r[n]}return e}r.d(t,{Z:function(){return o}});var o=function e(t,r){function o(e,o,a){if("undefined"!=typeof document){"number"==typeof(a=n({},r,a)).expires&&(a.expires=new Date(Date.now()+864e5*a.expires)),a.expires&&(a.expires=a.expires.toUTCString()),e=encodeURIComponent(e).replace(/%(2[346B]|5E|60|7C)/g,decodeURIComponent).replace(/[()]/g,escape);var i="";for(var c in a)a[c]&&(i+="; "+c,!0!==a[c]&&(i+="="+a[c].split(";")[0]));return document.cookie=e+"="+t.write(o,e)+i}}return Object.create({set:o,get:function(e){if("undefined"!=typeof document&&(!arguments.length||e)){for(var r=document.cookie?document.cookie.split("; "):[],n={},o=0;o<r.length;o++){var a=r[o].split("="),i=a.slice(1).join("=");try{var c=decodeURIComponent(a[0]);if(n[c]=t.read(i,c),e===c)break}catch(e){}}return e?n[e]:n}},remove:function(e,t){o(e,"",n({},t,{expires:-1}))},withAttributes:function(t){return e(this.converter,n({},this.attributes,t))},withConverter:function(t){return e(n({},this.converter,t),this.attributes)}},{attributes:{value:Object.freeze(r)},converter:{value:Object.freeze(t)}})}({read:function(e){return'"'===e[0]&&(e=e.slice(1,-1)),e.replace(/(%[\dA-F]{2})+/gi,decodeURIComponent)},write:function(e){return encodeURIComponent(e).replace(/%(2[346BF]|3[AC-F]|40|5[BDE]|60|7[BCD])/g,decodeURIComponent)}},{path:"/"})}},__webpack_module_cache__={};function __webpack_require__(e){var t=__webpack_module_cache__[e];if(void 0!==t)return t.exports;var r=__webpack_module_cache__[e]={exports:{}};return __webpack_modules__[e](r,r.exports,__webpack_require__),r.exports}__webpack_require__.n=function(e){var t=e&&e.__esModule?function(){return e.default}:function(){return e};return __webpack_require__.d(t,{a:t}),t},__webpack_require__.d=function(e,t){for(var r in t)__webpack_require__.o(t,r)&&!__webpack_require__.o(e,r)&&Object.defineProperty(e,r,{enumerable:!0,get:t[r]})},__webpack_require__.o=function(e,t){return Object.prototype.hasOwnProperty.call(e,t)},__webpack_require__.r=function(e){"undefined"!=typeof Symbol&&Symbol.toStringTag&&Object.defineProperty(e,Symbol.toStringTag,{value:"Module"}),Object.defineProperty(e,"__esModule",{value:!0})};var __webpack_exports__={};return function(){"use strict";__webpack_require__.r(__webpack_exports__),__webpack_require__.d(__webpack_exports__,{addNewMailmap:function(){return l},initMailmapUI:function(){return f},mailmapForm:function(){return c},updateMailmap:function(){return s}});var e,t=__webpack_require__(15861),r=__webpack_require__(64687),n=__webpack_require__.n(r),o=__webpack_require__(59537),a=__webpack_require__(82409),i=__webpack_require__.n(a);function c(e,t,r,n,o){return void 0===t&&(t=""),void 0===r&&(r=""),void 0===n&&(n=!1),void 0===o&&(o=!1),i()({buttonText:e,email:t,displayName:r,displayNameActivated:n,updateForm:o})}function u(r,a,i){swh.webapp.showModalHtml(r,a),$("#swh-mailmap-form").on("submit",function(){var r=(0,t.Z)(n().mark((function t(r){var a,c,u;return n().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:return r.preventDefault(),r.stopPropagation(),a={from_email:$("#swh-mailmap-from-email").val(),display_name:$("#swh-mailmap-display-name").val(),display_name_activated:$("#swh-mailmap-display-name-activated").prop("checked")},t.prev=3,t.next=6,(0,o.e_)(i,{"Content-Type":"application/json"},JSON.stringify(a));case 6:c=t.sent,$("#swh-web-modal-html").modal("hide"),(0,o.ry)(c),e.draw(),t.next=18;break;case 12:return t.prev=12,t.t0=t.catch(3),t.next=16,t.t0.text();case 16:u=t.sent,swh.webapp.showModalMessage("Error",u);case 18:case"end":return t.stop()}}),t,null,[[3,12]])})));return function(e){return r.apply(this,arguments)}}())}function l(){u("Add new mailmap",c("Add mailmap"),Urls.profile_mailmap_add())}function s(t){for(var r,n=e.rows().data(),o=0;o<n.length;++o){var a=n[o];if(a.id===t){r=a;break}}u("Update existing mailmap",c("Update mailmap",r.from_email,r.display_name,r.display_name_activated,!0),Urls.profile_mailmap_update())}var p='<i class="mdi mdi-check-bold" aria-hidden="true"></i>',d='<i class="mdi mdi-close-thick" aria-hidden="true"></i>';function f(){$(document).ready((function(){e=$("#swh-mailmaps-table").on("error.dt",(function(e,t,r,n){$("#swh-mailmaps-list-error").text("An error occurred while retrieving the mailmaps list"),console.log(n)})).DataTable({serverSide:!0,ajax:Urls.profile_mailmap_list_datatables(),columns:[{data:"from_email",name:"from_email",render:$.fn.dataTable.render.text()},{data:"from_email_verified",name:"from_email_verified",render:function(e,t,r){return e?p:d},className:"dt-center"},{data:"display_name",name:"display_name",render:$.fn.dataTable.render.text()},{data:"display_name_activated",name:"display_name_activated",render:function(e,t,r){return e?p:d},className:"dt-center"},{data:"last_update_date",name:"last_update_date",render:function(e,t,r){return"display"===t?new Date(e).toLocaleString():e}},{render:function(e,t,r){var n=new Date(r.last_update_date),o=new Date(r.mailmap_last_processing_date);return!o||o<n?d:p},className:"dt-center",orderable:!1},{render:function(e,t,r){return'<button class="btn btn-default"\n                         onclick="swh.mailmap.updateMailmap('+r.id+')">\n                  Edit\n                </button>'},orderable:!1}],ordering:!0,searching:!0,searchDelay:1e3,scrollY:"50vh",scrollCollapse:!0})}))}}(),__webpack_exports__}()}));
//# sourceMappingURL=mailmap.bc51519d9b54299cfe5e.js.map