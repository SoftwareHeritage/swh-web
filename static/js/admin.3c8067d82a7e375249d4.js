!function(e,t){"object"==typeof exports&&"object"==typeof module?module.exports=t():"function"==typeof define&&define.amd?define([],t):"object"==typeof exports?exports.swh=t():(e.swh=e.swh||{},e.swh.admin=t())}(self,(function(){return function(){"use strict";var e={98921:function(e,t,n){function r(e,t){if("display"===t&&(e&&e.startsWith("swh")))return'<a href="'+Urls.browse_swhid(e)+'">'+e.replace(/;/g,";<br/>")+"</a>";return e}function i(){var e;$(document).ready((function(){$.fn.dataTable.ext.errMode="none",e=$("#swh-admin-deposit-list").on("error.dt",(function(e,t,n,r){$("#swh-admin-deposit-list-error").text(r)})).DataTable({serverSide:!0,processing:!0,dom:'<<"d-flex justify-content-between align-items-center"f<"#list-exclude">l>rt<"bottom"ip>>',ajax:{url:Urls.admin_deposit_list(),data:function(e){e.excludePattern=$("#swh-admin-deposit-list-exclude-filter").val()}},columns:[{data:"id",name:"id"},{data:"swhid_context",name:"swhid_context",render:function(e,t,n){if(e&&"display"===t){var r=";origin=",i=e.indexOf(r);if(-1!==i){var a=e.slice(i+r.length),s=a.indexOf(";");return-1!==s&&(a=a.slice(0,s)),'<a href="'+a+'">'+a+"</a>"}}return e}},{data:"reception_date",name:"reception_date",render:function(e,t,n){return"display"===t?new Date(e).toLocaleString():e}},{data:"status",name:"status"},{data:"status_detail",name:"status_detail",render:function(e,t,n){if("display"===t&&e){var r=e;return"object"==typeof e&&(r=JSON.stringify(e,null,4)),'<div style="width: 200px; white-space: pre; overflow-x: auto;">'+r+"</div>"}return e},orderable:!1,visible:!1},{data:"swhid",name:"swhid",render:function(e,t,n){return r(e,t)},orderable:!1,visible:!1},{data:"swhid_context",name:"swhid_context",render:function(e,t,n){return r(e,t)},orderable:!1,visible:!1}],scrollX:!0,scrollY:"50vh",scrollCollapse:!0,order:[[0,"desc"]]}),$("div#list-exclude").html('<div id="swh-admin-deposit-list-exclude-wrapper">\n    <div id="swh-admin-deposit-list-exclude-div-wrapper" class="dataTables_filter">\n      <label>\n        Exclude:<input id="swh-admin-deposit-list-exclude-filter"\n                       type="search"\n                       value="check-deposit"\n                       class="form-control form-control-sm"\n                       placeholder="exclude-pattern" aria-controls="swh-admin-deposit-list">\n          </input>\n      </label>\n    </div>\n  </div>\n'),$("#swh-admin-deposit-list-exclude-filter").keyup((function(){e.draw()})),e.draw()})),$("a.toggle-col").on("click",(function(t){t.preventDefault();var n=e.column($(this).attr("data-column"));n.visible(!n.visible()),n.visible()?$(this).removeClass("col-hidden"):$(this).addClass("col-hidden")}))}n.d(t,{d:function(){return i}})},31818:function(e,t,n){n.r(t),n.d(t,{initDepositAdmin:function(){return r.d},acceptOriginSaveRequest:function(){return i.LH},addAuthorizedOriginUrl:function(){return i.rl},addUnauthorizedOriginUrl:function(){return i.l6},initOriginSaveAdmin:function(){return i.ju},rejectOriginSaveRequest:function(){return i.p2},removeAcceptedOriginSaveRequest:function(){return i.iD},removeAuthorizedOriginUrl:function(){return i.S$},removePendingOriginSaveRequest:function(){return i.bU},removeRejectedOriginSaveRequest:function(){return i.ij},removeUnauthorizedOriginUrl:function(){return i.Hr}});var r=n(98921),i=n(30574)},30574:function(e,t,n){n.d(t,{ju:function(){return c},rl:function(){return h},S$:function(){return f},l6:function(){return p},Hr:function(){return v},LH:function(){return g},p2:function(){return w},bU:function(){return _},iD:function(){return b},ij:function(){return y}});var r,i,a,s,o,u=n(45149),d=n(91386);function l(e){$(e+" tbody").on("click","tr",(function(){$(this).hasClass("selected")?($(this).removeClass("selected"),$(e).closest(".tab-pane").find(".swh-action-need-selection").prop("disabled",!0)):($(e+" tr.selected").removeClass("selected"),$(this).addClass("selected"),$(e).closest(".tab-pane").find(".swh-action-need-selection").prop("disabled",!1))}))}function c(){$(document).ready((function(){$.fn.dataTable.ext.errMode="throw",r=$("#swh-authorized-origin-urls").DataTable({serverSide:!0,ajax:Urls.admin_origin_save_authorized_urls_list(),columns:[{data:"url",name:"url"}],scrollY:"50vh",scrollCollapse:!0,info:!1}),l("#swh-authorized-origin-urls"),swh.webapp.addJumpToPagePopoverToDataTable(r),i=$("#swh-unauthorized-origin-urls").DataTable({serverSide:!0,ajax:Urls.admin_origin_save_unauthorized_urls_list(),columns:[{data:"url",name:"url"}],scrollY:"50vh",scrollCollapse:!0,info:!1}),l("#swh-unauthorized-origin-urls"),swh.webapp.addJumpToPagePopoverToDataTable(i);var e=[{data:"id",name:"id",visible:!1,searchable:!1},{data:"save_request_date",name:"request_date",render:function(e,t,n){return"display"===t?new Date(e).toLocaleString():e}},{data:"visit_type",name:"visit_type"},{data:"origin_url",name:"origin_url",render:function(e,t,n){if("display"===t){var r="",i=$.fn.dataTable.render.text().display(e);if("succeed"===n.save_task_status){var a=Urls.browse_origin()+"?origin_url="+encodeURIComponent(i);n.visit_date&&(a+="&amp;timestamp="+encodeURIComponent(n.visit_date)),r+='<a href="'+a+'">'+i+"</a>"}else r+=i;return r+='&nbsp;<a href="'+i+'"><i class="mdi mdi-open-in-new" aria-hidden="true"></i></a>'}return e}}];a=$("#swh-origin-save-pending-requests").DataTable({serverSide:!0,processing:!0,language:{processing:'<img src="'+d.XC+'"></img>'},ajax:Urls.origin_save_requests_list("pending"),searchDelay:1e3,columns:e,scrollY:"50vh",scrollCollapse:!0,order:[[0,"desc"]],responsive:{details:{type:"none"}}}),l("#swh-origin-save-pending-requests"),swh.webapp.addJumpToPagePopoverToDataTable(a),o=$("#swh-origin-save-rejected-requests").DataTable({serverSide:!0,processing:!0,language:{processing:'<img src="'+d.XC+'"></img>'},ajax:Urls.origin_save_requests_list("rejected"),searchDelay:1e3,columns:e,scrollY:"50vh",scrollCollapse:!0,order:[[0,"desc"]],responsive:{details:{type:"none"}}}),l("#swh-origin-save-rejected-requests"),swh.webapp.addJumpToPagePopoverToDataTable(o),e.push({data:"save_task_status",name:"save_task_status"}),e.push({name:"info",render:function(e,t,n){return"succeed"===n.save_task_status||"failed"===n.save_task_status?'<i class="mdi mdi-information-outline swh-save-request-info" aria-hidden="true" style="cursor: pointer"onclick="swh.save.displaySaveRequestInfo(event, '+n.id+')"></i>':""}}),s=$("#swh-origin-save-accepted-requests").DataTable({serverSide:!0,processing:!0,language:{processing:'<img src="'+d.XC+'"></img>'},ajax:Urls.origin_save_requests_list("accepted"),searchDelay:1e3,columns:e,scrollY:"50vh",scrollCollapse:!0,order:[[0,"desc"]],responsive:{details:{type:"none"}}}),l("#swh-origin-save-accepted-requests"),swh.webapp.addJumpToPagePopoverToDataTable(s),$("#swh-origin-save-requests-nav-item").on("shown.bs.tab",(function(){a.draw()})),$("#swh-origin-save-url-filters-nav-item").on("shown.bs.tab",(function(){r.draw()})),$("#swh-authorized-origins-tab").on("shown.bs.tab",(function(){r.draw()})),$("#swh-unauthorized-origins-tab").on("shown.bs.tab",(function(){i.draw()})),$("#swh-save-requests-pending-tab").on("shown.bs.tab",(function(){a.draw()})),$("#swh-save-requests-accepted-tab").on("shown.bs.tab",(function(){s.draw()})),$("#swh-save-requests-rejected-tab").on("shown.bs.tab",(function(){o.draw()})),$("#swh-save-requests-pending-tab").click((function(){a.ajax.reload(null,!1)})),$("#swh-save-requests-accepted-tab").click((function(){s.ajax.reload(null,!1)})),$("#swh-save-requests-rejected-tab").click((function(){o.ajax.reload(null,!1)})),$("body").on("click",(function(e){$(e.target).parents(".popover").length>0?event.stopPropagation():0===$(e.target).parents(".swh-save-request-info").length&&$(".swh-save-request-info").popover("dispose")}))}))}function h(){var e=$("#swh-authorized-url-prefix").val(),t=Urls.admin_origin_save_add_authorized_url(e);(0,u.e_)(t).then(u.ry).then((function(){r.row.add({url:e}).draw(),$(".swh-add-authorized-origin-status").html((0,u.EM)("success","The origin url prefix has been successfully added in the authorized list.",!0))})).catch((function(e){$(".swh-add-authorized-origin-status").html((0,u.EM)("warning","The provided origin url prefix is already registered in the authorized list.",!0))}))}function f(){var e=$("#swh-authorized-origin-urls tr.selected").text();if(e){var t=Urls.admin_origin_save_remove_authorized_url(e);(0,u.e_)(t).then(u.ry).then((function(){r.row(".selected").remove().draw()})).catch((function(){}))}}function p(){var e=$("#swh-unauthorized-url-prefix").val(),t=Urls.admin_origin_save_add_unauthorized_url(e);(0,u.e_)(t).then(u.ry).then((function(){i.row.add({url:e}).draw(),$(".swh-add-unauthorized-origin-status").html((0,u.EM)("success","The origin url prefix has been successfully added in the unauthorized list.",!0))})).catch((function(){$(".swh-add-unauthorized-origin-status").html((0,u.EM)("warning","The provided origin url prefix is already registered in the unauthorized list.",!0))}))}function v(){var e=$("#swh-unauthorized-origin-urls tr.selected").text();if(e){var t=Urls.admin_origin_save_remove_unauthorized_url(e);(0,u.e_)(t).then(u.ry).then((function(){i.row(".selected").remove().draw()})).catch((function(){}))}}function g(){var e=a.row(".selected");if(e.length){swh.webapp.showModalConfirm("Accept origin save request ?","Are you sure to accept this origin save request ?",(function(){var t=e.data(),n=Urls.admin_origin_save_request_accept(t.visit_type,t.origin_url);(0,u.e_)(n).then((function(){a.ajax.reload(null,!1)}))}))}}function w(){var e=a.row(".selected");if(e.length){swh.webapp.showModalConfirm("Reject origin save request ?","Are you sure to reject this origin save request ?",(function(){var t=e.data(),n=Urls.admin_origin_save_request_reject(t.visit_type,t.origin_url);(0,u.e_)(n).then((function(){a.ajax.reload(null,!1)}))}))}}function m(e){var t=e.row(".selected");if(t.length){var n=t.data().id;swh.webapp.showModalConfirm("Remove origin save request ?","Are you sure to remove this origin save request ?",(function(){var t=Urls.admin_origin_save_request_remove(n);(0,u.e_)(t).then((function(){e.ajax.reload(null,!1)}))}))}}function _(){m(a)}function b(){m(s)}function y(){m(o)}},91386:function(e,t,n){n.d(t,{XC:function(){return r}});var r=(0,n(45149).TT)("img/swh-spinner.gif")},45149:function(e,t,n){function r(e){if(!e.ok)throw e;return e}function i(e){return"/static/"+e}function a(e,t,n){return void 0===t&&(t={}),void 0===n&&(n=null),t["X-CSRFToken"]=Cookies.get("csrftoken"),fetch(e,{credentials:"include",headers:t,method:"POST",body:n})}function s(e,t,n){void 0===n&&(n=!1);var r="",i="";return n&&(r='<button type="button" class="close" data-dismiss="alert" aria-label="Close">\n        <span aria-hidden="true">&times;</span>\n      </button>',i="alert-dismissible"),'<div class="alert alert-'+e+" "+i+'" role="alert">'+t+r+"</div>"}n.d(t,{ry:function(){return r},TT:function(){return i},e_:function(){return a},EM:function(){return s}})}},t={};function n(r){if(t[r])return t[r].exports;var i=t[r]={exports:{}};return e[r](i,i.exports,n),i.exports}return n.d=function(e,t){for(var r in t)n.o(t,r)&&!n.o(e,r)&&Object.defineProperty(e,r,{enumerable:!0,get:t[r]})},n.o=function(e,t){return Object.prototype.hasOwnProperty.call(e,t)},n.r=function(e){"undefined"!=typeof Symbol&&Symbol.toStringTag&&Object.defineProperty(e,Symbol.toStringTag,{value:"Module"}),Object.defineProperty(e,"__esModule",{value:!0})},n(31818)}()}));
//# sourceMappingURL=admin.3c8067d82a7e375249d4.js.map