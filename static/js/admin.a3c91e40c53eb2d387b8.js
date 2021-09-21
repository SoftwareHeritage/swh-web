/*! For license information please see admin.a3c91e40c53eb2d387b8.js.LICENSE.txt */
!function(e,t){"object"==typeof exports&&"object"==typeof module?module.exports=t():"function"==typeof define&&define.amd?define([],t):"object"==typeof exports?exports.swh=t():(e.swh=e.swh||{},e.swh.admin=t())}(self,(function(){return function(){var e={48926:function(e){function t(e,t,r,n,i,o,a){try{var s=e[o](a),u=s.value}catch(e){return void r(e)}s.done?t(u):Promise.resolve(u).then(n,i)}e.exports=function(e){return function(){var r=this,n=arguments;return new Promise((function(i,o){var a=e.apply(r,n);function s(e){t(a,i,o,s,u,"next",e)}function u(e){t(a,i,o,s,u,"throw",e)}s(void 0)}))}}},78279:function(e,t,r){var n=function(){return this||"object"==typeof self&&self}()||Function("return this")(),i=n.regeneratorRuntime&&Object.getOwnPropertyNames(n).indexOf("regeneratorRuntime")>=0,o=i&&n.regeneratorRuntime;if(n.regeneratorRuntime=void 0,e.exports=r(61553),i)n.regeneratorRuntime=o;else try{delete n.regeneratorRuntime}catch(e){n.regeneratorRuntime=void 0}},61553:function(e){!function(t){"use strict";var r,n=Object.prototype,i=n.hasOwnProperty,o="function"==typeof Symbol?Symbol:{},a=o.iterator||"@@iterator",s=o.asyncIterator||"@@asyncIterator",u=o.toStringTag||"@@toStringTag",c=t.regeneratorRuntime;if(c)e.exports=c;else{(c=t.regeneratorRuntime=e.exports).wrap=y;var l="suspendedStart",d="suspendedYield",f="executing",h="completed",p={},v={};v[a]=function(){return this};var g=Object.getPrototypeOf,m=g&&g(g(L([])));m&&m!==n&&i.call(m,a)&&(v=m);var w=j.prototype=_.prototype=Object.create(v);x.prototype=w.constructor=j,j.constructor=x,j[u]=x.displayName="GeneratorFunction",c.isGeneratorFunction=function(e){var t="function"==typeof e&&e.constructor;return!!t&&(t===x||"GeneratorFunction"===(t.displayName||t.name))},c.mark=function(e){return Object.setPrototypeOf?Object.setPrototypeOf(e,j):(e.__proto__=j,u in e||(e[u]="GeneratorFunction")),e.prototype=Object.create(w),e},c.awrap=function(e){return{__await:e}},$(k.prototype),k.prototype[s]=function(){return this},c.AsyncIterator=k,c.async=function(e,t,r,n){var i=new k(y(e,t,r,n));return c.isGeneratorFunction(t)?i:i.next().then((function(e){return e.done?e.value:i.next()}))},$(w),w[u]="Generator",w[a]=function(){return this},w.toString=function(){return"[object Generator]"},c.keys=function(e){var t=[];for(var r in e)t.push(r);return t.reverse(),function r(){for(;t.length;){var n=t.pop();if(n in e)return r.value=n,r.done=!1,r}return r.done=!0,r}},c.values=L,C.prototype={constructor:C,reset:function(e){if(this.prev=0,this.next=0,this.sent=this._sent=r,this.done=!1,this.delegate=null,this.method="next",this.arg=r,this.tryEntries.forEach(O),!e)for(var t in this)"t"===t.charAt(0)&&i.call(this,t)&&!isNaN(+t.slice(1))&&(this[t]=r)},stop:function(){this.done=!0;var e=this.tryEntries[0].completion;if("throw"===e.type)throw e.arg;return this.rval},dispatchException:function(e){if(this.done)throw e;var t=this;function n(n,i){return s.type="throw",s.arg=e,t.next=n,i&&(t.method="next",t.arg=r),!!i}for(var o=this.tryEntries.length-1;o>=0;--o){var a=this.tryEntries[o],s=a.completion;if("root"===a.tryLoc)return n("end");if(a.tryLoc<=this.prev){var u=i.call(a,"catchLoc"),c=i.call(a,"finallyLoc");if(u&&c){if(this.prev<a.catchLoc)return n(a.catchLoc,!0);if(this.prev<a.finallyLoc)return n(a.finallyLoc)}else if(u){if(this.prev<a.catchLoc)return n(a.catchLoc,!0)}else{if(!c)throw new Error("try statement without catch or finally");if(this.prev<a.finallyLoc)return n(a.finallyLoc)}}}},abrupt:function(e,t){for(var r=this.tryEntries.length-1;r>=0;--r){var n=this.tryEntries[r];if(n.tryLoc<=this.prev&&i.call(n,"finallyLoc")&&this.prev<n.finallyLoc){var o=n;break}}o&&("break"===e||"continue"===e)&&o.tryLoc<=t&&t<=o.finallyLoc&&(o=null);var a=o?o.completion:{};return a.type=e,a.arg=t,o?(this.method="next",this.next=o.finallyLoc,p):this.complete(a)},complete:function(e,t){if("throw"===e.type)throw e.arg;return"break"===e.type||"continue"===e.type?this.next=e.arg:"return"===e.type?(this.rval=this.arg=e.arg,this.method="return",this.next="end"):"normal"===e.type&&t&&(this.next=t),p},finish:function(e){for(var t=this.tryEntries.length-1;t>=0;--t){var r=this.tryEntries[t];if(r.finallyLoc===e)return this.complete(r.completion,r.afterLoc),O(r),p}},catch:function(e){for(var t=this.tryEntries.length-1;t>=0;--t){var r=this.tryEntries[t];if(r.tryLoc===e){var n=r.completion;if("throw"===n.type){var i=n.arg;O(r)}return i}}throw new Error("illegal catch attempt")},delegateYield:function(e,t,n){return this.delegate={iterator:L(e),resultName:t,nextLoc:n},"next"===this.method&&(this.arg=r),p}}}function y(e,t,r,n){var i=t&&t.prototype instanceof _?t:_,o=Object.create(i.prototype),a=new C(n||[]);return o._invoke=function(e,t,r){var n=l;return function(i,o){if(n===f)throw new Error("Generator is already running");if(n===h){if("throw"===i)throw o;return S()}for(r.method=i,r.arg=o;;){var a=r.delegate;if(a){var s=T(a,r);if(s){if(s===p)continue;return s}}if("next"===r.method)r.sent=r._sent=r.arg;else if("throw"===r.method){if(n===l)throw n=h,r.arg;r.dispatchException(r.arg)}else"return"===r.method&&r.abrupt("return",r.arg);n=f;var u=b(e,t,r);if("normal"===u.type){if(n=r.done?h:d,u.arg===p)continue;return{value:u.arg,done:r.done}}"throw"===u.type&&(n=h,r.method="throw",r.arg=u.arg)}}}(e,r,a),o}function b(e,t,r){try{return{type:"normal",arg:e.call(t,r)}}catch(e){return{type:"throw",arg:e}}}function _(){}function x(){}function j(){}function $(e){["next","throw","return"].forEach((function(t){e[t]=function(e){return this._invoke(t,e)}}))}function k(e){function t(r,n,o,a){var s=b(e[r],e,n);if("throw"!==s.type){var u=s.arg,c=u.value;return c&&"object"==typeof c&&i.call(c,"__await")?Promise.resolve(c.__await).then((function(e){t("next",e,o,a)}),(function(e){t("throw",e,o,a)})):Promise.resolve(c).then((function(e){u.value=e,o(u)}),(function(e){return t("throw",e,o,a)}))}a(s.arg)}var r;this._invoke=function(e,n){function i(){return new Promise((function(r,i){t(e,n,r,i)}))}return r=r?r.then(i,i):i()}}function T(e,t){var n=e.iterator[t.method];if(n===r){if(t.delegate=null,"throw"===t.method){if(e.iterator.return&&(t.method="return",t.arg=r,T(e,t),"throw"===t.method))return p;t.method="throw",t.arg=new TypeError("The iterator does not provide a 'throw' method")}return p}var i=b(n,e.iterator,t.arg);if("throw"===i.type)return t.method="throw",t.arg=i.arg,t.delegate=null,p;var o=i.arg;return o?o.done?(t[e.resultName]=o.value,t.next=e.nextLoc,"return"!==t.method&&(t.method="next",t.arg=r),t.delegate=null,p):o:(t.method="throw",t.arg=new TypeError("iterator result is not an object"),t.delegate=null,p)}function q(e){var t={tryLoc:e[0]};1 in e&&(t.catchLoc=e[1]),2 in e&&(t.finallyLoc=e[2],t.afterLoc=e[3]),this.tryEntries.push(t)}function O(e){var t=e.completion||{};t.type="normal",delete t.arg,e.completion=t}function C(e){this.tryEntries=[{tryLoc:"root"}],e.forEach(q,this),this.reset(!0)}function L(e){if(e){var t=e[a];if(t)return t.call(e);if("function"==typeof e.next)return e;if(!isNaN(e.length)){var n=-1,o=function t(){for(;++n<e.length;)if(i.call(e,n))return t.value=e[n],t.done=!1,t;return t.value=r,t.done=!0,t};return o.next=o}}return{next:S}}function S(){return{value:r,done:!0}}}(function(){return this||"object"==typeof self&&self}()||Function("return this")())},87757:function(e,t,r){e.exports=r(78279)},53793:function(e,t,r){"use strict";function n(e,t){if("display"===t&&(e&&e.startsWith("swh")))return'<a href="'+Urls.browse_swhid(e)+'">'+e.replace(/;/g,";<br/>")+"</a>";return e}function i(){var e;$(document).ready((function(){$.fn.dataTable.ext.errMode="none",e=$("#swh-admin-deposit-list").on("error.dt",(function(e,t,r,n){$("#swh-admin-deposit-list-error").text(n)})).DataTable({serverSide:!0,processing:!0,dom:'<<"d-flex justify-content-between align-items-center"f<"#list-exclude">l>rt<"bottom"ip>>',ajax:{url:Urls.admin_deposit_list(),data:function(e){e.excludePattern=$("#swh-admin-deposit-list-exclude-filter").val()}},columns:[{data:"id",name:"id"},{data:"swhid_context",name:"swhid_context",render:function(e,t,r){if(e&&"display"===t){var n=";origin=",i=e.indexOf(n);if(-1!==i){var o=e.slice(i+n.length),a=o.indexOf(";");return-1!==a&&(o=o.slice(0,a)),'<a href="'+o+'">'+o+"</a>"}}return e}},{data:"reception_date",name:"reception_date",render:function(e,t,r){return"display"===t?new Date(e).toLocaleString():e}},{data:"status",name:"status"},{data:"status_detail",name:"status_detail",render:function(e,t,r){if("display"===t&&e){var n=e;return"object"==typeof e&&(n=JSON.stringify(e,null,4)),'<div style="width: 200px; white-space: pre; overflow-x: auto;">'+n+"</div>"}return e},orderable:!1,visible:!1},{data:"swhid",name:"swhid",render:function(e,t,r){return n(e,t)},orderable:!1,visible:!1},{data:"swhid_context",name:"swhid_context",render:function(e,t,r){return n(e,t)},orderable:!1,visible:!1}],scrollX:!0,scrollY:"50vh",scrollCollapse:!0,order:[[0,"desc"]]}),$("div#list-exclude").html('<div id="swh-admin-deposit-list-exclude-wrapper">\n    <div id="swh-admin-deposit-list-exclude-div-wrapper" class="dataTables_filter">\n      <label>\n        Exclude:<input id="swh-admin-deposit-list-exclude-filter"\n                       type="search"\n                       value="check-deposit"\n                       class="form-control form-control-sm"\n                       placeholder="exclude-pattern" aria-controls="swh-admin-deposit-list">\n          </input>\n      </label>\n    </div>\n  </div>\n'),$("#swh-admin-deposit-list-exclude-filter").keyup((function(){e.draw()})),e.draw()})),$("a.toggle-col").on("click",(function(t){t.preventDefault();var r=e.column($(this).attr("data-column"));r.visible(!r.visible()),r.visible()?$(this).removeClass("col-hidden"):$(this).addClass("col-hidden")}))}r.d(t,{d:function(){return i}})},49880:function(e,t,r){"use strict";r.d(t,{ju:function(){return v},rl:function(){return g},S$:function(){return w},l6:function(){return b},Hr:function(){return x},LH:function(){return k},p2:function(){return T},bU:function(){return O},iD:function(){return C},ij:function(){return L}});var n,i,o,a,s,u=r(48926),c=r.n(u),l=r(87757),d=r.n(l),f=r(55423),h=r(80893);function p(e){$(e+" tbody").on("click","tr",(function(){$(this).hasClass("selected")?($(this).removeClass("selected"),$(e).closest(".tab-pane").find(".swh-action-need-selection").prop("disabled",!0)):($(e+" tr.selected").removeClass("selected"),$(this).addClass("selected"),$(e).closest(".tab-pane").find(".swh-action-need-selection").prop("disabled",!1))}))}function v(){$(document).ready((function(){$.fn.dataTable.ext.errMode="throw",n=$("#swh-authorized-origin-urls").DataTable({serverSide:!0,ajax:Urls.admin_origin_save_authorized_urls_list(),columns:[{data:"url",name:"url"}],scrollY:"50vh",scrollCollapse:!0,info:!1}),p("#swh-authorized-origin-urls"),swh.webapp.addJumpToPagePopoverToDataTable(n),i=$("#swh-unauthorized-origin-urls").DataTable({serverSide:!0,ajax:Urls.admin_origin_save_unauthorized_urls_list(),columns:[{data:"url",name:"url"}],scrollY:"50vh",scrollCollapse:!0,info:!1}),p("#swh-unauthorized-origin-urls"),swh.webapp.addJumpToPagePopoverToDataTable(i);var e=[{data:"id",name:"id",visible:!1,searchable:!1},{data:"save_request_date",name:"request_date",render:function(e,t,r){return"display"===t?new Date(e).toLocaleString():e}},{data:"visit_type",name:"visit_type"},{data:"origin_url",name:"origin_url",render:function(e,t,r){if("display"===t){var n="",i=$.fn.dataTable.render.text().display(e);if("succeeded"===r.save_task_status){var o=Urls.browse_origin()+"?origin_url="+encodeURIComponent(i);r.visit_date&&(o+="&amp;timestamp="+encodeURIComponent(r.visit_date)),n+='<a href="'+o+'">'+i+"</a>"}else n+=i;return n+='&nbsp;<a href="'+i+'" target="_blank" rel="noopener noreferrer"><i class="mdi mdi-open-in-new" aria-hidden="true"></i></a>'}return e}}];o=$("#swh-origin-save-pending-requests").DataTable({serverSide:!0,processing:!0,language:{processing:'<img src="'+h.XC+'"></img>'},ajax:Urls.origin_save_requests_list("pending"),searchDelay:1e3,columns:e,scrollY:"50vh",scrollCollapse:!0,order:[[0,"desc"]],responsive:{details:{type:"none"}}}),p("#swh-origin-save-pending-requests"),swh.webapp.addJumpToPagePopoverToDataTable(o),s=$("#swh-origin-save-rejected-requests").DataTable({serverSide:!0,processing:!0,language:{processing:'<img src="'+h.XC+'"></img>'},ajax:Urls.origin_save_requests_list("rejected"),searchDelay:1e3,columns:e,scrollY:"50vh",scrollCollapse:!0,order:[[0,"desc"]],responsive:{details:{type:"none"}}}),p("#swh-origin-save-rejected-requests"),swh.webapp.addJumpToPagePopoverToDataTable(s),e.push({data:"save_task_status",name:"save_task_status"}),e.push({name:"info",render:function(e,t,r){return"succeeded"===r.save_task_status||"failed"===r.save_task_status?'<i class="mdi mdi-information-outline swh-save-request-info" aria-hidden="true" style="cursor: pointer"onclick="swh.save.displaySaveRequestInfo(event, '+r.id+')"></i>':""}}),a=$("#swh-origin-save-accepted-requests").DataTable({serverSide:!0,processing:!0,language:{processing:'<img src="'+h.XC+'"></img>'},ajax:Urls.origin_save_requests_list("accepted"),searchDelay:1e3,columns:e,scrollY:"50vh",scrollCollapse:!0,order:[[0,"desc"]],responsive:{details:{type:"none"}}}),p("#swh-origin-save-accepted-requests"),swh.webapp.addJumpToPagePopoverToDataTable(a),$("#swh-origin-save-requests-nav-item").on("shown.bs.tab",(function(){o.draw()})),$("#swh-origin-save-url-filters-nav-item").on("shown.bs.tab",(function(){n.draw()})),$("#swh-authorized-origins-tab").on("shown.bs.tab",(function(){n.draw()})),$("#swh-unauthorized-origins-tab").on("shown.bs.tab",(function(){i.draw()})),$("#swh-save-requests-pending-tab").on("shown.bs.tab",(function(){o.draw()})),$("#swh-save-requests-accepted-tab").on("shown.bs.tab",(function(){a.draw()})),$("#swh-save-requests-rejected-tab").on("shown.bs.tab",(function(){s.draw()})),$("#swh-save-requests-pending-tab").click((function(){o.ajax.reload(null,!1)})),$("#swh-save-requests-accepted-tab").click((function(){a.ajax.reload(null,!1)})),$("#swh-save-requests-rejected-tab").click((function(){s.ajax.reload(null,!1)})),$("body").on("click",(function(e){$(e.target).parents(".popover").length>0?e.stopPropagation():0===$(e.target).parents(".swh-save-request-info").length&&$(".swh-save-request-info").popover("dispose")}))}))}function g(){return m.apply(this,arguments)}function m(){return(m=c()(d().mark((function e(){var t,r,i;return d().wrap((function(e){for(;;)switch(e.prev=e.next){case 0:return t=$("#swh-authorized-url-prefix").val(),r=Urls.admin_origin_save_add_authorized_url(t),e.prev=2,e.next=5,(0,f.e_)(r);case 5:i=e.sent,(0,f.ry)(i),n.row.add({url:t}).draw(),$(".swh-add-authorized-origin-status").html((0,f.EM)("success","The origin url prefix has been successfully added in the authorized list.",!0)),e.next=14;break;case 11:e.prev=11,e.t0=e.catch(2),$(".swh-add-authorized-origin-status").html((0,f.EM)("warning","The provided origin url prefix is already registered in the authorized list.",!0));case 14:case"end":return e.stop()}}),e,null,[[2,11]])})))).apply(this,arguments)}function w(){return y.apply(this,arguments)}function y(){return(y=c()(d().mark((function e(){var t,r,i;return d().wrap((function(e){for(;;)switch(e.prev=e.next){case 0:if(!(t=$("#swh-authorized-origin-urls tr.selected").text())){e.next=13;break}return r=Urls.admin_origin_save_remove_authorized_url(t),e.prev=3,e.next=6,(0,f.e_)(r);case 6:i=e.sent,(0,f.ry)(i),n.row(".selected").remove().draw(),e.next=13;break;case 11:e.prev=11,e.t0=e.catch(3);case 13:case"end":return e.stop()}}),e,null,[[3,11]])})))).apply(this,arguments)}function b(){return _.apply(this,arguments)}function _(){return(_=c()(d().mark((function e(){var t,r,n;return d().wrap((function(e){for(;;)switch(e.prev=e.next){case 0:return t=$("#swh-unauthorized-url-prefix").val(),r=Urls.admin_origin_save_add_unauthorized_url(t),e.prev=2,e.next=5,(0,f.e_)(r);case 5:n=e.sent,(0,f.ry)(n),i.row.add({url:t}).draw(),$(".swh-add-unauthorized-origin-status").html((0,f.EM)("success","The origin url prefix has been successfully added in the unauthorized list.",!0)),e.next=14;break;case 11:e.prev=11,e.t0=e.catch(2),$(".swh-add-unauthorized-origin-status").html((0,f.EM)("warning","The provided origin url prefix is already registered in the unauthorized list.",!0));case 14:case"end":return e.stop()}}),e,null,[[2,11]])})))).apply(this,arguments)}function x(){return j.apply(this,arguments)}function j(){return(j=c()(d().mark((function e(){var t,r,n;return d().wrap((function(e){for(;;)switch(e.prev=e.next){case 0:if(!(t=$("#swh-unauthorized-origin-urls tr.selected").text())){e.next=14;break}return r=Urls.admin_origin_save_remove_unauthorized_url(t),e.prev=3,e.next=6,(0,f.e_)(r);case 6:n=e.sent,(0,f.ry)(n),i.row(".selected").remove().draw(),e.next=13;break;case 11:e.prev=11,e.t0=e.catch(3);case 13:case 14:case"end":return e.stop()}}),e,null,[[3,11]])})))).apply(this,arguments)}function k(){var e=o.row(".selected");if(e.length){var t=function(){var t=c()(d().mark((function t(){var r,n;return d().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:return r=e.data(),n=Urls.admin_origin_save_request_accept(r.visit_type,r.origin_url),t.next=4,(0,f.e_)(n);case 4:o.ajax.reload(null,!1);case 5:case"end":return t.stop()}}),t)})));return function(){return t.apply(this,arguments)}}();swh.webapp.showModalConfirm("Accept origin save request ?","Are you sure to accept this origin save request ?",t)}}function T(){var e=o.row(".selected");if(e.length){var t=function(){var t=c()(d().mark((function t(){var r,n;return d().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:return r=e.data(),n=Urls.admin_origin_save_request_reject(r.visit_type,r.origin_url),t.next=4,(0,f.e_)(n);case 4:o.ajax.reload(null,!1);case 5:case"end":return t.stop()}}),t)})));return function(){return t.apply(this,arguments)}}();swh.webapp.showModalConfirm("Reject origin save request ?","Are you sure to reject this origin save request ?",t)}}function q(e){var t=e.row(".selected");if(t.length){var r=t.data().id,n=function(){var t=c()(d().mark((function t(){var n;return d().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:return n=Urls.admin_origin_save_request_remove(r),t.next=3,(0,f.e_)(n);case 3:e.ajax.reload(null,!1);case 4:case"end":return t.stop()}}),t)})));return function(){return t.apply(this,arguments)}}();swh.webapp.showModalConfirm("Remove origin save request ?","Are you sure to remove this origin save request ?",n)}}function O(){q(o)}function C(){q(a)}function L(){q(s)}},80893:function(e,t,r){"use strict";r.d(t,{XC:function(){return n}});var n=(0,r(55423).TT)("img/swh-spinner.gif")},55423:function(e,t,r){"use strict";r.d(t,{ry:function(){return i},TT:function(){return o},e_:function(){return a},EM:function(){return s}});r(48926),r(87757);var n=r(31955);function i(e){if(!e.ok)throw e;return e}function o(e){return"/static/"+e}function a(e,t,r){return void 0===t&&(t={}),void 0===r&&(r=null),t["X-CSRFToken"]=n.Z.get("csrftoken"),fetch(e,{credentials:"include",headers:t,method:"POST",body:r})}function s(e,t,r){void 0===r&&(r=!1);var n="",i="";return r&&(n='<button type="button" class="close" data-dismiss="alert" aria-label="Close">\n        <span aria-hidden="true">&times;</span>\n      </button>',i="alert-dismissible"),'<div class="alert alert-'+e+" "+i+'" role="alert">'+t+n+"</div>"}},31955:function(e,t){"use strict";function r(e){for(var t=1;t<arguments.length;t++){var r=arguments[t];for(var n in r)e[n]=r[n]}return e}var n=function e(t,n){function i(e,i,o){if("undefined"!=typeof document){"number"==typeof(o=r({},n,o)).expires&&(o.expires=new Date(Date.now()+864e5*o.expires)),o.expires&&(o.expires=o.expires.toUTCString()),e=encodeURIComponent(e).replace(/%(2[346B]|5E|60|7C)/g,decodeURIComponent).replace(/[()]/g,escape);var a="";for(var s in o)o[s]&&(a+="; "+s,!0!==o[s]&&(a+="="+o[s].split(";")[0]));return document.cookie=e+"="+t.write(i,e)+a}}return Object.create({set:i,get:function(e){if("undefined"!=typeof document&&(!arguments.length||e)){for(var r=document.cookie?document.cookie.split("; "):[],n={},i=0;i<r.length;i++){var o=r[i].split("="),a=o.slice(1).join("=");try{var s=decodeURIComponent(o[0]);if(n[s]=t.read(a,s),e===s)break}catch(e){}}return e?n[e]:n}},remove:function(e,t){i(e,"",r({},t,{expires:-1}))},withAttributes:function(t){return e(this.converter,r({},this.attributes,t))},withConverter:function(t){return e(r({},this.converter,t),this.attributes)}},{attributes:{value:Object.freeze(n)},converter:{value:Object.freeze(t)}})}({read:function(e){return'"'===e[0]&&(e=e.slice(1,-1)),e.replace(/(%[\dA-F]{2})+/gi,decodeURIComponent)},write:function(e){return encodeURIComponent(e).replace(/%(2[346BF]|3[AC-F]|40|5[BDE]|60|7[BCD])/g,decodeURIComponent)}},{path:"/"});t.Z=n}},t={};function r(n){var i=t[n];if(void 0!==i)return i.exports;var o=t[n]={exports:{}};return e[n](o,o.exports,r),o.exports}r.n=function(e){var t=e&&e.__esModule?function(){return e.default}:function(){return e};return r.d(t,{a:t}),t},r.d=function(e,t){for(var n in t)r.o(t,n)&&!r.o(e,n)&&Object.defineProperty(e,n,{enumerable:!0,get:t[n]})},r.o=function(e,t){return Object.prototype.hasOwnProperty.call(e,t)},r.r=function(e){"undefined"!=typeof Symbol&&Symbol.toStringTag&&Object.defineProperty(e,Symbol.toStringTag,{value:"Module"}),Object.defineProperty(e,"__esModule",{value:!0})};var n={};return function(){"use strict";r.r(n),r.d(n,{initDepositAdmin:function(){return e.d},acceptOriginSaveRequest:function(){return t.LH},addAuthorizedOriginUrl:function(){return t.rl},addUnauthorizedOriginUrl:function(){return t.l6},initOriginSaveAdmin:function(){return t.ju},rejectOriginSaveRequest:function(){return t.p2},removeAcceptedOriginSaveRequest:function(){return t.iD},removeAuthorizedOriginUrl:function(){return t.S$},removePendingOriginSaveRequest:function(){return t.bU},removeRejectedOriginSaveRequest:function(){return t.ij},removeUnauthorizedOriginUrl:function(){return t.Hr}});var e=r(53793),t=r(49880)}(),n}()}));
//# sourceMappingURL=admin.a3c91e40c53eb2d387b8.js.map