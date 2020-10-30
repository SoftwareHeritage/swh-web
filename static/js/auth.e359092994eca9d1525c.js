!function(e,t){"object"==typeof exports&&"object"==typeof module?module.exports=t():"function"==typeof define&&define.amd?define([],t):"object"==typeof exports?exports.auth=t():(e.swh=e.swh||{},e.swh.auth=t())}(window,(function(){return function(e){var t={};function n(o){if(t[o])return t[o].exports;var r=t[o]={i:o,l:!1,exports:{}};return e[o].call(r.exports,r,r.exports,n),r.l=!0,r.exports}return n.m=e,n.c=t,n.d=function(e,t,o){n.o(e,t)||Object.defineProperty(e,t,{enumerable:!0,get:o})},n.r=function(e){"undefined"!=typeof Symbol&&Symbol.toStringTag&&Object.defineProperty(e,Symbol.toStringTag,{value:"Module"}),Object.defineProperty(e,"__esModule",{value:!0})},n.t=function(e,t){if(1&t&&(e=n(e)),8&t)return e;if(4&t&&"object"==typeof e&&e&&e.__esModule)return e;var o=Object.create(null);if(n.r(o),Object.defineProperty(o,"default",{enumerable:!0,value:e}),2&t&&"string"!=typeof e)for(var r in e)n.d(o,r,function(t){return e[t]}.bind(null,r));return o},n.n=function(e){var t=e&&e.__esModule?function(){return e.default}:function(){return e};return n.d(t,"a",t),t},n.o=function(e,t){return Object.prototype.hasOwnProperty.call(e,t)},n.p="/static/",n(n.s=253)}({2:function(e,t,n){"use strict";function o(e){if(!e.ok)throw e;return e}function r(e){for(var t=0;t<e.length;++t)if(!e[t].ok)throw e[t];return e}function s(e){return"/static/"+e}function a(e,t,n){return void 0===t&&(t={}),void 0===n&&(n=null),t["X-CSRFToken"]=Cookies.get("csrftoken"),fetch(e,{credentials:"include",headers:t,method:"POST",body:n})}function i(e,t){return new RegExp("(?:git|https?|git@)(?:\\:\\/\\/)?"+t+"[/|:][A-Za-z0-9-/]+?\\/[\\w\\.-]+\\/?(?!=.git)(?:\\.git(?:\\/?|\\#[\\w\\.\\-_]+)?)?$").test(e)}function u(){history.replaceState("",document.title,window.location.pathname+window.location.search)}function d(e,t){var n=window.getSelection();n.removeAllRanges();var o=document.createRange();o.setStart(e,0),"#text"!==t.nodeName?o.setEnd(t,t.childNodes.length):o.setEnd(t,t.textContent.length),n.addRange(o)}function c(e,t,n){void 0===n&&(n=!1);var o="",r="";return n&&(o='<button type="button" class="close" data-dismiss="alert" aria-label="Close">\n        <span aria-hidden="true">&times;</span>\n      </button>',r="alert-dismissible"),'<div class="alert alert-'+e+" "+r+'" role="alert">'+t+o+"</div>"}n.d(t,"b",(function(){return o})),n.d(t,"c",(function(){return r})),n.d(t,"h",(function(){return s})),n.d(t,"a",(function(){return a})),n.d(t,"e",(function(){return i})),n.d(t,"f",(function(){return u})),n.d(t,"g",(function(){return d})),n.d(t,"d",(function(){return c}))},253:function(e,t,n){e.exports=n(254)},254:function(e,t,n){"use strict";n.r(t),n.d(t,"applyTokenAction",(function(){return w})),n.d(t,"initProfilePage",(function(){return h}));var o,r=n(2);n(255);function s(){var e=$("#swh-user-password").val();$("#swh-user-password-submit").prop("disabled",0===e.length)}function a(e){return'<p id="swh-token-error-message" class="mt-3">'+e+"</p>"}function i(e){return'<p id="swh-token-success-message" class="mt-3">'+e+"</p>"}function u(){$("#swh-user-password-submit").prop("disabled",!0),$("#swh-user-password").off("change"),$("#swh-user-password").off("keyup")}function d(){Object(r.a)(Urls.oidc_generate_bearer_token(),{},JSON.stringify({password:$("#swh-user-password").val()})).then(r.b).then((function(e){return e.text()})).then((function(e){u();var t=i("Below is your token.")+'\n         <pre id="swh-bearer-token">'+e+"</pre>";$("#swh-password-form").append(t),o.draw()})).catch((function(e){400===e.status?$("#swh-password-form").append(a("You are not allowed to generate bearer tokens.")):401===e.status?$("#swh-password-form").append(a("The password is invalid.")):$("#swh-password-form").append(a("Internal server error."))}))}function c(e){var t={password:$("#swh-user-password").val(),token_id:e};Object(r.a)(Urls.oidc_get_bearer_token(),{},JSON.stringify(t)).then(r.b).then((function(e){return e.text()})).then((function(e){u();var t=i("Below is your token.")+'\n         <pre id="swh-bearer-token">'+e+"</pre>";$("#swh-password-form").append(t)})).catch((function(e){401===e.status?$("#swh-password-form").append(a("The password is invalid.")):$("#swh-password-form").append(a("Internal server error."))}))}function l(e){var t={password:$("#swh-user-password").val(),token_ids:e};Object(r.a)(Urls.oidc_revoke_bearer_tokens(),{},JSON.stringify(t)).then(r.b).then((function(){u(),$("#swh-password-form").append(i("Bearer token"+(e.length>1?"s":"")+" successfully revoked")),o.draw()})).catch((function(e){401===e.status?$("#swh-password-form").append(a("The password is invalid.")):$("#swh-password-form").append(a("Internal server error."))}))}function p(e){l([e])}function f(){for(var e=[],t=o.rows().data(),n=0;n<t.length;++n)e.push(t[n].id);l(e)}function w(e,t){var n={generate:{modalTitle:"Bearer token generation",infoText:"Enter your password and click on the button to generate the token.",buttonText:"Generate token",submitCallback:d},display:{modalTitle:"Display bearer token",infoText:"Enter your password and click on the button to display the token.",buttonText:"Display token",submitCallback:c},revoke:{modalTitle:"Revoke bearer token",infoText:"Enter your password and click on the button to revoke the token.",buttonText:"Revoke token",submitCallback:p},revokeAll:{modalTitle:"Revoke all bearer tokens",infoText:"Enter your password and click on the button to revoke all tokens.",buttonText:"Revoke tokens",submitCallback:f}};if(n[e]){var o,r,a=(o=n[e].infoText,r=n[e].buttonText,'<form id="swh-password-form">\n      <p id="swh-password-form-text">'+o+'</p>\n      <label for="swh-user-password">Password:&nbsp;</label>\n      <input id="swh-user-password" type="password" name="swh-user-password" required>\n      <input id="swh-user-password-submit" type="submit" value="'+r+'" disabled>\n    </form>');swh.webapp.showModalHtml(n[e].modalTitle,a),$("#swh-user-password").change(s),$("#swh-user-password").keyup(s),$("#swh-password-form").submit((function(o){o.preventDefault(),o.stopPropagation(),n[e].submitCallback(t)}))}}function h(){$(document).ready((function(){o=$("#swh-bearer-tokens-table").on("error.dt",(function(e,t,n,o){$("#swh-origin-save-request-list-error").text("An error occurred while retrieving the tokens list"),console.log(o)})).DataTable({serverSide:!0,ajax:Urls.oidc_list_bearer_tokens(),columns:[{data:"creation_date",name:"creation_date",render:function(e,t,n){return"display"===t?new Date(e).toLocaleString():e}},{render:function(e,t,n){return'<button class="btn btn-default"\n                         onclick="swh.auth.applyTokenAction(\'display\', '+n.id+')">\n                  Display token\n                </button>\n                <button class="btn btn-default"\n                        onclick="swh.auth.applyTokenAction(\'revoke\', '+n.id+')">\n                  Revoke token\n                </button>'}}],ordering:!1,searching:!1,scrollY:"50vh",scrollCollapse:!0}),$("#swh-oidc-profile-tokens-tab").on("shown.bs.tab",(function(){o.draw(),window.location.hash="#tokens"})),$("#swh-oidc-profile-account-tab").on("shown.bs.tab",(function(){Object(r.f)()})),"#tokens"===window.location.hash&&$('.nav-tabs a[href="#swh-oidc-profile-tokens"]').tab("show")}))}},255:function(e,t,n){}})}));
//# sourceMappingURL=auth.e359092994eca9d1525c.js.map