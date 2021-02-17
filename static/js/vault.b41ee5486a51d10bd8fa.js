!function(e,t){"object"==typeof exports&&"object"==typeof module?module.exports=t():"function"==typeof define&&define.amd?define([],t):"object"==typeof exports?exports.swh=t():(e.swh=e.swh||{},e.swh.vault=t())}(self,(function(){return function(){var __webpack_modules__={2325:function(e,t,o){"use strict";o.d(t,{YQ:function(){return r},dg:function(){return s},es:function(){return _},JO:function(){return u},vE:function(){return l}});var n=o(45149),a={position:"fixed",left:"1rem",bottom:"1rem","z-index":"100000"};function r(e,t){var o;o="directory"===e?Urls.api_1_vault_cook_directory(t):Urls.api_1_vault_cook_revision_gitfast(t),fetch(o).then((function(e){return e.json()})).then((function(o){if("NotFoundExc"===o.exception||"failed"===o.status)swh.vault.removeCookingTaskInfo([t]),$("#vault-cook-"+e+"-modal").modal("show");else if("done"===o.status)$("#vault-fetch-"+e+"-modal").modal("show");else{var r=$((0,n.EM)("danger","Archive cooking service is currently experiencing issues.<br/>Please try again later.",!0));r.css(a),$("body").append(r)}}))}function i(e){var t=swh.webapp.getSwhIdsContext();e.origin=t[e.object_type].context.origin,e.path=t[e.object_type].context.path,e.browse_url=t[e.object_type].swhid_with_context_url,e.browse_url||(e.browse_url=t[e.object_type].swhid_url);var o,r=JSON.parse(localStorage.getItem("swh-vault-cooking-tasks"));(r||(r=[]),void 0===r.find((function(t){return t.object_type===e.object_type&&t.object_id===e.object_id})))&&(o="directory"===e.object_type?Urls.api_1_vault_cook_directory(e.object_id):Urls.api_1_vault_cook_revision_gitfast(e.object_id),e.email&&(o+="?email="+e.email),(0,n.e_)(o).then(n.ry).then((function(){r.push(e),localStorage.setItem("swh-vault-cooking-tasks",JSON.stringify(r)),$("#vault-cook-directory-modal").modal("hide"),$("#vault-cook-revision-modal").modal("hide");var t=$((0,n.EM)("success",'Archive cooking request successfully submitted.<br/>Go to the <a href="'+Urls.browse_vault()+'">Downloads</a> page to get the download link once it is ready.',!0));t.css(a),$("body").append(t)})).catch((function(){$("#vault-cook-directory-modal").modal("hide"),$("#vault-cook-revision-modal").modal("hide");var e=$((0,n.EM)("danger","Archive cooking request submission failed.",!0));e.css(a),$("body").append(e)})))}function c(e){return/^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/.test(String(e).toLowerCase())}function s(e){var t=$("#swh-vault-directory-email").val().trim();!t||c(t)?i({object_type:"directory",object_id:e,email:t,status:"new"}):$("#invalid-email-modal").modal("show")}function _(e){$("#vault-fetch-directory-modal").modal("hide");var t=Urls.api_1_vault_cook_directory(e);fetch(t).then((function(e){return e.json()})).then((function(e){swh.vault.fetchCookedObject(e.fetch_url)}))}function u(e){var t=$("#swh-vault-revision-email").val().trim();!t||c(t)?i({object_type:"revision",object_id:e,email:t,status:"new"}):$("#invalid-email-modal").modal("show")}function l(e){$("#vault-fetch-directory-modal").modal("hide");var t=Urls.api_1_vault_cook_revision_gitfast(e);fetch(t).then((function(e){return e.json()})).then((function(e){swh.vault.fetchCookedObject(e.fetch_url)}))}},7451:function(e,t,o){"use strict";o.d(t,{H6:function(){return u},rh:function(){return l},xF:function(){return p},LY:function(){return f}});var n,a,r=o(45149),i=o(96874),c=o.n(i),s=5e3;function _(e,t){"new"===t.status?e.css("background-color","rgba(128, 128, 128, 0.5)"):"pending"===t.status?e.css("background-color","rgba(0, 0, 255, 0.5)"):"done"===t.status?e.css("background-color","#5cb85c"):"failed"===t.status&&(e.css("background-color","rgba(255, 0, 0, 0.5)"),e.css("background-image","none")),e.text(t.progress_message||t.status),"new"===t.status||"pending"===t.status?e.addClass("progress-bar-animated"):e.removeClass("progress-bar-striped")}function u(e){a=null,fetch(e).then((function(t){if(t.ok)$("#vault-fetch-iframe").attr("src",e);else{for(var o=JSON.parse(localStorage.getItem("swh-vault-cooking-tasks")),n=0;n<o.length;++n)if(o[n].fetch_url===e){a=o[n];break}$("#vault-recook-object-modal").modal("show")}}))}function l(){var e;a&&(clearTimeout(n),e="directory"===a.object_type?Urls.api_1_vault_cook_directory(a.object_id):Urls.api_1_vault_cook_revision_gitfast(a.object_id),a.email&&(e+="?email="+a.email),(0,r.e_)(e).then(r.ry).then((function(){a.status="new";for(var e=JSON.parse(localStorage.getItem("swh-vault-cooking-tasks")),t=0;t<e.length;++t)if(e[t].object_id===a.object_id){e[t]=a;break}localStorage.setItem("swh-vault-cooking-tasks",JSON.stringify(e)),d(),$("#vault-recook-object-modal").modal("hide")})).catch((function(){d(),$("#vault-recook-object-modal").modal("hide")})))}function d(){var e=JSON.parse(localStorage.getItem("swh-vault-cooking-tasks"));if(!e||0===e.length)return $(".swh-vault-table tbody tr").remove(),void(n=setTimeout(d,s));for(var t=[],o={},a=[],i=0;i<e.length;++i){var u=e[i];a.push(u.object_id),o[u.object_id]=u;var l=void 0;l="directory"===u.object_type?Urls.api_1_vault_cook_directory(u.object_id):Urls.api_1_vault_cook_revision_gitfast(u.object_id),"done"!==u.status&&"failed"!==u.status&&t.push(fetch(l))}$(".swh-vault-table tbody tr").each((function(e,t){var o=$(t).find(".vault-object-info").data("object-id");-1===$.inArray(o,a)&&$(t).remove()})),Promise.all(t).then(r.un).then((function(e){return Promise.all(e.map((function(e){return e.json()})))})).then((function(t){for(var a=$("#vault-cooking-tasks tbody"),r=0;r<t.length;++r){var i=o[t[r].obj_id];i.status=t[r].status,i.fetch_url=t[r].fetch_url,i.progress_message=t[r].progress_message}for(var u=0;u<e.length;++u){var l=e[u],p=$("#vault-task-"+l.object_id);if(p.length){_(p.find(".progress-bar"),l);var f=p.find(".vault-dl-link");"done"===l.status?f[0].innerHTML='<button class="btn btn-default btn-sm" onclick="swh.vault.fetchCookedObject(\''+l.fetch_url+'\')"><i class="mdi mdi-download mdi-fw" aria-hidden="true"></i>Download</button>':f[0].innerHTML=""}else{var b=l.browse_url;b||(b="directory"===l.object_type?Urls.browse_directory(l.object_id):Urls.browse_revision(l.object_id));var v=$.parseHTML('<div class="progress">\n    <div class="progress-bar progress-bar-success progress-bar-striped"\n          role="progressbar" aria-valuenow="100" aria-valuemin="0"\n          aria-valuemax="100" style="width: 100%;height: 100%;">\n    </div>\n  </div>;')[0];_($(v).find(".progress-bar"),l),a.prepend(c()({browseUrl:b,cookingTask:l,progressBar:v,Urls:Urls,swh:swh}))}}localStorage.setItem("swh-vault-cooking-tasks",JSON.stringify(e)),n=setTimeout(d,s)})).catch((function(e){console.log("Error when fetching vault cooking tasks:",e)}))}function p(e){var t=JSON.parse(localStorage.getItem("swh-vault-cooking-tasks"));t&&(t=$.grep(t,(function(t){return-1===$.inArray(t.object_id,e)})),localStorage.setItem("swh-vault-cooking-tasks",JSON.stringify(t)))}function f(){$("#vault-tasks-toggle-selection").change((function(e){$(".vault-task-toggle-selection").prop("checked",e.currentTarget.checked)})),$("#vault-remove-tasks").click((function(){clearTimeout(n);var e=[];$(".swh-vault-table tbody tr").each((function(t,o){if($(o).find(".vault-task-toggle-selection").prop("checked")){var n=$(o).find(".vault-object-info").data("object-id");e.push(n),$(o).remove()}})),p(e),$("#vault-tasks-toggle-selection").prop("checked",!1),n=setTimeout(d,s)})),d(),window.onfocus=function(){clearTimeout(n),d()}}},45149:function(e,t,o){"use strict";function n(e){if(!e.ok)throw e;return e}function a(e){for(var t=0;t<e.length;++t)if(!e[t].ok)throw e[t];return e}function r(e,t,o){return void 0===t&&(t={}),void 0===o&&(o=null),t["X-CSRFToken"]=Cookies.get("csrftoken"),fetch(e,{credentials:"include",headers:t,method:"POST",body:o})}function i(e,t,o){void 0===o&&(o=!1);var n="",a="";return o&&(n='<button type="button" class="close" data-dismiss="alert" aria-label="Close">\n        <span aria-hidden="true">&times;</span>\n      </button>',a="alert-dismissible"),'<div class="alert alert-'+e+" "+a+'" role="alert">'+t+n+"</div>"}o.d(t,{ry:function(){return n},un:function(){return a},e_:function(){return r},EM:function(){return i}})},96874:function(module){module.exports=function anonymous(locals,escapeFn,include,rethrow){escapeFn=escapeFn||function(e){return null==e?"":String(e).replace(_MATCH_HTML,encode_char)};var _ENCODE_HTML_RULES={"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&#34;","'":"&#39;"},_MATCH_HTML=/[&<>'"]/g;function encode_char(e){return _ENCODE_HTML_RULES[e]||e}var __output="";function __append(e){null!=e&&(__output+=e)}with(locals||{})__append("\n\n"),"directory"===cookingTask.object_type?(__append('\n  <tr id="vault-task-'),__append(escapeFn(cookingTask.object_id)),__append('" title="Once downloaded, the directory can be extracted with the following command:\n\n$ tar xvzf '),__append(escapeFn(cookingTask.object_id)),__append('.tar.gz">\n')):(__append('\n  </tr><tr id="vault-task-'),__append(escapeFn(cookingTask.object_id)),__append('" title="Once downloaded, the git repository can be imported with the following commands:\n\n$ git init\n$ zcat '),__append(escapeFn(cookingTask.object_id)),__append('.gitfast.gz | git fast-import">\n')),__append('\n    <td>\n      <div class="custom-control custom-checkbox">\n      <input type="checkbox" class="custom-control-input vault-task-toggle-selection" id="vault-task-toggle-selection-'),__append(escapeFn(cookingTask.object_id)),__append('">\n      <label class="custom-control-label" for="vault-task-toggle-selection-'),__append(escapeFn(cookingTask.object_id)),__append('">\n      </label>\n    </div></td>\n    '),cookingTask.origin?(__append('\n      <td class="vault-origin">\n        <a href="'),__append(escapeFn(Urls.browse_origin())),__append("?origin_url="),__append(escapeFn(cookingTask.origin)),__append('">\n          '),__append(escapeFn(decodeURIComponent(cookingTask.origin))),__append("\n        </a>\n      </td>\n    ")):__append('\n      <td class="vault-origin">unknown</td>\n    '),__append('\n    <td>\n      <i class="'),__append(escapeFn(swh.webapp.getSwhObjectIcon(cookingTask.object_type))),__append(' mdi-fw"></i>\n      '),__append(escapeFn(cookingTask.object_type)),__append('\n    </td>\n    <td class="vault-object-info" data-object-id="'),__append(escapeFn(cookingTask.object_id)),__append('">\n      <b>id:</b>&nbsp;<a href="'),__append(escapeFn(browseUrl)),__append('">'),__append(escapeFn(cookingTask.object_id)),__append("</a>\n      "),cookingTask.path&&(__append("\n        <br><b>path:</b>&nbsp;"),__append(escapeFn(cookingTask.path)),__append("\n      ")),__append("\n    </td>\n    <td>"),__append(progressBar.outerHTML),__append('</td>\n    <td class="vault-dl-link">\n      '),"done"===cookingTask.status&&(__append('\n        <button class="btn btn-default btn-sm" onclick="swh.vault.fetchCookedObject(\''),__append(escapeFn(cookingTask.fetch_url)),__append('\')">\n          <i class="mdi mdi-download mdi-fw" aria-hidden="true"></i>Download\n        </button>\n      ')),__append("\n    </td>\n  </tr>");return __output}}},__webpack_module_cache__={};function __webpack_require__(e){if(__webpack_module_cache__[e])return __webpack_module_cache__[e].exports;var t=__webpack_module_cache__[e]={exports:{}};return __webpack_modules__[e](t,t.exports,__webpack_require__),t.exports}__webpack_require__.n=function(e){var t=e&&e.__esModule?function(){return e.default}:function(){return e};return __webpack_require__.d(t,{a:t}),t},__webpack_require__.d=function(e,t){for(var o in t)__webpack_require__.o(t,o)&&!__webpack_require__.o(e,o)&&Object.defineProperty(e,o,{enumerable:!0,get:t[o]})},__webpack_require__.o=function(e,t){return Object.prototype.hasOwnProperty.call(e,t)},__webpack_require__.r=function(e){"undefined"!=typeof Symbol&&Symbol.toStringTag&&Object.defineProperty(e,Symbol.toStringTag,{value:"Module"}),Object.defineProperty(e,"__esModule",{value:!0})};var __webpack_exports__={};return function(){"use strict";__webpack_require__.r(__webpack_exports__),__webpack_require__.d(__webpack_exports__,{fetchCookedObject:function(){return e.H6},initUi:function(){return e.LY},recookObject:function(){return e.rh},removeCookingTaskInfo:function(){return e.xF},cookDirectoryArchive:function(){return t.dg},cookRevisionArchive:function(){return t.JO},fetchDirectoryArchive:function(){return t.es},fetchRevisionArchive:function(){return t.vE},vaultRequest:function(){return t.YQ}});var e=__webpack_require__(7451),t=__webpack_require__(2325)}(),__webpack_exports__}()}));
//# sourceMappingURL=vault.b41ee5486a51d10bd8fa.js.map