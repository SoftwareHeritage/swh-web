/*! For license information please see auth.640a09c0fe3c1bc8a893.js.LICENSE.txt */
!function(){try{var t="undefined"!=typeof window?window:"undefined"!=typeof global?global:"undefined"!=typeof self?self:{},e=(new Error).stack;e&&(t._sentryDebugIds=t._sentryDebugIds||{},t._sentryDebugIds[e]="4e39cfe4-451e-4a4b-8550-eb42b0d7b163",t._sentryDebugIdIdentifier="sentry-dbid-4e39cfe4-451e-4a4b-8550-eb42b0d7b163")}catch(t){}}();var _global="undefined"!=typeof window?window:"undefined"!=typeof global?global:"undefined"!=typeof self?self:{};_global.SENTRY_RELEASE={id:"0.3.0"},function(t,e){"object"==typeof exports&&"object"==typeof module?module.exports=e():"function"==typeof define&&define.amd?define([],e):"object"==typeof exports?exports.swh=e():(t.swh=t.swh||{},t.swh.auth=e())}(self,(function(){return function(){var t={59537:function(t,e,r){"use strict";r.d(e,{L3:function(){return a},e_:function(){return i},ry:function(){return o}});r(64687);var n=r(31955);function o(t){if(!t.ok)throw t;return t}function i(t,e,r){return void 0===e&&(e={}),void 0===r&&(r=null),e["X-CSRFToken"]=n.Z.get("csrftoken"),fetch(t,{credentials:"include",headers:e,method:"POST",body:r})}function a(){history.replaceState("",document.title,window.location.pathname+window.location.search)}},17061:function(t,e,r){var n=r(18698).default;function o(){"use strict";t.exports=o=function(){return r},t.exports.__esModule=!0,t.exports.default=t.exports;var e,r={},i=Object.prototype,a=i.hasOwnProperty,c=Object.defineProperty||function(t,e,r){t[e]=r.value},u="function"==typeof Symbol?Symbol:{},s=u.iterator||"@@iterator",l=u.asyncIterator||"@@asyncIterator",f=u.toStringTag||"@@toStringTag";function h(t,e,r){return Object.defineProperty(t,e,{value:r,enumerable:!0,configurable:!0,writable:!0}),t[e]}try{h({},"")}catch(e){h=function(t,e,r){return t[e]=r}}function p(t,e,r,n){var o=e&&e.prototype instanceof g?e:g,i=Object.create(o.prototype),a=new I(n||[]);return c(i,"_invoke",{value:O(t,r,a)}),i}function d(t,e,r){try{return{type:"normal",arg:t.call(e,r)}}catch(t){return{type:"throw",arg:t}}}r.wrap=p;var y="suspendedStart",v="suspendedYield",b="executing",m="completed",w={};function g(){}function k(){}function x(){}var _={};h(_,s,(function(){return this}));var L=Object.getPrototypeOf,E=L&&L(L(D([])));E&&E!==i&&a.call(E,s)&&(_=E);var T=x.prototype=g.prototype=Object.create(_);function S(t){["next","throw","return"].forEach((function(e){h(t,e,(function(t){return this._invoke(e,t)}))}))}function j(t,e){function r(o,i,c,u){var s=d(t[o],t,i);if("throw"!==s.type){var l=s.arg,f=l.value;return f&&"object"==n(f)&&a.call(f,"__await")?e.resolve(f.__await).then((function(t){r("next",t,c,u)}),(function(t){r("throw",t,c,u)})):e.resolve(f).then((function(t){l.value=t,c(l)}),(function(t){return r("throw",t,c,u)}))}u(s.arg)}var o;c(this,"_invoke",{value:function(t,n){function i(){return new e((function(e,o){r(t,n,e,o)}))}return o=o?o.then(i,i):i()}})}function O(t,r,n){var o=y;return function(i,a){if(o===b)throw new Error("Generator is already running");if(o===m){if("throw"===i)throw a;return{value:e,done:!0}}for(n.method=i,n.arg=a;;){var c=n.delegate;if(c){var u=C(c,n);if(u){if(u===w)continue;return u}}if("next"===n.method)n.sent=n._sent=n.arg;else if("throw"===n.method){if(o===y)throw o=m,n.arg;n.dispatchException(n.arg)}else"return"===n.method&&n.abrupt("return",n.arg);o=b;var s=d(t,r,n);if("normal"===s.type){if(o=n.done?m:v,s.arg===w)continue;return{value:s.arg,done:n.done}}"throw"===s.type&&(o=m,n.method="throw",n.arg=s.arg)}}}function C(t,r){var n=r.method,o=t.iterator[n];if(o===e)return r.delegate=null,"throw"===n&&t.iterator.return&&(r.method="return",r.arg=e,C(t,r),"throw"===r.method)||"return"!==n&&(r.method="throw",r.arg=new TypeError("The iterator does not provide a '"+n+"' method")),w;var i=d(o,t.iterator,r.arg);if("throw"===i.type)return r.method="throw",r.arg=i.arg,r.delegate=null,w;var a=i.arg;return a?a.done?(r[t.resultName]=a.value,r.next=t.nextLoc,"return"!==r.method&&(r.method="next",r.arg=e),r.delegate=null,w):a:(r.method="throw",r.arg=new TypeError("iterator result is not an object"),r.delegate=null,w)}function P(t){var e={tryLoc:t[0]};1 in t&&(e.catchLoc=t[1]),2 in t&&(e.finallyLoc=t[2],e.afterLoc=t[3]),this.tryEntries.push(e)}function R(t){var e=t.completion||{};e.type="normal",delete e.arg,t.completion=e}function I(t){this.tryEntries=[{tryLoc:"root"}],t.forEach(P,this),this.reset(!0)}function D(t){if(t||""===t){var r=t[s];if(r)return r.call(t);if("function"==typeof t.next)return t;if(!isNaN(t.length)){var o=-1,i=function r(){for(;++o<t.length;)if(a.call(t,o))return r.value=t[o],r.done=!1,r;return r.value=e,r.done=!0,r};return i.next=i}}throw new TypeError(n(t)+" is not iterable")}return k.prototype=x,c(T,"constructor",{value:x,configurable:!0}),c(x,"constructor",{value:k,configurable:!0}),k.displayName=h(x,f,"GeneratorFunction"),r.isGeneratorFunction=function(t){var e="function"==typeof t&&t.constructor;return!!e&&(e===k||"GeneratorFunction"===(e.displayName||e.name))},r.mark=function(t){return Object.setPrototypeOf?Object.setPrototypeOf(t,x):(t.__proto__=x,h(t,f,"GeneratorFunction")),t.prototype=Object.create(T),t},r.awrap=function(t){return{__await:t}},S(j.prototype),h(j.prototype,l,(function(){return this})),r.AsyncIterator=j,r.async=function(t,e,n,o,i){void 0===i&&(i=Promise);var a=new j(p(t,e,n,o),i);return r.isGeneratorFunction(e)?a:a.next().then((function(t){return t.done?t.value:a.next()}))},S(T),h(T,f,"Generator"),h(T,s,(function(){return this})),h(T,"toString",(function(){return"[object Generator]"})),r.keys=function(t){var e=Object(t),r=[];for(var n in e)r.push(n);return r.reverse(),function t(){for(;r.length;){var n=r.pop();if(n in e)return t.value=n,t.done=!1,t}return t.done=!0,t}},r.values=D,I.prototype={constructor:I,reset:function(t){if(this.prev=0,this.next=0,this.sent=this._sent=e,this.done=!1,this.delegate=null,this.method="next",this.arg=e,this.tryEntries.forEach(R),!t)for(var r in this)"t"===r.charAt(0)&&a.call(this,r)&&!isNaN(+r.slice(1))&&(this[r]=e)},stop:function(){this.done=!0;var t=this.tryEntries[0].completion;if("throw"===t.type)throw t.arg;return this.rval},dispatchException:function(t){if(this.done)throw t;var r=this;function n(n,o){return c.type="throw",c.arg=t,r.next=n,o&&(r.method="next",r.arg=e),!!o}for(var o=this.tryEntries.length-1;o>=0;--o){var i=this.tryEntries[o],c=i.completion;if("root"===i.tryLoc)return n("end");if(i.tryLoc<=this.prev){var u=a.call(i,"catchLoc"),s=a.call(i,"finallyLoc");if(u&&s){if(this.prev<i.catchLoc)return n(i.catchLoc,!0);if(this.prev<i.finallyLoc)return n(i.finallyLoc)}else if(u){if(this.prev<i.catchLoc)return n(i.catchLoc,!0)}else{if(!s)throw new Error("try statement without catch or finally");if(this.prev<i.finallyLoc)return n(i.finallyLoc)}}}},abrupt:function(t,e){for(var r=this.tryEntries.length-1;r>=0;--r){var n=this.tryEntries[r];if(n.tryLoc<=this.prev&&a.call(n,"finallyLoc")&&this.prev<n.finallyLoc){var o=n;break}}o&&("break"===t||"continue"===t)&&o.tryLoc<=e&&e<=o.finallyLoc&&(o=null);var i=o?o.completion:{};return i.type=t,i.arg=e,o?(this.method="next",this.next=o.finallyLoc,w):this.complete(i)},complete:function(t,e){if("throw"===t.type)throw t.arg;return"break"===t.type||"continue"===t.type?this.next=t.arg:"return"===t.type?(this.rval=this.arg=t.arg,this.method="return",this.next="end"):"normal"===t.type&&e&&(this.next=e),w},finish:function(t){for(var e=this.tryEntries.length-1;e>=0;--e){var r=this.tryEntries[e];if(r.finallyLoc===t)return this.complete(r.completion,r.afterLoc),R(r),w}},catch:function(t){for(var e=this.tryEntries.length-1;e>=0;--e){var r=this.tryEntries[e];if(r.tryLoc===t){var n=r.completion;if("throw"===n.type){var o=n.arg;R(r)}return o}}throw new Error("illegal catch attempt")},delegateYield:function(t,r,n){return this.delegate={iterator:D(t),resultName:r,nextLoc:n},"next"===this.method&&(this.arg=e),w}},r}t.exports=o,t.exports.__esModule=!0,t.exports.default=t.exports},18698:function(t){function e(r){return t.exports=e="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},t.exports.__esModule=!0,t.exports.default=t.exports,e(r)}t.exports=e,t.exports.__esModule=!0,t.exports.default=t.exports},64687:function(t,e,r){var n=r(17061)();t.exports=n;try{regeneratorRuntime=n}catch(t){"object"==typeof globalThis?globalThis.regeneratorRuntime=n:Function("r","regeneratorRuntime = r")(n)}},15861:function(t,e,r){"use strict";function n(t,e,r,n,o,i,a){try{var c=t[i](a),u=c.value}catch(t){return void r(t)}c.done?e(u):Promise.resolve(u).then(n,o)}function o(t){return function(){var e=this,r=arguments;return new Promise((function(o,i){var a=t.apply(e,r);function c(t){n(a,o,i,c,u,"next",t)}function u(t){n(a,o,i,c,u,"throw",t)}c(void 0)}))}}r.d(e,{Z:function(){return o}})},31955:function(t,e,r){"use strict";function n(t){for(var e=1;e<arguments.length;e++){var r=arguments[e];for(var n in r)t[n]=r[n]}return t}r.d(e,{Z:function(){return o}});var o=function t(e,r){function o(t,o,i){if("undefined"!=typeof document){"number"==typeof(i=n({},r,i)).expires&&(i.expires=new Date(Date.now()+864e5*i.expires)),i.expires&&(i.expires=i.expires.toUTCString()),t=encodeURIComponent(t).replace(/%(2[346B]|5E|60|7C)/g,decodeURIComponent).replace(/[()]/g,escape);var a="";for(var c in i)i[c]&&(a+="; "+c,!0!==i[c]&&(a+="="+i[c].split(";")[0]));return document.cookie=t+"="+e.write(o,t)+a}}return Object.create({set:o,get:function(t){if("undefined"!=typeof document&&(!arguments.length||t)){for(var r=document.cookie?document.cookie.split("; "):[],n={},o=0;o<r.length;o++){var i=r[o].split("="),a=i.slice(1).join("=");try{var c=decodeURIComponent(i[0]);if(n[c]=e.read(a,c),t===c)break}catch(t){}}return t?n[t]:n}},remove:function(t,e){o(t,"",n({},e,{expires:-1}))},withAttributes:function(e){return t(this.converter,n({},this.attributes,e))},withConverter:function(e){return t(n({},this.converter,e),this.attributes)}},{attributes:{value:Object.freeze(r)},converter:{value:Object.freeze(e)}})}({read:function(t){return'"'===t[0]&&(t=t.slice(1,-1)),t.replace(/(%[\dA-F]{2})+/gi,decodeURIComponent)},write:function(t){return encodeURIComponent(t).replace(/%(2[346BF]|3[AC-F]|40|5[BDE]|60|7[BCD])/g,decodeURIComponent)}},{path:"/"})}},e={};function r(n){var o=e[n];if(void 0!==o)return o.exports;var i=e[n]={exports:{}};return t[n](i,i.exports,r),i.exports}r.n=function(t){var e=t&&t.__esModule?function(){return t.default}:function(){return t};return r.d(e,{a:e}),e},r.d=function(t,e){for(var n in e)r.o(e,n)&&!r.o(t,n)&&Object.defineProperty(t,n,{enumerable:!0,get:e[n]})},r.o=function(t,e){return Object.prototype.hasOwnProperty.call(t,e)},r.r=function(t){"undefined"!=typeof Symbol&&Symbol.toStringTag&&Object.defineProperty(t,Symbol.toStringTag,{value:"Module"}),Object.defineProperty(t,"__esModule",{value:!0})};var n={};return function(){"use strict";r.r(n),r.d(n,{applyTokenAction:function(){return y},initProfilePage:function(){return v}});var t,e=r(15861),o=r(64687),i=r.n(o),a=r(59537);function c(t){return'<p id="swh-token-error-message" class="mt-3 swh-token-form-message">'+t+"</p>"}function u(){window.location=Urls.oidc_generate_bearer_token()}function s(t){return l.apply(this,arguments)}function l(){return(l=(0,e.Z)(i().mark((function t(e){var r,n,o,u,s,l;return i().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:return r={token_id:e},t.prev=1,t.next=4,(0,a.e_)(Urls.oidc_get_bearer_token(),{},JSON.stringify(r));case 4:return n=t.sent,(0,a.ry)(n),t.next=8,n.text();case 8:o=t.sent,u='<p>Below is your token.</p>\n      <pre id="swh-bearer-token" class="mt-3">'+o+"</pre>",swh.webapp.showModalHtml("Display bearer token",u),t.next=21;break;case 13:return t.prev=13,t.t0=t.catch(1),t.next=17,t.t0.text();case 17:s=t.sent,l="Internal server error.",400===t.t0.status&&(l=s),swh.webapp.showModalHtml("Display bearer token",c(l));case 21:case"end":return t.stop()}}),t,null,[[1,13]])})))).apply(this,arguments)}function f(t){return h.apply(this,arguments)}function h(){return(h=(0,e.Z)(i().mark((function e(r){var n,o;return i().wrap((function(e){for(;;)switch(e.prev=e.next){case 0:return n={token_ids:r},e.prev=1,e.next=4,(0,a.e_)(Urls.oidc_revoke_bearer_tokens(),{},JSON.stringify(n));case 4:o=e.sent,(0,a.ry)(o),$("#swh-token-form-submit").prop("disabled",!0),$("#swh-token-form-message").html('<p id="swh-token-success-message" class="mt-3 swh-token-form-message">'+("Bearer token"+(r.length>1?"s":"")+" successfully revoked.")+"</p>"),t.draw(),e.next=14;break;case 11:e.prev=11,e.t0=e.catch(1),$("#swh-token-form-message").html(c("Internal server error."));case 14:case"end":return e.stop()}}),e,null,[[1,11]])})))).apply(this,arguments)}function p(t){f([t])}function d(){for(var e=[],r=t.rows().data(),n=0;n<r.length;++n)e.push(r[n].id);f(e)}function y(t,e){var r,n,o={display:{submitCallback:s},generate:{modalTitle:"Bearer token generation",infoText:"Click on the button to generate the token. You will be redirected to Software Heritage Authentication Service and might be asked to enter your password again.",buttonText:"Generate token",submitCallback:u},revoke:{modalTitle:"Revoke bearer token",infoText:"Click on the button to revoke the token.",buttonText:"Revoke token",submitCallback:p},revokeAll:{modalTitle:"Revoke all bearer tokens",infoText:"Click on the button to revoke all tokens.",buttonText:"Revoke tokens",submitCallback:d}};if(o[t])if("display"!==t){var i=(r=o[t].infoText,n=o[t].buttonText,'<form id="swh-token-form" class="text-center">\n      <p id="swh-token-form-text">'+r+'</p>\n      <input id="swh-token-form-submit" type="submit" value="'+n+'">\n      <div id="swh-token-form-message"></div>\n    </form>');swh.webapp.showModalHtml(o[t].modalTitle,i),$("#swh-token-form").submit((function(r){r.preventDefault(),r.stopPropagation(),o[t].submitCallback(e)}))}else o[t].submitCallback(e)}function v(){$(document).ready((function(){t=$("#swh-bearer-tokens-table").on("error.dt",(function(t,e,r,n){$("#swh-origin-save-request-list-error").text("An error occurred while retrieving the tokens list"),console.log(n)})).DataTable({serverSide:!0,ajax:Urls.oidc_list_bearer_tokens(),columns:[{data:"creation_date",name:"creation_date",render:function(t,e,r){return"display"===e?new Date(t).toLocaleString():t}},{render:function(t,e,r){return'<button class="btn btn-default"\n                         onclick="swh.auth.applyTokenAction(\'display\', '+r.id+')">\n                  Display token\n                </button>\n                <button class="btn btn-default"\n                        onclick="swh.auth.applyTokenAction(\'revoke\', '+r.id+')">\n                  Revoke token\n                </button>'}}],ordering:!1,searching:!1,scrollY:"50vh",scrollCollapse:!0}),$("#swh-oidc-profile-tokens-tab").on("shown.bs.tab",(function(){t.draw(),window.location.hash="#tokens"})),$("#swh-oidc-profile-account-tab").on("shown.bs.tab",(function(){(0,a.L3)()})),"#tokens"===window.location.hash&&$('.nav-tabs a[href="#swh-oidc-profile-tokens"]').tab("show")}))}}(),n}()}));
//# sourceMappingURL=auth.640a09c0fe3c1bc8a893.js.map