/*! For license information please see auth.9d2f755f6adf03da929c.js.LICENSE.txt */
!function(t,e){"object"==typeof exports&&"object"==typeof module?module.exports=e():"function"==typeof define&&define.amd?define([],e):"object"==typeof exports?exports.swh=e():(t.swh=t.swh||{},t.swh.auth=e())}(self,(function(){return function(){var t={87757:function(t,e,r){t.exports=r(35666)},59537:function(t,e,r){"use strict";r.d(e,{L3:function(){return a},e_:function(){return i},ry:function(){return o}});r(87757);var n=r(31955);function o(t){if(!t.ok)throw t;return t}function i(t,e,r){return void 0===e&&(e={}),void 0===r&&(r=null),e["X-CSRFToken"]=n.Z.get("csrftoken"),fetch(t,{credentials:"include",headers:e,method:"POST",body:r})}function a(){history.replaceState("",document.title,window.location.pathname+window.location.search)}},35666:function(t){var e=function(t){"use strict";var e,r=Object.prototype,n=r.hasOwnProperty,o=Object.defineProperty||function(t,e,r){t[e]=r.value},i="function"==typeof Symbol?Symbol:{},a=i.iterator||"@@iterator",c=i.asyncIterator||"@@asyncIterator",u=i.toStringTag||"@@toStringTag";function s(t,e,r){return Object.defineProperty(t,e,{value:r,enumerable:!0,configurable:!0,writable:!0}),t[e]}try{s({},"")}catch(t){s=function(t,e,r){return t[e]=r}}function l(t,e,r,n){var i=e&&e.prototype instanceof w?e:w,a=Object.create(i.prototype),c=new R(n||[]);return o(a,"_invoke",{value:T(t,r,c)}),a}function f(t,e,r){try{return{type:"normal",arg:t.call(e,r)}}catch(t){return{type:"throw",arg:t}}}t.wrap=l;var h="suspendedStart",p="suspendedYield",d="executing",v="completed",y={};function w(){}function m(){}function b(){}var g={};s(g,a,(function(){return this}));var k=Object.getPrototypeOf,x=k&&k(k(C([])));x&&x!==r&&n.call(x,a)&&(g=x);var _=b.prototype=w.prototype=Object.create(g);function E(t){["next","throw","return"].forEach((function(e){s(t,e,(function(t){return this._invoke(e,t)}))}))}function L(t,e){function r(o,i,a,c){var u=f(t[o],t,i);if("throw"!==u.type){var s=u.arg,l=s.value;return l&&"object"==typeof l&&n.call(l,"__await")?e.resolve(l.__await).then((function(t){r("next",t,a,c)}),(function(t){r("throw",t,a,c)})):e.resolve(l).then((function(t){s.value=t,a(s)}),(function(t){return r("throw",t,a,c)}))}c(u.arg)}var i;o(this,"_invoke",{value:function(t,n){function o(){return new e((function(e,o){r(t,n,e,o)}))}return i=i?i.then(o,o):o()}})}function T(t,e,r){var n=h;return function(o,i){if(n===d)throw new Error("Generator is already running");if(n===v){if("throw"===o)throw i;return P()}for(r.method=o,r.arg=i;;){var a=r.delegate;if(a){var c=S(a,r);if(c){if(c===y)continue;return c}}if("next"===r.method)r.sent=r._sent=r.arg;else if("throw"===r.method){if(n===h)throw n=v,r.arg;r.dispatchException(r.arg)}else"return"===r.method&&r.abrupt("return",r.arg);n=d;var u=f(t,e,r);if("normal"===u.type){if(n=r.done?v:p,u.arg===y)continue;return{value:u.arg,done:r.done}}"throw"===u.type&&(n=v,r.method="throw",r.arg=u.arg)}}}function S(t,r){var n=r.method,o=t.iterator[n];if(o===e)return r.delegate=null,"throw"===n&&t.iterator.return&&(r.method="return",r.arg=e,S(t,r),"throw"===r.method)||"return"!==n&&(r.method="throw",r.arg=new TypeError("The iterator does not provide a '"+n+"' method")),y;var i=f(o,t.iterator,r.arg);if("throw"===i.type)return r.method="throw",r.arg=i.arg,r.delegate=null,y;var a=i.arg;return a?a.done?(r[t.resultName]=a.value,r.next=t.nextLoc,"return"!==r.method&&(r.method="next",r.arg=e),r.delegate=null,y):a:(r.method="throw",r.arg=new TypeError("iterator result is not an object"),r.delegate=null,y)}function j(t){var e={tryLoc:t[0]};1 in t&&(e.catchLoc=t[1]),2 in t&&(e.finallyLoc=t[2],e.afterLoc=t[3]),this.tryEntries.push(e)}function O(t){var e=t.completion||{};e.type="normal",delete e.arg,t.completion=e}function R(t){this.tryEntries=[{tryLoc:"root"}],t.forEach(j,this),this.reset(!0)}function C(t){if(t){var r=t[a];if(r)return r.call(t);if("function"==typeof t.next)return t;if(!isNaN(t.length)){var o=-1,i=function r(){for(;++o<t.length;)if(n.call(t,o))return r.value=t[o],r.done=!1,r;return r.value=e,r.done=!0,r};return i.next=i}}return{next:P}}function P(){return{value:e,done:!0}}return m.prototype=b,o(_,"constructor",{value:b,configurable:!0}),o(b,"constructor",{value:m,configurable:!0}),m.displayName=s(b,u,"GeneratorFunction"),t.isGeneratorFunction=function(t){var e="function"==typeof t&&t.constructor;return!!e&&(e===m||"GeneratorFunction"===(e.displayName||e.name))},t.mark=function(t){return Object.setPrototypeOf?Object.setPrototypeOf(t,b):(t.__proto__=b,s(t,u,"GeneratorFunction")),t.prototype=Object.create(_),t},t.awrap=function(t){return{__await:t}},E(L.prototype),s(L.prototype,c,(function(){return this})),t.AsyncIterator=L,t.async=function(e,r,n,o,i){void 0===i&&(i=Promise);var a=new L(l(e,r,n,o),i);return t.isGeneratorFunction(r)?a:a.next().then((function(t){return t.done?t.value:a.next()}))},E(_),s(_,u,"Generator"),s(_,a,(function(){return this})),s(_,"toString",(function(){return"[object Generator]"})),t.keys=function(t){var e=Object(t),r=[];for(var n in e)r.push(n);return r.reverse(),function t(){for(;r.length;){var n=r.pop();if(n in e)return t.value=n,t.done=!1,t}return t.done=!0,t}},t.values=C,R.prototype={constructor:R,reset:function(t){if(this.prev=0,this.next=0,this.sent=this._sent=e,this.done=!1,this.delegate=null,this.method="next",this.arg=e,this.tryEntries.forEach(O),!t)for(var r in this)"t"===r.charAt(0)&&n.call(this,r)&&!isNaN(+r.slice(1))&&(this[r]=e)},stop:function(){this.done=!0;var t=this.tryEntries[0].completion;if("throw"===t.type)throw t.arg;return this.rval},dispatchException:function(t){if(this.done)throw t;var r=this;function o(n,o){return c.type="throw",c.arg=t,r.next=n,o&&(r.method="next",r.arg=e),!!o}for(var i=this.tryEntries.length-1;i>=0;--i){var a=this.tryEntries[i],c=a.completion;if("root"===a.tryLoc)return o("end");if(a.tryLoc<=this.prev){var u=n.call(a,"catchLoc"),s=n.call(a,"finallyLoc");if(u&&s){if(this.prev<a.catchLoc)return o(a.catchLoc,!0);if(this.prev<a.finallyLoc)return o(a.finallyLoc)}else if(u){if(this.prev<a.catchLoc)return o(a.catchLoc,!0)}else{if(!s)throw new Error("try statement without catch or finally");if(this.prev<a.finallyLoc)return o(a.finallyLoc)}}}},abrupt:function(t,e){for(var r=this.tryEntries.length-1;r>=0;--r){var o=this.tryEntries[r];if(o.tryLoc<=this.prev&&n.call(o,"finallyLoc")&&this.prev<o.finallyLoc){var i=o;break}}i&&("break"===t||"continue"===t)&&i.tryLoc<=e&&e<=i.finallyLoc&&(i=null);var a=i?i.completion:{};return a.type=t,a.arg=e,i?(this.method="next",this.next=i.finallyLoc,y):this.complete(a)},complete:function(t,e){if("throw"===t.type)throw t.arg;return"break"===t.type||"continue"===t.type?this.next=t.arg:"return"===t.type?(this.rval=this.arg=t.arg,this.method="return",this.next="end"):"normal"===t.type&&e&&(this.next=e),y},finish:function(t){for(var e=this.tryEntries.length-1;e>=0;--e){var r=this.tryEntries[e];if(r.finallyLoc===t)return this.complete(r.completion,r.afterLoc),O(r),y}},catch:function(t){for(var e=this.tryEntries.length-1;e>=0;--e){var r=this.tryEntries[e];if(r.tryLoc===t){var n=r.completion;if("throw"===n.type){var o=n.arg;O(r)}return o}}throw new Error("illegal catch attempt")},delegateYield:function(t,r,n){return this.delegate={iterator:C(t),resultName:r,nextLoc:n},"next"===this.method&&(this.arg=e),y}},t}(t.exports);try{regeneratorRuntime=e}catch(t){"object"==typeof globalThis?globalThis.regeneratorRuntime=e:Function("r","regeneratorRuntime = r")(e)}},15861:function(t,e,r){"use strict";function n(t,e,r,n,o,i,a){try{var c=t[i](a),u=c.value}catch(t){return void r(t)}c.done?e(u):Promise.resolve(u).then(n,o)}function o(t){return function(){var e=this,r=arguments;return new Promise((function(o,i){var a=t.apply(e,r);function c(t){n(a,o,i,c,u,"next",t)}function u(t){n(a,o,i,c,u,"throw",t)}c(void 0)}))}}r.d(e,{Z:function(){return o}})},31955:function(t,e){"use strict";function r(t){for(var e=1;e<arguments.length;e++){var r=arguments[e];for(var n in r)t[n]=r[n]}return t}var n=function t(e,n){function o(t,o,i){if("undefined"!=typeof document){"number"==typeof(i=r({},n,i)).expires&&(i.expires=new Date(Date.now()+864e5*i.expires)),i.expires&&(i.expires=i.expires.toUTCString()),t=encodeURIComponent(t).replace(/%(2[346B]|5E|60|7C)/g,decodeURIComponent).replace(/[()]/g,escape);var a="";for(var c in i)i[c]&&(a+="; "+c,!0!==i[c]&&(a+="="+i[c].split(";")[0]));return document.cookie=t+"="+e.write(o,t)+a}}return Object.create({set:o,get:function(t){if("undefined"!=typeof document&&(!arguments.length||t)){for(var r=document.cookie?document.cookie.split("; "):[],n={},o=0;o<r.length;o++){var i=r[o].split("="),a=i.slice(1).join("=");try{var c=decodeURIComponent(i[0]);if(n[c]=e.read(a,c),t===c)break}catch(t){}}return t?n[t]:n}},remove:function(t,e){o(t,"",r({},e,{expires:-1}))},withAttributes:function(e){return t(this.converter,r({},this.attributes,e))},withConverter:function(e){return t(r({},this.converter,e),this.attributes)}},{attributes:{value:Object.freeze(n)},converter:{value:Object.freeze(e)}})}({read:function(t){return'"'===t[0]&&(t=t.slice(1,-1)),t.replace(/(%[\dA-F]{2})+/gi,decodeURIComponent)},write:function(t){return encodeURIComponent(t).replace(/%(2[346BF]|3[AC-F]|40|5[BDE]|60|7[BCD])/g,decodeURIComponent)}},{path:"/"});e.Z=n}},e={};function r(n){var o=e[n];if(void 0!==o)return o.exports;var i=e[n]={exports:{}};return t[n](i,i.exports,r),i.exports}r.n=function(t){var e=t&&t.__esModule?function(){return t.default}:function(){return t};return r.d(e,{a:e}),e},r.d=function(t,e){for(var n in e)r.o(e,n)&&!r.o(t,n)&&Object.defineProperty(t,n,{enumerable:!0,get:e[n]})},r.g=function(){if("object"==typeof globalThis)return globalThis;try{return this||new Function("return this")()}catch(t){if("object"==typeof window)return window}}(),r.o=function(t,e){return Object.prototype.hasOwnProperty.call(t,e)},r.r=function(t){"undefined"!=typeof Symbol&&Symbol.toStringTag&&Object.defineProperty(t,Symbol.toStringTag,{value:"Module"}),Object.defineProperty(t,"__esModule",{value:!0})};var n,o={};return(n="undefined"!=typeof window?window:void 0!==r.g?r.g:"undefined"!=typeof self?self:{}).SENTRY_RELEASE={id:"0.2.21"},n.SENTRY_RELEASES=n.SENTRY_RELEASES||{},n.SENTRY_RELEASES["swh-webapp@swh"]={id:"0.2.21"},function(){"use strict";r.r(o),r.d(o,{applyTokenAction:function(){return v},initProfilePage:function(){return y}});var t,e=r(15861),n=r(87757),i=r.n(n),a=r(59537);function c(t){return'<p id="swh-token-error-message" class="mt-3 swh-token-form-message">'+t+"</p>"}function u(){window.location=Urls.oidc_generate_bearer_token()}function s(t){return l.apply(this,arguments)}function l(){return(l=(0,e.Z)(i().mark((function t(e){var r,n,o,u,s,l;return i().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:return r={token_id:e},t.prev=1,t.next=4,(0,a.e_)(Urls.oidc_get_bearer_token(),{},JSON.stringify(r));case 4:return n=t.sent,(0,a.ry)(n),t.next=8,n.text();case 8:o=t.sent,u='<p>Below is your token.</p>\n      <pre id="swh-bearer-token" class="mt-3">'+o+"</pre>",swh.webapp.showModalHtml("Display bearer token",u),t.next=21;break;case 13:return t.prev=13,t.t0=t.catch(1),t.next=17,t.t0.text();case 17:s=t.sent,l="Internal server error.",400===t.t0.status&&(l=s),swh.webapp.showModalHtml("Display bearer token",c(l));case 21:case"end":return t.stop()}}),t,null,[[1,13]])})))).apply(this,arguments)}function f(t){return h.apply(this,arguments)}function h(){return(h=(0,e.Z)(i().mark((function e(r){var n,o;return i().wrap((function(e){for(;;)switch(e.prev=e.next){case 0:return n={token_ids:r},e.prev=1,e.next=4,(0,a.e_)(Urls.oidc_revoke_bearer_tokens(),{},JSON.stringify(n));case 4:o=e.sent,(0,a.ry)(o),$("#swh-token-form-submit").prop("disabled",!0),$("#swh-token-form-message").html('<p id="swh-token-success-message" class="mt-3 swh-token-form-message">'+("Bearer token"+(r.length>1?"s":"")+" successfully revoked.")+"</p>"),t.draw(),e.next=14;break;case 11:e.prev=11,e.t0=e.catch(1),$("#swh-token-form-message").html(c("Internal server error."));case 14:case"end":return e.stop()}}),e,null,[[1,11]])})))).apply(this,arguments)}function p(t){f([t])}function d(){for(var e=[],r=t.rows().data(),n=0;n<r.length;++n)e.push(r[n].id);f(e)}function v(t,e){var r,n,o={display:{submitCallback:s},generate:{modalTitle:"Bearer token generation",infoText:"Click on the button to generate the token. You will be redirected to Software Heritage Authentication Service and might be asked to enter your password again.",buttonText:"Generate token",submitCallback:u},revoke:{modalTitle:"Revoke bearer token",infoText:"Click on the button to revoke the token.",buttonText:"Revoke token",submitCallback:p},revokeAll:{modalTitle:"Revoke all bearer tokens",infoText:"Click on the button to revoke all tokens.",buttonText:"Revoke tokens",submitCallback:d}};if(o[t])if("display"!==t){var i=(r=o[t].infoText,n=o[t].buttonText,'<form id="swh-token-form" class="text-center">\n      <p id="swh-token-form-text">'+r+'</p>\n      <input id="swh-token-form-submit" type="submit" value="'+n+'">\n      <div id="swh-token-form-message"></div>\n    </form>');swh.webapp.showModalHtml(o[t].modalTitle,i),$("#swh-token-form").submit((function(r){r.preventDefault(),r.stopPropagation(),o[t].submitCallback(e)}))}else o[t].submitCallback(e)}function y(){$(document).ready((function(){t=$("#swh-bearer-tokens-table").on("error.dt",(function(t,e,r,n){$("#swh-origin-save-request-list-error").text("An error occurred while retrieving the tokens list"),console.log(n)})).DataTable({serverSide:!0,ajax:Urls.oidc_list_bearer_tokens(),columns:[{data:"creation_date",name:"creation_date",render:function(t,e,r){return"display"===e?new Date(t).toLocaleString():t}},{render:function(t,e,r){return'<button class="btn btn-default"\n                         onclick="swh.auth.applyTokenAction(\'display\', '+r.id+')">\n                  Display token\n                </button>\n                <button class="btn btn-default"\n                        onclick="swh.auth.applyTokenAction(\'revoke\', '+r.id+')">\n                  Revoke token\n                </button>'}}],ordering:!1,searching:!1,scrollY:"50vh",scrollCollapse:!0}),$("#swh-oidc-profile-tokens-tab").on("shown.bs.tab",(function(){t.draw(),window.location.hash="#tokens"})),$("#swh-oidc-profile-account-tab").on("shown.bs.tab",(function(){(0,a.L3)()})),"#tokens"===window.location.hash&&$('.nav-tabs a[href="#swh-oidc-profile-tokens"]').tab("show")}))}}(),o}()}));
//# sourceMappingURL=auth.9d2f755f6adf03da929c.js.map