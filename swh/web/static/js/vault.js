!function(t,e){"object"==typeof exports&&"object"==typeof module?module.exports=e():"function"==typeof define&&define.amd?define([],e):"object"==typeof exports?exports.vault=e():(t.swh=t.swh||{},t.swh.vault=e())}(window,function(){return function(t){var e={};function o(a){if(e[a])return e[a].exports;var r=e[a]={i:a,l:!1,exports:{}};return t[a].call(r.exports,r,r.exports,o),r.l=!0,r.exports}return o.m=t,o.c=e,o.d=function(t,e,a){o.o(t,e)||Object.defineProperty(t,e,{configurable:!1,enumerable:!0,get:a})},o.r=function(t){Object.defineProperty(t,"__esModule",{value:!0})},o.n=function(t){var e=t&&t.__esModule?function(){return t.default}:function(){return t};return o.d(e,"a",e),e},o.o=function(t,e){return Object.prototype.hasOwnProperty.call(t,e)},o.p="/static/",o(o.s=448)}({203:function(t,e,o){"use strict";o.r(e);o(447);var a=o(35),r='<div class="progress" style="margin-bottom: 0px;">\n                  <div class="progress-bar progress-bar-success progress-bar-striped"\n                       role="progressbar" aria-valuenow="100" aria-valuemin="0"\n                       aria-valuemax="100" style="width: 100%;height: 100%;">\n                  </div>\n                </div>;',i=5e3,n=void 0;function s(t,e){"new"===e.status?t.css("background-color","rgba(128, 128, 128, 0.5)"):"pending"===e.status?t.css("background-color","rgba(0, 0, 255, 0.5)"):"done"===e.status?t.css("background-color","#5cb85c"):"failed"===e.status&&(t.css("background-color","rgba(255, 0, 0, 0.5)"),t.css("background-image","none")),t.text(e.progress_message||e.status),"new"===e.status||"pending"===e.status?t.addClass("active"):t.removeClass("progress-bar-striped")}function c(){var t=JSON.parse(localStorage.getItem("swh-vault-cooking-tasks"));if(!t||0===t.length)return $(".swh-vault-table tbody tr").remove(),void(n=setTimeout(c,i));for(var e=[],o={},d=[],l=0;l<t.length;++l){var u=t[l];d.push(u.object_id),o[u.object_id]=u;var f=void 0;f="directory"===u.object_type?Urls.vault_cook_directory(u.object_id):Urls.vault_cook_revision_gitfast(u.object_id),"done"!==u.status&&"failed"!==u.status&&e.push(fetch(f))}$(".swh-vault-table tbody tr").each(function(t,e){var o=$(e).find(".vault-object-id").data("object-id");-1===$.inArray(o,d)&&$(e).remove()}),Promise.all(e).then(a.b).then(function(t){return Promise.all(t.map(function(t){return t.json()}))}).then(function(e){for(var a=$("#vault-cooking-tasks tbody"),d=0;d<e.length;++d){var l=o[e[d].obj_id];l.status=e[d].status,l.fetch_url=e[d].fetch_url,l.progress_message=e[d].progress_message}for(var u=0;u<t.length;++u){var f=t[u],v=$("#vault-task-"+f.object_id);if(v.length){s(v.find(".progress-bar"),f);var b=v.find(".vault-dl-link");"done"===f.status?b[0].innerHTML='<a class="btn btn-md btn-swh" href="'+f.fetch_url+'"><i class="fa fa-download fa-fw" aria-hidden="true"></i>Download</a>':"failed"===f.status&&(b[0].innerHTML="")}else{var g=void 0;g="directory"===f.object_type?Urls.browse_directory(f.object_id):Urls.browse_revision(f.object_id);var h=$.parseHTML(r)[0];s($(h).find(".progress-bar"),f);var p=void 0;p="directory"===f.object_type?'<tr id="vault-task-'+f.object_id+'" title="Once downloaded, the directory can be extracted with the following command:\n\n$ tar xvzf '+f.object_id+'.tar.gz">':'<tr id="vault-task-'+f.object_id+'"  title="Once downloaded, the git repository can be imported with the following commands:\n\n$ git init\n$ zcat '+f.object_id+'.gitfast.gz | git fast-import">',p+='<td><input type="checkbox" class="vault-task-toggle-selection"/></td>',"directory"===f.object_type?p+='<td><i class="fa fa-folder fa-fw" aria-hidden="true"></i>directory</td>':p+='<td><i class="octicon octicon-git-commit fa-fw"></i>revision</td>',p+='<td class="vault-object-id" data-object-id="'+f.object_id+'"><a href="'+g+'">'+f.object_id+"</a></td>",p+='<td style="width: 350px">'+h.outerHTML+"</td>";var m="Waiting for download link to be available";"done"===f.status?m='<a class="btn btn-md btn-swh" href="'+f.fetch_url+'"><i class="fa fa-download fa-fw" aria-hidden="true"></i>Download</a>':"failed"===f.status&&(m=""),p+='<td class="vault-dl-link" style="width: 320px">'+m+"</td>",p+="</tr>",a.prepend(p)}}localStorage.setItem("swh-vault-cooking-tasks",JSON.stringify(t)),n=setTimeout(c,i)}).catch(function(){})}function d(){$("#vault-tasks-toggle-selection").change(function(t){$(".vault-task-toggle-selection").prop("checked",t.currentTarget.checked)}),$("#vault-remove-tasks").click(function(){clearTimeout(n);var t=[];$(".swh-vault-table tbody tr").each(function(e,o){if($(o).find(".vault-task-toggle-selection").prop("checked")){var a=$(o).find(".vault-object-id").data("object-id");t.push(a),$(o).remove()}});var e=JSON.parse(localStorage.getItem("swh-vault-cooking-tasks"));e=$.grep(e,function(e){return-1===$.inArray(e.object_id,t)}),localStorage.setItem("swh-vault-cooking-tasks",JSON.stringify(e)),$("#vault-tasks-toggle-selection").prop("checked",!1),n=setTimeout(c,i)}),n=setTimeout(c,i),$(document).on("shown.bs.tab",'a[data-toggle="tab"]',function(t){"Vault"===t.currentTarget.text.trim()&&(clearTimeout(n),c())}),window.onfocus=function(){clearTimeout(n),c()}}function l(t){var e=JSON.parse(localStorage.getItem("swh-vault-cooking-tasks"));if(e||(e=[]),void 0===e.find(function(e){return e.object_type===t.object_type&&e.object_id===t.object_id})){var o=void 0;o="directory"===t.object_type?Urls.vault_cook_directory(t.object_id):Urls.vault_cook_revision_gitfast(t.object_id),t.email&&(o+="?email="+t.email),fetch(o,{method:"POST"}).then(a.a).then(function(){e.push(t),localStorage.setItem("swh-vault-cooking-tasks",JSON.stringify(e)),$("#vault-cook-directory-modal").modal("hide"),$("#vault-cook-revision-modal").modal("hide"),swh.browse.showTab("#vault")}).catch(function(){$("#vault-cook-directory-modal").modal("hide"),$("#vault-cook-revision-modal").modal("hide")})}else swh.browse.showTab("#vault")}function u(t){return/^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/.test(String(t).toLowerCase())}function f(t){var e=$("#swh-vault-directory-email").val().trim();!e||u(e)?l({object_type:"directory",object_id:t,email:e,status:"new"}):$("#invalid-email-modal").modal("show")}function v(t){var e=$("#swh-vault-revision-email").val().trim();!e||u(e)?l({object_type:"revision",object_id:t,email:e,status:"new"}):$("#invalid-email-modal").modal("show")}function b(){$(document).ready(function(){$(".swh-browse-top-navigation").append($("#vault-cook-directory-modal")),$(".swh-browse-top-navigation").append($("#vault-cook-revision-modal")),$(".swh-browse-top-navigation").append($("#invalid-email-modal"))})}o.d(e,"initUi",function(){return d}),o.d(e,"cookDirectoryArchive",function(){return f}),o.d(e,"cookRevisionArchive",function(){return v}),o.d(e,"initTaskCreationUi",function(){return b})},35:function(t,e,o){"use strict";function a(t){if(!t.ok)throw Error(t.statusText);return t}function r(t){for(var e=0;e<t.length;++e)if(!t[e].ok)throw Error(t[e].statusText);return t}function i(t){return"/static/"+t}o.d(e,"a",function(){return a}),o.d(e,"b",function(){return r}),o.d(e,"c",function(){return i})},447:function(t,e,o){},448:function(t,e,o){t.exports=o(203)}})});
//# vault.js.map