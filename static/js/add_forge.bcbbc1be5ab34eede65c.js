/*! For license information please see add_forge.bcbbc1be5ab34eede65c.js.LICENSE.txt */
!function(e,t){"object"==typeof exports&&"object"==typeof module?module.exports=t():"function"==typeof define&&define.amd?define([],t):"object"==typeof exports?exports.swh=t():(e.swh=e.swh||{},e.swh.add_forge=t())}(self,(function(){return function(){var __webpack_modules__={87757:function(e,t,n){e.exports=n(35666)},7200:function(e,t,n){"use strict";n.d(t,{T:function(){return f},x:function(){return _}});var r,o=n(15861),a=n(87757),i=n.n(a),s=n(59537),u=n(39449),c=n.n(u),d=n(86515),p="swh-add-forge-user-filter",l=c()({inputId:p,checked:!0});function f(){$(document).ready((function(){$("#requestCreateForm").submit(function(){var e=(0,o.Z)(i().mark((function e(t){var n,o,a;return i().wrap((function(e){for(;;)switch(e.prev=e.next){case 0:return t.preventDefault(),e.prev=1,e.next=4,(0,s.e_)($(this).attr("action"),{"Content-Type":"application/x-www-form-urlencoded"},$(this).serialize());case 4:n=e.sent,(0,s.ry)(n),$("#userMessageDetail").empty(),$("#userMessage").text("Your request has been submitted"),$("#userMessage").removeClass("badge-danger"),$("#userMessage").addClass("badge-success"),r.draw(),e.next=23;break;case 13:return e.prev=13,e.t0=e.catch(1),$("#userMessageDetail").empty(),e.next=18,e.t0.json();case 18:a=e.sent,o=409===e.t0.status?a:(0,s.DK)(a,"An unknown error occurred during the request creation"),$("#userMessage").text(o),$("#userMessage").removeClass("badge-success"),$("#userMessage").addClass("badge-danger");case 23:case"end":return e.stop()}}),e,this,[[1,13]])})));return function(t){return e.apply(this,arguments)}}()),_()}))}function _(){r=$("#add-forge-request-browse").on("error.dt",(function(e,t,n,r){$("#add-forge-browse-request-error").text(r)})).DataTable({serverSide:!0,processing:!0,language:{processing:'<img src="'+d.XC+'"></img>'},retrieve:!0,searching:!0,info:!1,dom:'<"row"<"col-sm-3"l><"col-sm-6 text-left user-requests-filter"><"col-sm-3"f>><"row"<"col-sm-12"tr>><"row"<"col-sm-5"i><"col-sm-7"p>>',ajax:{url:Urls.add_forge_request_list_datatables(),data:function(e){var t=$("#"+p).prop("checked");swh.webapp.isUserLoggedIn()&&(void 0===t||t)&&(e.user_requests_only="1")}},fnInitComplete:function(){swh.webapp.isUserLoggedIn()&&($("div.user-requests-filter").html(l),$("#"+p).on("change",(function(){r.draw()})))},columns:[{data:"submission_date",name:"submission_date",render:s.Jp},{data:"forge_type",name:"forge_type",render:$.fn.dataTable.render.text()},{data:"forge_url",name:"forge_url",render:function(e,t,n){if("display"===t){var r="",o=$.fn.dataTable.render.text().display(e);return r+=o,r+='&nbsp;<a href="'+o+'" target="_blank" rel="noopener noreferrer"><i class="mdi mdi-open-in-new" aria-hidden="true"></i></a>'}return e}},{data:"status",name:"status",render:function(e,t,n,r){return swh.add_forge.formatRequestStatusName(e)}}]})}},98955:function(e,t,n){"use strict";n.d(t,{f:function(){return s},y:function(){return u}});var r=n(15861),o=n(87757),a=n.n(o),i=n(59537);function s(){u()}function u(){return c.apply(this,arguments)}function c(){return(c=(0,r.Z)(a().mark((function e(){return a().wrap((function(e){for(;;)switch(e.prev=e.next){case 0:$("#swh-add-forge-now-moderation-list").on("error.dt",(function(e,t,n,r){$("#swh-add-forge-now-moderation-list-error").text(r)})).DataTable({serverSide:!0,processing:!0,searching:!0,info:!1,dom:'<<"d-flex justify-content-between align-items-center"f<"#list-exclude">l>rt<"bottom"ip>>',ajax:{url:Urls.add_forge_request_list_datatables()},columns:[{data:"id",name:"id",render:function(e,t,n,r){return"<a href="+Urls.add_forge_now_request_dashboard(e)+">"+e+"</a>"}},{data:"submission_date",name:"submission_date",render:i.Jp},{data:"forge_type",name:"forge_type",render:$.fn.dataTable.render.text()},{data:"forge_url",name:"forge_url",render:$.fn.dataTable.render.text()},{data:"status",name:"status",render:function(e,t,n,r){return swh.add_forge.formatRequestStatusName(e)}}]});case 1:case"end":return e.stop()}}),e)})))).apply(this,arguments)}},90668:function(e,t,n){"use strict";n.d(t,{H:function(){return m},q:function(){return l}});var r,o=n(15861),a=n(87757),i=n.n(a),s=n(59537),u=n(46717),c=n.n(u),d=n(16756),p=n.n(d);function l(e){$(document).ready((function(){f(e),$("#contactForgeAdmin").click((function(e){var t,n,o,a;t=$("#contactForgeAdmin").attr("emailTo"),n=$("#contactForgeAdmin").attr("emailSubject"),o=c()({forgeUrl:r.forge_url}).trim().replace(/\n/g,"%0D%0A"),(a=window.open("","_blank","",!0)).location.href="mailto: "+t+"?subject="+n+"&body="+o,a.focus()})),$("#updateRequestForm").submit(function(){var t=(0,o.Z)(i().mark((function t(n){var r;return i().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:return n.preventDefault(),t.prev=1,t.next=4,(0,s.e_)($(this).attr("action"),{"Content-Type":"application/x-www-form-urlencoded"},$(this).serialize());case 4:r=t.sent,(0,s.ry)(r),$("#userMessage").text("The request status has been updated "),$("#userMessage").removeClass("badge-danger"),$("#userMessage").addClass("badge-success"),f(e),t.next=17;break;case 12:t.prev=12,t.t0=t.catch(1),$("#userMessage").text("Sorry; Updating the request failed"),$("#userMessage").removeClass("badge-success"),$("#userMessage").addClass("badge-danger");case 17:case"end":return t.stop()}}),t,this,[[1,12]])})));return function(e){return t.apply(this,arguments)}}())}))}function f(e){return _.apply(this,arguments)}function _(){return(_=(0,o.Z)(i().mark((function e(t){var n,o;return i().wrap((function(e){for(;;)switch(e.prev=e.next){case 0:return e.prev=0,e.next=3,fetch(Urls.api_1_add_forge_request_get(t));case 3:return n=e.sent,(0,s.ry)(n),e.next=7,n.json();case 7:o=e.sent,r=o.request,$("#requestStatus").text(swh.add_forge.formatRequestStatusName(r.status)),$("#requestType").text(r.forge_type),$("#requestURL").text(r.forge_url),$("#requestContactName").text(r.forge_contact_name),$("#requestContactConsent").text(r.submitter_forward_username),$("#requestContactEmail").text(r.forge_contact_email),$("#submitterMessage").text(r.forge_contact_comment),$("#updateComment").val(""),$("#contactForgeAdmin").attr("emailTo",r.forge_contact_email),$("#contactForgeAdmin").attr("emailSubject","[swh-add_forge_now] Request "+r.id),h(o.history),m(r.status),e.next=27;break;case 23:e.prev=23,e.t0=e.catch(0),$("#fetchError").removeClass("d-none"),$("#requestDetails").addClass("d-none");case 27:case"end":return e.stop()}}),e,null,[[0,23]])})))).apply(this,arguments)}function h(e){$("#requestHistory").children().remove(),e.forEach((function(e,t){var n=p()({event:e,index:t,getHumanReadableDate:s.Jp});$("#requestHistory").append(n)}))}function m(e){var t={PENDING:["WAITING_FOR_FEEDBACK","REJECTED","SUSPENDED"],WAITING_FOR_FEEDBACK:["FEEDBACK_TO_HANDLE"],FEEDBACK_TO_HANDLE:["WAITING_FOR_FEEDBACK","ACCEPTED","REJECTED","SUSPENDED"],ACCEPTED:["SCHEDULED"],SCHEDULED:["FIRST_LISTING_DONE","FIRST_ORIGIN_LOADED"],FIRST_LISTING_DONE:["FIRST_ORIGIN_LOADED"],FIRST_ORIGIN_LOADED:[],REJECTED:[],SUSPENDED:["PENDING"],DENIED:[]}[e];$("#decisionOptions").children().remove(),t.forEach((function(e,t){var n=swh.add_forge.formatRequestStatusName(e);$("#decisionOptions").append('<option value="'+e+'">'+n+"</option>")})),$("#decisionOptions").append("<option hidden disabled selected value> -- Add a comment -- </option>")}},86515:function(e,t,n){"use strict";n.d(t,{XC:function(){return r}});var r=(0,n(59537).TT)("img/swh-spinner.gif")},59537:function(e,t,n){"use strict";n.d(t,{DK:function(){return a},Jp:function(){return u},TT:function(){return i},e_:function(){return s},ry:function(){return o}});n(87757);var r=n(31955);function o(e){if(!e.ok)throw e;return e}function a(e,t){var n="";try{var r=JSON.parse(e.reason);Object.entries(r).forEach((function(e,t){var r=e[0],o=e[1][0];n+="\n"+r+": "+o}))}catch(t){n=e.reason}return n?"Error: "+n:t}function i(e){return"/static/"+e}function s(e,t,n){return void 0===t&&(t={}),void 0===n&&(n=null),t["X-CSRFToken"]=r.Z.get("csrftoken"),fetch(e,{credentials:"include",headers:t,method:"POST",body:n})}function u(e){return new Date(e).toLocaleString()}},16756:function(module){module.exports=function anonymous(locals,escapeFn,include,rethrow){escapeFn=escapeFn||function(e){return null==e?"":String(e).replace(_MATCH_HTML,encode_char)};var _ENCODE_HTML_RULES={"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&#34;","'":"&#39;"},_MATCH_HTML=/[&<>'"]/g;function encode_char(e){return _ENCODE_HTML_RULES[e]||e}var __output="";function __append(e){null!=e&&(__output+=e)}with(locals||{})__append('\n<div class="history-item">\n  <div class="card border-dark">\n    <div class="card-header" id="historyItem'),__append(escapeFn(index)),__append('}">\n      <h2 class="mb-0">\n        <button class="btn btn-link" type="button" data-toggle="collapse" data-target="#collapse'),__append(escapeFn(index)),__append('" aria-expanded="true" aria-controls="collapse$'),__append(escapeFn(index)),__append('">\n                From '),__append(escapeFn(event.actor)),__append(" ("),__append(escapeFn(event.actor_role)),__append(") on "),__append(escapeFn(getHumanReadableDate(event.date))),__append("\n          "),null!==event.new_status&&(__append('\n          <span style="padding-left: 10px;">New status:</span> '),__append(escapeFn(swh.add_forge.formatRequestStatusName(event.new_status))),__append("\n          ")),__append('\n        </button>\n      </h2>\n    </div>\n    <div id="collapse'),__append(escapeFn(index)),__append('" class="collapse" aria-labelledby="historyItem'),__append(escapeFn(index)),__append('" data-parent="#requestHistory">\n      <div class="card-body">\n        <p>'),__append(escapeFn(event.text)),__append("</p>\n        "),null!==event.new_status&&(__append("\n          <p>\n           <span>Status changed to:</span> <strong>"),__append(escapeFn(swh.add_forge.formatRequestStatusName(event.new_status))),__append("</strong>\n          </p>\n        ")),__append("\n      </div>\n    </div>\n  </div>\n</div>\n");return __output}},46717:function(module){module.exports=function anonymous(locals,escapeFn,include,rethrow){escapeFn=escapeFn||function(e){return null==e?"":String(e).replace(_MATCH_HTML,encode_char)};var _ENCODE_HTML_RULES={"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&#34;","'":"&#39;"},_MATCH_HTML=/[&<>'"]/g;function encode_char(e){return _ENCODE_HTML_RULES[e]||e}var __output="";function __append(e){null!=e&&(__output+=e)}with(locals||{})__append("\nDear forge administrator,\n\nThe mission of Software Heritage is to collect, preserve and share all the\npublicly available source code (see https://www.softwareheritage.org for more\ninformation).\n\nWe just received a request to add the forge hosted at "),__append(escapeFn(forgeUrl)),__append(" to the\nlist of software origins that are archived, and it is our understanding that you\nare the contact person for this forge.\n\nIn order to archive the forge contents, we will have to periodically pull the\npublic repositories it contains and clone them into the\nSoftware Heritage archive.\n\nWould you be so kind as to reply to this message to acknowledge the reception\nof this email and let us know if there are any special steps we should take in\norder to properly archive the public repositories hosted on your infrastructure?\n\nThank you in advance for your help.\n\nKind regards,\nThe Software Heritage team\n");return __output}},39449:function(module){module.exports=function anonymous(locals,escapeFn,include,rethrow){escapeFn=escapeFn||function(e){return null==e?"":String(e).replace(_MATCH_HTML,encode_char)};var _ENCODE_HTML_RULES={"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&#34;","'":"&#39;"},_MATCH_HTML=/[&<>'"]/g;function encode_char(e){return _ENCODE_HTML_RULES[e]||e}var __output="";function __append(e){null!=e&&(__output+=e)}with(locals||{})__append('\n<div class="custom-control custom-checkbox swhid-option">\n  <input class="custom-control-input" value="option-user-requests-filter" type="checkbox"\n    '),checked&&__append('\n         checked="checked"\n    '),__append('\n         id="'),__append(escapeFn(inputId)),__append('">\n  <label class="custom-control-label font-weight-normal" for="'),__append(escapeFn(inputId)),__append('">\n    show only your own requests\n  </label>\n</div>\n');return __output}},35666:function(e){var t=function(e){"use strict";var t,n=Object.prototype,r=n.hasOwnProperty,o="function"==typeof Symbol?Symbol:{},a=o.iterator||"@@iterator",i=o.asyncIterator||"@@asyncIterator",s=o.toStringTag||"@@toStringTag";function u(e,t,n){return Object.defineProperty(e,t,{value:n,enumerable:!0,configurable:!0,writable:!0}),e[t]}try{u({},"")}catch(e){u=function(e,t,n){return e[t]=n}}function c(e,t,n,r){var o=t&&t.prototype instanceof m?t:m,a=Object.create(o.prototype),i=new S(r||[]);return a._invoke=function(e,t,n){var r=p;return function(o,a){if(r===f)throw new Error("Generator is already running");if(r===_){if("throw"===o)throw a;return F()}for(n.method=o,n.arg=a;;){var i=n.delegate;if(i){var s=T(i,n);if(s){if(s===h)continue;return s}}if("next"===n.method)n.sent=n._sent=n.arg;else if("throw"===n.method){if(r===p)throw r=_,n.arg;n.dispatchException(n.arg)}else"return"===n.method&&n.abrupt("return",n.arg);r=f;var u=d(e,t,n);if("normal"===u.type){if(r=n.done?_:l,u.arg===h)continue;return{value:u.arg,done:n.done}}"throw"===u.type&&(r=_,n.method="throw",n.arg=u.arg)}}}(e,n,i),a}function d(e,t,n){try{return{type:"normal",arg:e.call(t,n)}}catch(e){return{type:"throw",arg:e}}}e.wrap=c;var p="suspendedStart",l="suspendedYield",f="executing",_="completed",h={};function m(){}function g(){}function v(){}var y={};y[a]=function(){return this};var w=Object.getPrototypeOf,b=w&&w(w(k([])));b&&b!==n&&r.call(b,a)&&(y=b);var E=v.prototype=m.prototype=Object.create(y);function x(e){["next","throw","return"].forEach((function(t){u(e,t,(function(e){return this._invoke(t,e)}))}))}function D(e,t){function n(o,a,i,s){var u=d(e[o],e,a);if("throw"!==u.type){var c=u.arg,p=c.value;return p&&"object"==typeof p&&r.call(p,"__await")?t.resolve(p.__await).then((function(e){n("next",e,i,s)}),(function(e){n("throw",e,i,s)})):t.resolve(p).then((function(e){c.value=e,i(c)}),(function(e){return n("throw",e,i,s)}))}s(u.arg)}var o;this._invoke=function(e,r){function a(){return new t((function(t,o){n(e,r,t,o)}))}return o=o?o.then(a,a):a()}}function T(e,n){var r=e.iterator[n.method];if(r===t){if(n.delegate=null,"throw"===n.method){if(e.iterator.return&&(n.method="return",n.arg=t,T(e,n),"throw"===n.method))return h;n.method="throw",n.arg=new TypeError("The iterator does not provide a 'throw' method")}return h}var o=d(r,e.iterator,n.arg);if("throw"===o.type)return n.method="throw",n.arg=o.arg,n.delegate=null,h;var a=o.arg;return a?a.done?(n[e.resultName]=a.value,n.next=e.nextLoc,"return"!==n.method&&(n.method="next",n.arg=t),n.delegate=null,h):a:(n.method="throw",n.arg=new TypeError("iterator result is not an object"),n.delegate=null,h)}function L(e){var t={tryLoc:e[0]};1 in e&&(t.catchLoc=e[1]),2 in e&&(t.finallyLoc=e[2],t.afterLoc=e[3]),this.tryEntries.push(t)}function C(e){var t=e.completion||{};t.type="normal",delete t.arg,e.completion=t}function S(e){this.tryEntries=[{tryLoc:"root"}],e.forEach(L,this),this.reset(!0)}function k(e){if(e){var n=e[a];if(n)return n.call(e);if("function"==typeof e.next)return e;if(!isNaN(e.length)){var o=-1,i=function n(){for(;++o<e.length;)if(r.call(e,o))return n.value=e[o],n.done=!1,n;return n.value=t,n.done=!0,n};return i.next=i}}return{next:F}}function F(){return{value:t,done:!0}}return g.prototype=E.constructor=v,v.constructor=g,g.displayName=u(v,s,"GeneratorFunction"),e.isGeneratorFunction=function(e){var t="function"==typeof e&&e.constructor;return!!t&&(t===g||"GeneratorFunction"===(t.displayName||t.name))},e.mark=function(e){return Object.setPrototypeOf?Object.setPrototypeOf(e,v):(e.__proto__=v,u(e,s,"GeneratorFunction")),e.prototype=Object.create(E),e},e.awrap=function(e){return{__await:e}},x(D.prototype),D.prototype[i]=function(){return this},e.AsyncIterator=D,e.async=function(t,n,r,o,a){void 0===a&&(a=Promise);var i=new D(c(t,n,r,o),a);return e.isGeneratorFunction(n)?i:i.next().then((function(e){return e.done?e.value:i.next()}))},x(E),u(E,s,"Generator"),E[a]=function(){return this},E.toString=function(){return"[object Generator]"},e.keys=function(e){var t=[];for(var n in e)t.push(n);return t.reverse(),function n(){for(;t.length;){var r=t.pop();if(r in e)return n.value=r,n.done=!1,n}return n.done=!0,n}},e.values=k,S.prototype={constructor:S,reset:function(e){if(this.prev=0,this.next=0,this.sent=this._sent=t,this.done=!1,this.delegate=null,this.method="next",this.arg=t,this.tryEntries.forEach(C),!e)for(var n in this)"t"===n.charAt(0)&&r.call(this,n)&&!isNaN(+n.slice(1))&&(this[n]=t)},stop:function(){this.done=!0;var e=this.tryEntries[0].completion;if("throw"===e.type)throw e.arg;return this.rval},dispatchException:function(e){if(this.done)throw e;var n=this;function o(r,o){return s.type="throw",s.arg=e,n.next=r,o&&(n.method="next",n.arg=t),!!o}for(var a=this.tryEntries.length-1;a>=0;--a){var i=this.tryEntries[a],s=i.completion;if("root"===i.tryLoc)return o("end");if(i.tryLoc<=this.prev){var u=r.call(i,"catchLoc"),c=r.call(i,"finallyLoc");if(u&&c){if(this.prev<i.catchLoc)return o(i.catchLoc,!0);if(this.prev<i.finallyLoc)return o(i.finallyLoc)}else if(u){if(this.prev<i.catchLoc)return o(i.catchLoc,!0)}else{if(!c)throw new Error("try statement without catch or finally");if(this.prev<i.finallyLoc)return o(i.finallyLoc)}}}},abrupt:function(e,t){for(var n=this.tryEntries.length-1;n>=0;--n){var o=this.tryEntries[n];if(o.tryLoc<=this.prev&&r.call(o,"finallyLoc")&&this.prev<o.finallyLoc){var a=o;break}}a&&("break"===e||"continue"===e)&&a.tryLoc<=t&&t<=a.finallyLoc&&(a=null);var i=a?a.completion:{};return i.type=e,i.arg=t,a?(this.method="next",this.next=a.finallyLoc,h):this.complete(i)},complete:function(e,t){if("throw"===e.type)throw e.arg;return"break"===e.type||"continue"===e.type?this.next=e.arg:"return"===e.type?(this.rval=this.arg=e.arg,this.method="return",this.next="end"):"normal"===e.type&&t&&(this.next=t),h},finish:function(e){for(var t=this.tryEntries.length-1;t>=0;--t){var n=this.tryEntries[t];if(n.finallyLoc===e)return this.complete(n.completion,n.afterLoc),C(n),h}},catch:function(e){for(var t=this.tryEntries.length-1;t>=0;--t){var n=this.tryEntries[t];if(n.tryLoc===e){var r=n.completion;if("throw"===r.type){var o=r.arg;C(n)}return o}}throw new Error("illegal catch attempt")},delegateYield:function(e,n,r){return this.delegate={iterator:k(e),resultName:n,nextLoc:r},"next"===this.method&&(this.arg=t),h}},e}(e.exports);try{regeneratorRuntime=t}catch(e){Function("r","regeneratorRuntime = r")(t)}},15861:function(e,t,n){"use strict";function r(e,t,n,r,o,a,i){try{var s=e[a](i),u=s.value}catch(e){return void n(e)}s.done?t(u):Promise.resolve(u).then(r,o)}function o(e){return function(){var t=this,n=arguments;return new Promise((function(o,a){var i=e.apply(t,n);function s(e){r(i,o,a,s,u,"next",e)}function u(e){r(i,o,a,s,u,"throw",e)}s(void 0)}))}}n.d(t,{Z:function(){return o}})},31955:function(e,t){"use strict";function n(e){for(var t=1;t<arguments.length;t++){var n=arguments[t];for(var r in n)e[r]=n[r]}return e}var r=function e(t,r){function o(e,o,a){if("undefined"!=typeof document){"number"==typeof(a=n({},r,a)).expires&&(a.expires=new Date(Date.now()+864e5*a.expires)),a.expires&&(a.expires=a.expires.toUTCString()),e=encodeURIComponent(e).replace(/%(2[346B]|5E|60|7C)/g,decodeURIComponent).replace(/[()]/g,escape);var i="";for(var s in a)a[s]&&(i+="; "+s,!0!==a[s]&&(i+="="+a[s].split(";")[0]));return document.cookie=e+"="+t.write(o,e)+i}}return Object.create({set:o,get:function(e){if("undefined"!=typeof document&&(!arguments.length||e)){for(var n=document.cookie?document.cookie.split("; "):[],r={},o=0;o<n.length;o++){var a=n[o].split("="),i=a.slice(1).join("=");try{var s=decodeURIComponent(a[0]);if(r[s]=t.read(i,s),e===s)break}catch(e){}}return e?r[e]:r}},remove:function(e,t){o(e,"",n({},t,{expires:-1}))},withAttributes:function(t){return e(this.converter,n({},this.attributes,t))},withConverter:function(t){return e(n({},this.converter,t),this.attributes)}},{attributes:{value:Object.freeze(r)},converter:{value:Object.freeze(t)}})}({read:function(e){return'"'===e[0]&&(e=e.slice(1,-1)),e.replace(/(%[\dA-F]{2})+/gi,decodeURIComponent)},write:function(e){return encodeURIComponent(e).replace(/%(2[346BF]|3[AC-F]|40|5[BDE]|60|7[BCD])/g,decodeURIComponent)}},{path:"/"});t.Z=r}},__webpack_module_cache__={};function __webpack_require__(e){var t=__webpack_module_cache__[e];if(void 0!==t)return t.exports;var n=__webpack_module_cache__[e]={exports:{}};return __webpack_modules__[e](n,n.exports,__webpack_require__),n.exports}__webpack_require__.n=function(e){var t=e&&e.__esModule?function(){return e.default}:function(){return e};return __webpack_require__.d(t,{a:t}),t},__webpack_require__.d=function(e,t){for(var n in t)__webpack_require__.o(t,n)&&!__webpack_require__.o(e,n)&&Object.defineProperty(e,n,{enumerable:!0,get:t[n]})},__webpack_require__.o=function(e,t){return Object.prototype.hasOwnProperty.call(e,t)},__webpack_require__.r=function(e){"undefined"!=typeof Symbol&&Symbol.toStringTag&&Object.defineProperty(e,Symbol.toStringTag,{value:"Module"}),Object.defineProperty(e,"__esModule",{value:!0})};var __webpack_exports__={};return function(){"use strict";__webpack_require__.r(__webpack_exports__),__webpack_require__.d(__webpack_exports__,{formatRequestStatusName:function(){return r},onCreateRequestPageLoad:function(){return e.T},onModerationPageLoad:function(){return t.f},onRequestDashboardLoad:function(){return n.q},populateDecisionSelectOption:function(){return n.H},populateModerationList:function(){return t.y},populateRequestBrowseList:function(){return e.x}});var e=__webpack_require__(7200),t=__webpack_require__(98955),n=__webpack_require__(90668);function r(e){var t={PENDING:"Pending",WAITING_FOR_FEEDBACK:"Waiting for feedback",FEEDBACK_TO_HANDLE:"Feedback to handle",ACCEPTED:"Accepted",SCHEDULED:"Scheduled",FIRST_LISTING_DONE:"First listing done",FIRST_ORIGIN_LOADED:"First origin loaded",REJECTED:"Rejected",SUSPENDED:"Suspended",DENIED:"Denied"};return e in t?t[e]:e}}(),__webpack_exports__}()}));
//# sourceMappingURL=add_forge.bcbbc1be5ab34eede65c.js.map