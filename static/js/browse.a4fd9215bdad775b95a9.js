/*! For license information please see browse.a4fd9215bdad775b95a9.js.LICENSE.txt */
!function(t,e){"object"==typeof exports&&"object"==typeof module?module.exports=e():"function"==typeof define&&define.amd?define([],e):"object"==typeof exports?exports.swh=e():(t.swh=t.swh||{},t.swh.browse=e())}(self,(function(){return function(){var t={48926:function(t){function e(t,e,n,r,o,i,a){try{var s=t[i](a),c=s.value}catch(t){return void n(t)}s.done?e(c):Promise.resolve(c).then(r,o)}t.exports=function(t){return function(){var n=this,r=arguments;return new Promise((function(o,i){var a=t.apply(n,r);function s(t){e(a,o,i,s,c,"next",t)}function c(t){e(a,o,i,s,c,"throw",t)}s(void 0)}))}}},78279:function(t,e,n){var r=function(){return this||"object"==typeof self&&self}()||Function("return this")(),o=r.regeneratorRuntime&&Object.getOwnPropertyNames(r).indexOf("regeneratorRuntime")>=0,i=o&&r.regeneratorRuntime;if(r.regeneratorRuntime=void 0,t.exports=n(61553),o)r.regeneratorRuntime=i;else try{delete r.regeneratorRuntime}catch(t){r.regeneratorRuntime=void 0}},61553:function(t){!function(e){"use strict";var n,r=Object.prototype,o=r.hasOwnProperty,i="function"==typeof Symbol?Symbol:{},a=i.iterator||"@@iterator",s=i.asyncIterator||"@@asyncIterator",c=i.toStringTag||"@@toStringTag",u=e.regeneratorRuntime;if(u)t.exports=u;else{(u=e.regeneratorRuntime=t.exports).wrap=y;var l="suspendedStart",h="suspendedYield",f="executing",d="completed",p={},v={};v[a]=function(){return this};var g=Object.getPrototypeOf,w=g&&g(g(L([])));w&&w!==r&&o.call(w,a)&&(v=w);var m=$.prototype=x.prototype=Object.create(v);k.prototype=m.constructor=$,$.constructor=k,$[c]=k.displayName="GeneratorFunction",u.isGeneratorFunction=function(t){var e="function"==typeof t&&t.constructor;return!!e&&(e===k||"GeneratorFunction"===(e.displayName||e.name))},u.mark=function(t){return Object.setPrototypeOf?Object.setPrototypeOf(t,$):(t.__proto__=$,c in t||(t[c]="GeneratorFunction")),t.prototype=Object.create(m),t},u.awrap=function(t){return{__await:t}},E(S.prototype),S.prototype[s]=function(){return this},u.AsyncIterator=S,u.async=function(t,e,n,r){var o=new S(y(t,e,n,r));return u.isGeneratorFunction(e)?o:o.next().then((function(t){return t.done?t.value:o.next()}))},E(m),m[c]="Generator",m[a]=function(){return this},m.toString=function(){return"[object Generator]"},u.keys=function(t){var e=[];for(var n in t)e.push(n);return e.reverse(),function n(){for(;e.length;){var r=e.pop();if(r in t)return n.value=r,n.done=!1,n}return n.done=!0,n}},u.values=L,C.prototype={constructor:C,reset:function(t){if(this.prev=0,this.next=0,this.sent=this._sent=n,this.done=!1,this.delegate=null,this.method="next",this.arg=n,this.tryEntries.forEach(T),!t)for(var e in this)"t"===e.charAt(0)&&o.call(this,e)&&!isNaN(+e.slice(1))&&(this[e]=n)},stop:function(){this.done=!0;var t=this.tryEntries[0].completion;if("throw"===t.type)throw t.arg;return this.rval},dispatchException:function(t){if(this.done)throw t;var e=this;function r(r,o){return s.type="throw",s.arg=t,e.next=r,o&&(e.method="next",e.arg=n),!!o}for(var i=this.tryEntries.length-1;i>=0;--i){var a=this.tryEntries[i],s=a.completion;if("root"===a.tryLoc)return r("end");if(a.tryLoc<=this.prev){var c=o.call(a,"catchLoc"),u=o.call(a,"finallyLoc");if(c&&u){if(this.prev<a.catchLoc)return r(a.catchLoc,!0);if(this.prev<a.finallyLoc)return r(a.finallyLoc)}else if(c){if(this.prev<a.catchLoc)return r(a.catchLoc,!0)}else{if(!u)throw new Error("try statement without catch or finally");if(this.prev<a.finallyLoc)return r(a.finallyLoc)}}}},abrupt:function(t,e){for(var n=this.tryEntries.length-1;n>=0;--n){var r=this.tryEntries[n];if(r.tryLoc<=this.prev&&o.call(r,"finallyLoc")&&this.prev<r.finallyLoc){var i=r;break}}i&&("break"===t||"continue"===t)&&i.tryLoc<=e&&e<=i.finallyLoc&&(i=null);var a=i?i.completion:{};return a.type=t,a.arg=e,i?(this.method="next",this.next=i.finallyLoc,p):this.complete(a)},complete:function(t,e){if("throw"===t.type)throw t.arg;return"break"===t.type||"continue"===t.type?this.next=t.arg:"return"===t.type?(this.rval=this.arg=t.arg,this.method="return",this.next="end"):"normal"===t.type&&e&&(this.next=e),p},finish:function(t){for(var e=this.tryEntries.length-1;e>=0;--e){var n=this.tryEntries[e];if(n.finallyLoc===t)return this.complete(n.completion,n.afterLoc),T(n),p}},catch:function(t){for(var e=this.tryEntries.length-1;e>=0;--e){var n=this.tryEntries[e];if(n.tryLoc===t){var r=n.completion;if("throw"===r.type){var o=r.arg;T(n)}return o}}throw new Error("illegal catch attempt")},delegateYield:function(t,e,r){return this.delegate={iterator:L(t),resultName:e,nextLoc:r},"next"===this.method&&(this.arg=n),p}}}function y(t,e,n,r){var o=e&&e.prototype instanceof x?e:x,i=Object.create(o.prototype),a=new C(r||[]);return i._invoke=function(t,e,n){var r=l;return function(o,i){if(r===f)throw new Error("Generator is already running");if(r===d){if("throw"===o)throw i;return j()}for(n.method=o,n.arg=i;;){var a=n.delegate;if(a){var s=_(a,n);if(s){if(s===p)continue;return s}}if("next"===n.method)n.sent=n._sent=n.arg;else if("throw"===n.method){if(r===l)throw r=d,n.arg;n.dispatchException(n.arg)}else"return"===n.method&&n.abrupt("return",n.arg);r=f;var c=b(t,e,n);if("normal"===c.type){if(r=n.done?d:h,c.arg===p)continue;return{value:c.arg,done:n.done}}"throw"===c.type&&(r=d,n.method="throw",n.arg=c.arg)}}}(t,n,a),i}function b(t,e,n){try{return{type:"normal",arg:t.call(e,n)}}catch(t){return{type:"throw",arg:t}}}function x(){}function k(){}function $(){}function E(t){["next","throw","return"].forEach((function(e){t[e]=function(t){return this._invoke(e,t)}}))}function S(t){function e(n,r,i,a){var s=b(t[n],t,r);if("throw"!==s.type){var c=s.arg,u=c.value;return u&&"object"==typeof u&&o.call(u,"__await")?Promise.resolve(u.__await).then((function(t){e("next",t,i,a)}),(function(t){e("throw",t,i,a)})):Promise.resolve(u).then((function(t){c.value=t,i(c)}),(function(t){return e("throw",t,i,a)}))}a(s.arg)}var n;this._invoke=function(t,r){function o(){return new Promise((function(n,o){e(t,r,n,o)}))}return n=n?n.then(o,o):o()}}function _(t,e){var r=t.iterator[e.method];if(r===n){if(e.delegate=null,"throw"===e.method){if(t.iterator.return&&(e.method="return",e.arg=n,_(t,e),"throw"===e.method))return p;e.method="throw",e.arg=new TypeError("The iterator does not provide a 'throw' method")}return p}var o=b(r,t.iterator,e.arg);if("throw"===o.type)return e.method="throw",e.arg=o.arg,e.delegate=null,p;var i=o.arg;return i?i.done?(e[t.resultName]=i.value,e.next=t.nextLoc,"return"!==e.method&&(e.method="next",e.arg=n),e.delegate=null,p):i:(e.method="throw",e.arg=new TypeError("iterator result is not an object"),e.delegate=null,p)}function O(t){var e={tryLoc:t[0]};1 in t&&(e.catchLoc=t[1]),2 in t&&(e.finallyLoc=t[2],e.afterLoc=t[3]),this.tryEntries.push(e)}function T(t){var e=t.completion||{};e.type="normal",delete e.arg,t.completion=e}function C(t){this.tryEntries=[{tryLoc:"root"}],t.forEach(O,this),this.reset(!0)}function L(t){if(t){var e=t[a];if(e)return e.call(t);if("function"==typeof t.next)return t;if(!isNaN(t.length)){var r=-1,i=function e(){for(;++r<t.length;)if(o.call(t,r))return e.value=t[r],e.done=!1,e;return e.value=n,e.done=!0,e};return i.next=i}}return{next:j}}function j(){return{value:n,done:!0}}}(function(){return this||"object"==typeof self&&self}()||Function("return this")())},87757:function(t,e,n){t.exports=n(78279)},12312:function(t,e,n){"use strict";n.d(e,{E:function(){return o}});var r=n(80893);function o(){window.location.pathname===Urls.browse_origin_visits()?$("#swh-browse-origin-visits-nav-link").addClass("active"):window.location.pathname===Urls.browse_origin_branches()||window.location.pathname===Urls.browse_snapshot_branches()?$("#swh-browse-snapshot-branches-nav-link").addClass("active"):window.location.pathname===Urls.browse_origin_releases()||window.location.pathname===Urls.browse_snapshot_releases()?$("#swh-browse-snapshot-releases-nav-link").addClass("active"):$("#swh-browse-code-nav-link").addClass("active")}$(document).ready((function(){$(".dropdown-submenu a.dropdown-item").on("click",(function(t){$(t.target).next("div").toggle(),"none"!==$(t.target).next("div").css("display")?$(t.target).focus():$(t.target).blur(),t.stopPropagation(),t.preventDefault()})),$(".swh-popover-toggler").popover({boundary:"viewport",container:"body",html:!0,placement:function(){return $(window).width()<r.Fg?"top":"right"},template:'<div class="popover" role="tooltip">\n                 <div class="arrow"></div>\n                 <h3 class="popover-header"></h3>\n                 <div class="popover-body swh-popover"></div>\n               </div>',content:function(){var t=$(this).attr("data-popover-content");return $(t).children(".popover-body").remove().html()},title:function(){var t=$(this).attr("data-popover-content");return $(t).children(".popover-heading").html()},offset:"50vh",sanitize:!1}),$(".swh-vault-menu a.dropdown-item").on("click",(function(t){$(".swh-popover-toggler").popover("hide")})),$(".swh-popover-toggler").on("show.bs.popover",(function(t){$(".swh-popover-toggler:not(#"+t.currentTarget.id+")").popover("hide"),$(".swh-vault-menu .dropdown-menu").hide()})),$(".swh-actions-dropdown").on("hide.bs.dropdown",(function(){$(".swh-vault-menu .dropdown-menu").hide(),$(".swh-popover-toggler").popover("hide")})),$("body").on("click",(function(t){$(t.target).parents(".swh-popover").length&&t.stopPropagation()}))}))},14444:function(t,e,n){"use strict";n.d(e,{A:function(){return E}});var r=n(48926),o=n.n(r),i=n(87757),a=n.n(i),s=n(55423);function c(t,e){var n="undefined"!=typeof Symbol&&t[Symbol.iterator]||t["@@iterator"];if(n)return(n=n.call(t)).next.bind(n);if(Array.isArray(t)||(n=function(t,e){if(!t)return;if("string"==typeof t)return u(t,e);var n=Object.prototype.toString.call(t).slice(8,-1);"Object"===n&&t.constructor&&(n=t.constructor.name);if("Map"===n||"Set"===n)return Array.from(t);if("Arguments"===n||/^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n))return u(t,e)}(t))||e&&t&&"number"==typeof t.length){n&&(t=n);var r=0;return function(){return r>=t.length?{done:!0}:{done:!1,value:t[r++]}}}throw new TypeError("Invalid attempt to iterate non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.")}function u(t,e){(null==e||e>t.length)&&(e=t.length);for(var n=0,r=new Array(e);n<e;n++)r[n]=t[n];return r}var l=[],h=null,f=null,d=!1;function p(t){return t.match(/<(.+)>; rel="next"/)[1]}function v(){setTimeout((function(){$("#origin-search-results tbody tr").removeAttr("style")}))}function g(){$("#origin-search-results tbody tr").remove()}function w(t){return m.apply(this,arguments)}function m(){return(m=o()(a().mark((function t(e){var n,r,o,i,s,u,f,p,w,m,y,b,x,k,E;return a().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:if(!(e.length>0)){t.next=17;break}for($("#swh-origin-search-results").show(),$("#swh-no-result").hide(),g(),n=$("#origin-search-results tbody"),r=[],o=c(e.entries());!(i=o()).done;)s=i.value,u=s[0],f=s[1],p=Urls.browse_origin()+"?origin_url="+encodeURIComponent(f.url),w='<tr id="origin-'+u+'" class="swh-search-result-entry swh-tr-hover-highlight">',w+='<td id="visit-type-origin-'+u+'" class="swh-origin-visit-type" style="width: 120px;"><i title="Checking software origin type" class="mdi mdi-sync mdi-spin mdi-fw"></i>Checking</td>',w+='<td style="white-space: nowrap;"><a href="'+p+'">'+f.url+"</a></td>",w+='<td class="swh-visit-status" id="visit-status-origin-'+u+'"><i title="Checking archiving status" class="mdi mdi-sync mdi-spin mdi-fw"></i>Checking</td>',w+="</tr>",n.append(w),m=Urls.api_1_origin_visit_latest(f.url),m+="?require_snapshot=true",r.push(fetch(m));return t.next=9,Promise.all(r);case 9:return y=t.sent,t.next=12,Promise.all(y.map((function(t){return t.json()})));case 12:for(b=t.sent,x=0;x<y.length;++x)k=y[x],E=b[x],404!==k.status&&E.type?($("#visit-type-origin-"+x).html(E.type),$("#visit-status-origin-"+x).html('<i title="Software origin has been archived by Software Heritage" class="mdi mdi-check-bold mdi-fw"></i>Archived')):($("#visit-type-origin-"+x).html("unknown"),$("#visit-status-origin-"+x).html('<i title="Software origin archival by Software Heritage is pending" class="mdi mdi-close-thick mdi-fw"></i>Pending archival'),$("#swh-filter-empty-visits").prop("checked")&&$("#origin-"+x).remove());v(),t.next=20;break;case 17:$("#swh-origin-search-results").hide(),$("#swh-no-result").text("No origins matching the search criteria were found."),$("#swh-no-result").show();case 20:null===h?$("#origins-next-results-button").addClass("disabled"):$("#origins-next-results-button").removeClass("disabled"),0===l.length?$("#origins-prev-results-button").addClass("disabled"):$("#origins-prev-results-button").removeClass("disabled"),d=!1,setTimeout((function(){window.scrollTo(0,0)}));case 24:case"end":return t.stop()}}),t)})))).apply(this,arguments)}function y(t,e){var n;$("#swh-search-origin-metadata").prop("checked")?(n=new URL(Urls.api_1_origin_metadata_search(),window.location)).searchParams.append("fulltext",t):n=new URL(Urls.api_1_origin_search(t),window.location);var r=$("#swh-search-origins-with-visit").prop("checked");n.searchParams.append("limit",e),n.searchParams.append("with_visit",r);var o=$("#swh-search-visit-type").val();"any"!==o&&n.searchParams.append("visit_type",o),b(n.toString())}function b(t){return x.apply(this,arguments)}function x(){return(x=o()(a().mark((function t(e){var n,r,o;return a().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:return g(),$(".swh-loading").addClass("show"),t.prev=2,t.next=5,fetch(e);case 5:return n=t.sent,(0,s.ry)(n),t.next=9,n.json();case 9:r=t.sent,f=e,h=null,n.headers.has("Link")&&void 0!==(o=p(n.headers.get("Link")))&&(h=o),$(".swh-loading").removeClass("show"),w(r),t.next=24;break;case 17:t.prev=17,t.t0=t.catch(2),$(".swh-loading").removeClass("show"),d=!1,$("#swh-origin-search-results").hide(),$("#swh-no-result").text("Error "+t.t0.status+": "+t.t0.statusText),$("#swh-no-result").show();case 24:case"end":return t.stop()}}),t,null,[[2,17]])})))).apply(this,arguments)}function k(){return(k=o()(a().mark((function t(){var e,n,r,o,i;return a().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:if($("#swh-no-result").hide(),e=$("#swh-origins-url-patterns").val(),d=!0,!e.startsWith("swh:")){t.next=27;break}return t.prev=4,n=Urls.api_1_resolve_swhid(e),t.next=8,fetch(n);case 8:return r=t.sent,(0,s.ry)(r),t.next=12,r.json();case 12:o=t.sent,window.location=o.browse_url,t.next=25;break;case 16:return t.prev=16,t.t0=t.catch(4),t.next=20,t.t0.json();case 20:i=t.sent,$("#swh-origin-search-results").hide(),$(".swh-search-pagination").hide(),$("#swh-no-result").text(i.reason),$("#swh-no-result").show();case 25:t.next=36;break;case 27:return t.next=29,(0,s.Sv)(e);case 29:if(!t.sent){t.next=33;break}window.location.href=Urls.browse_origin()+"?origin_url="+encodeURIComponent(e),t.next=36;break;case 33:$("#swh-origin-search-results").show(),$(".swh-search-pagination").show(),y(e,100);case 36:case"end":return t.stop()}}),t,null,[[4,16]])})))).apply(this,arguments)}function E(){$(document).ready((function(){$("#swh-search-origins").submit((function(t){if(t.preventDefault(),t.target.checkValidity()){$(t.target).removeClass("was-validated");var e=$("#swh-origins-url-patterns").val().trim(),n=$("#swh-search-origins-with-visit").prop("checked"),r=$("#swh-filter-empty-visits").prop("checked"),o=$("#swh-search-origin-metadata").prop("checked"),i=$("#swh-search-visit-type").val(),a=new URLSearchParams;a.append("q",e),n&&a.append("with_visit",n),r&&a.append("with_content",r),o&&a.append("search_metadata",o),"any"!==i&&a.append("visit_type",i),window.location=Urls.browse_search()+"?"+a.toString()}else $(t.target).addClass("was-validated")})),$("#origins-next-results-button").click((function(t){$("#origins-next-results-button").hasClass("disabled")||d||(d=!0,l.push(f),b(h),t.preventDefault())})),$("#origins-prev-results-button").click((function(t){$("#origins-prev-results-button").hasClass("disabled")||d||(d=!0,b(l.pop()),t.preventDefault())}));var t=new URLSearchParams(window.location.search),e=t.get("q"),n=t.has("with_visit"),r=t.has("with_content"),o=t.has("search_metadata"),i=t.get("visit_type");e&&($("#swh-origins-url-patterns").val(e),$("#swh-search-origins-with-visit").prop("checked",n),$("#swh-filter-empty-visits").prop("checked",r),$("#swh-search-origin-metadata").prop("checked",o),i&&$("#swh-search-visit-type").val(i),function(){k.apply(this,arguments)}())}))}},60284:function(t,e,n){"use strict";function r(t,e){function n(){$(".swh-releases-switch").removeClass("active"),$(".swh-branches-switch").addClass("active"),$("#swh-tab-releases").removeClass("active"),$("#swh-tab-branches").addClass("active")}function r(){$(".swh-branches-switch").removeClass("active"),$(".swh-releases-switch").addClass("active"),$("#swh-tab-branches").removeClass("active"),$("#swh-tab-releases").addClass("active")}$(document).ready((function(){$(".dropdown-menu a.swh-branches-switch").click((function(t){n(),t.stopPropagation()})),$(".dropdown-menu a.swh-releases-switch").click((function(t){r(),t.stopPropagation()}));var o=!1;$("#swh-branches-releases-dd").on("show.bs.dropdown",(function(){if(!o){var t=$(".swh-branches-releases").width();$(".swh-branches-releases").width(t+25),o=!0}})),t&&(e?n():r())}))}n.d(e,{a:function(){return r}})},8694:function(t,e,n){"use strict";n.d(e,{Z:function(){return a},_:function(){return s}});var r=n(42152),o=n.n(r),i=(n(89982),n(80893));function a(t){t.preventDefault(),$(t.target).tab("show")}function s(t){t.stopPropagation();var e=$(t.target).closest(".swhid-ui").find(".swhid"),n=$(t.target).data("swhid-with-context"),r=$(t.target).data("swhid-with-context-url"),o=e.text();if($(t.target).prop("checked"))e.attr("href",r),o=n.replace(/;/g,";\n");else{var i=o.indexOf(";");-1!==i&&(o=o.slice(0,i)),e.attr("href","/"+o)}e.text(o),c()}function c(){for(var t=$("#swhid-tab-content").find(".swhid"),e=t.text().replace(/;\n/g,";"),n=[],r=";lines=",o=new RegExp(/L(\d+)/g),i=o.exec(window.location.hash);i;)n.push(parseInt(i[1])),i=o.exec(window.location.hash);n.length>0&&(r+=n[0]),n.length>1&&(r+="-"+n[1]),$("#swhid-context-option-content").prop("checked")&&(e=e.replace(/;lines=\d+-*\d*/g,""),n.length>0&&(e+=r),t.text(e.replace(/;/g,";\n")),t.attr("href","/"+e))}$(document).ready((function(){new(o())(".btn-swhid-copy",{text:function(t){return $(t).closest(".swhid-ui").find(".swhid").text().replace(/;\n/g,";")}}),new(o())(".btn-swhid-url-copy",{text:function(t){var e=$(t).closest(".swhid-ui").find(".swhid").attr("href");return window.location.origin+e}}),.7*window.innerWidth>1e3&&$("#swh-identifiers").css("width","1000px");var t={tabLocation:"right",clickScreenToCloseFilters:[".ui-slideouttab-panel",".modal"],offset:function(){return $(window).width()<i.Fg?"250px":"200px"}};(window.innerHeight<600||window.innerWidth<500)&&(t.otherOffset="20px"),$("#swh-identifiers").tabSlideOut(t),$("#swh-identifiers").css("display","block"),$(".swhid-context-option").trigger("click"),$(window).on("hashchange",(function(){c()})),$("body").click((function(){c()}))}))},89982:function(){!function(t){t.fn.tabSlideOut=function(e){function n(t){return parseInt(t.outerHeight()+1,10)+"px"}function r(){var e=t(window).height();return"top"!==s&&"bottom"!==s||(e=t(window).width()),e-parseInt(a.otherOffset)-parseInt(a.offset)}var o=this;function i(){return o.hasClass("ui-slideouttab-open")}if("string"==typeof e)switch(e){case"open":return this.trigger("open"),this;case"close":return this.trigger("close"),this;case"isOpen":return i();case"toggle":return this.trigger("toggle"),this;case"bounce":return this.trigger("bounce"),this;default:throw new Error("Invalid tabSlideOut command")}else{var a=t.extend({tabLocation:"left",tabHandle:".handle",action:"click",hoverTimeout:5e3,offset:"200px",offsetReverse:!1,otherOffset:null,handleOffset:null,handleOffsetReverse:!1,bounceDistance:"50px",bounceTimes:4,bounceSpeed:300,tabImage:null,tabImageHeight:null,tabImageWidth:null,onLoadSlideOut:!1,clickScreenToClose:!0,clickScreenToCloseFilters:[".ui-slideouttab-panel"],onOpen:function(){},onClose:function(){}},e||{}),s=a.tabLocation,c=a.tabHandle=t(a.tabHandle,o);if(o.addClass("ui-slideouttab-panel").addClass("ui-slideouttab-"+s),a.offsetReverse&&o.addClass("ui-slideouttab-panel-reverse"),c.addClass("ui-slideouttab-handle"),a.handleOffsetReverse&&c.addClass("ui-slideouttab-handle-reverse"),a.toggleButton=t(a.toggleButton),null!==a.tabImage){var u=0,l=0;if(null!==a.tabImageHeight&&null!==a.tabImageWidth)u=a.tabImageHeight,l=a.tabImageWidth;else{var h=new Image;h.src=a.tabImage,u=h.naturalHeight,l=h.naturalWidth}c.addClass("ui-slideouttab-handle-image"),c.css({background:"url("+a.tabImage+") no-repeat",width:l,height:u})}"top"===s||"bottom"===s?(a.panelOffsetFrom=a.offsetReverse?"right":"left",a.handleOffsetFrom=a.handleOffsetReverse?"right":"left"):(a.panelOffsetFrom=a.offsetReverse?"bottom":"top",a.handleOffsetFrom=a.handleOffsetReverse?"bottom":"top"),null===a.handleOffset&&(a.handleOffset="-"+function(t,e){return parseInt(t.css("border-"+e+"-width"),10)}(o,a.handleOffsetFrom)+"px"),"top"===s||"bottom"===s?(o.css(a.panelOffsetFrom,a.offset),c.css(a.handleOffsetFrom,a.handleOffset),null!==a.otherOffset&&(o.css("width",r()+"px"),t(window).resize((function(){o.css("width",r()+"px")}))),"top"===s?c.css({bottom:"-"+n(c)}):c.css({top:"-"+n(c)})):(o.css(a.panelOffsetFrom,a.offset),c.css(a.handleOffsetFrom,a.handleOffset),null!==a.otherOffset&&(o.css("height",r()+"px"),t(window).resize((function(){o.css("height",r()+"px")}))),"left"===s?c.css({right:"0"}):c.css({left:"0"})),c.click((function(t){t.preventDefault()})),a.toggleButton.click((function(t){t.preventDefault()})),o.addClass("ui-slideouttab-ready");var f=function(){o.removeClass("ui-slideouttab-open").trigger("slideouttabclose"),a.onClose()},d=function(){o.addClass("ui-slideouttab-open").trigger("slideouttabopen"),a.onOpen()},p=function(){i()?f():d()},v=[];v[s]="-="+a.bounceDistance;var g=[];g[s]="+="+a.bounceDistance;if(a.clickScreenToClose&&t(document).click((function(e){if(i()&&!o[0].contains(e.target)){for(var n=t(e.target),r=0;r<a.clickScreenToCloseFilters.length;r++){var s=a.clickScreenToCloseFilters[r];if("string"==typeof s){if(n.is(s)||n.parents().is(s))return}else if("function"==typeof s&&s.call(o,e))return}f()}})),"click"===a.action)c.click((function(t){p()}));else if("hover"===a.action){var w=null;o.hover((function(){i()||d(),w=null}),(function(){i()&&null===w&&(w=setTimeout((function(){w&&f(),w=null}),a.hoverTimeout))})),c.click((function(t){i()&&f()}))}a.onLoadSlideOut&&(d(),setTimeout(d,500)),o.on("open",(function(t){i()||d()})),o.on("close",(function(t){i()&&f()})),o.on("toggle",(function(t){p()})),o.on("bounce",(function(t){i()?function(){for(var t=o,e=0;e<a.bounceTimes;e++)t=t.animate(v,a.bounceSpeed).animate(g,a.bounceSpeed);o.trigger("slideouttabbounce")}():function(){for(var t=o,e=0;e<a.bounceTimes;e++)t=t.animate(g,a.bounceSpeed).animate(v,a.bounceSpeed);o.trigger("slideouttabbounce")}()}))}return this}}(jQuery)},80893:function(t,e,n){"use strict";n.d(e,{Fg:function(){return o}});var r=n(55423),o=768;(0,r.TT)("img/swh-spinner.gif")},55423:function(t,e,n){"use strict";n.d(e,{ry:function(){return s},TT:function(){return c},Sv:function(){return l}});var r=n(48926),o=n.n(r),i=n(87757),a=n.n(i);function s(t){if(!t.ok)throw t;return t}function c(t){return"/static/"+t}function u(t){try{new URL(t)}catch(t){return!1}return!0}function l(t){return h.apply(this,arguments)}function h(){return(h=o()(a().mark((function t(e){var n;return a().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:if(u(e)){t.next=4;break}return t.abrupt("return",!1);case 4:return t.next=6,fetch(Urls.api_1_origin(e));case 6:return n=t.sent,t.abrupt("return",n.ok&&200===n.status);case 8:case"end":return t.stop()}}),t)})))).apply(this,arguments)}},42152:function(t){var e;e=function(){return function(){var t={134:function(t,e,n){"use strict";n.d(e,{default:function(){return y}});var r=n(279),o=n.n(r),i=n(370),a=n.n(i),s=n(817),c=n.n(s);function u(t){return(u="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t})(t)}function l(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,r.key,r)}}var h=function(){function t(e){!function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,t),this.resolveOptions(e),this.initSelection()}var e,n,r;return e=t,(n=[{key:"resolveOptions",value:function(){var t=arguments.length>0&&void 0!==arguments[0]?arguments[0]:{};this.action=t.action,this.container=t.container,this.emitter=t.emitter,this.target=t.target,this.text=t.text,this.trigger=t.trigger,this.selectedText=""}},{key:"initSelection",value:function(){this.text?this.selectFake():this.target&&this.selectTarget()}},{key:"createFakeElement",value:function(){var t="rtl"===document.documentElement.getAttribute("dir");this.fakeElem=document.createElement("textarea"),this.fakeElem.style.fontSize="12pt",this.fakeElem.style.border="0",this.fakeElem.style.padding="0",this.fakeElem.style.margin="0",this.fakeElem.style.position="absolute",this.fakeElem.style[t?"right":"left"]="-9999px";var e=window.pageYOffset||document.documentElement.scrollTop;return this.fakeElem.style.top="".concat(e,"px"),this.fakeElem.setAttribute("readonly",""),this.fakeElem.value=this.text,this.fakeElem}},{key:"selectFake",value:function(){var t=this,e=this.createFakeElement();this.fakeHandlerCallback=function(){return t.removeFake()},this.fakeHandler=this.container.addEventListener("click",this.fakeHandlerCallback)||!0,this.container.appendChild(e),this.selectedText=c()(e),this.copyText(),this.removeFake()}},{key:"removeFake",value:function(){this.fakeHandler&&(this.container.removeEventListener("click",this.fakeHandlerCallback),this.fakeHandler=null,this.fakeHandlerCallback=null),this.fakeElem&&(this.container.removeChild(this.fakeElem),this.fakeElem=null)}},{key:"selectTarget",value:function(){this.selectedText=c()(this.target),this.copyText()}},{key:"copyText",value:function(){var t;try{t=document.execCommand(this.action)}catch(e){t=!1}this.handleResult(t)}},{key:"handleResult",value:function(t){this.emitter.emit(t?"success":"error",{action:this.action,text:this.selectedText,trigger:this.trigger,clearSelection:this.clearSelection.bind(this)})}},{key:"clearSelection",value:function(){this.trigger&&this.trigger.focus(),document.activeElement.blur(),window.getSelection().removeAllRanges()}},{key:"destroy",value:function(){this.removeFake()}},{key:"action",set:function(){var t=arguments.length>0&&void 0!==arguments[0]?arguments[0]:"copy";if(this._action=t,"copy"!==this._action&&"cut"!==this._action)throw new Error('Invalid "action" value, use either "copy" or "cut"')},get:function(){return this._action}},{key:"target",set:function(t){if(void 0!==t){if(!t||"object"!==u(t)||1!==t.nodeType)throw new Error('Invalid "target" value, use a valid Element');if("copy"===this.action&&t.hasAttribute("disabled"))throw new Error('Invalid "target" attribute. Please use "readonly" instead of "disabled" attribute');if("cut"===this.action&&(t.hasAttribute("readonly")||t.hasAttribute("disabled")))throw new Error('Invalid "target" attribute. You can\'t cut text from elements with "readonly" or "disabled" attributes');this._target=t}},get:function(){return this._target}}])&&l(e.prototype,n),r&&l(e,r),t}();function f(t){return(f="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t})(t)}function d(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,r.key,r)}}function p(t,e){return(p=Object.setPrototypeOf||function(t,e){return t.__proto__=e,t})(t,e)}function v(t){var e=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Date.prototype.toString.call(Reflect.construct(Date,[],(function(){}))),!0}catch(t){return!1}}();return function(){var n,r=w(t);if(e){var o=w(this).constructor;n=Reflect.construct(r,arguments,o)}else n=r.apply(this,arguments);return g(this,n)}}function g(t,e){return!e||"object"!==f(e)&&"function"!=typeof e?function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t):e}function w(t){return(w=Object.setPrototypeOf?Object.getPrototypeOf:function(t){return t.__proto__||Object.getPrototypeOf(t)})(t)}function m(t,e){var n="data-clipboard-".concat(t);if(e.hasAttribute(n))return e.getAttribute(n)}var y=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),e&&p(t,e)}(i,t);var e,n,r,o=v(i);function i(t,e){var n;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,i),(n=o.call(this)).resolveOptions(e),n.listenClick(t),n}return e=i,r=[{key:"isSupported",value:function(){var t=arguments.length>0&&void 0!==arguments[0]?arguments[0]:["copy","cut"],e="string"==typeof t?[t]:t,n=!!document.queryCommandSupported;return e.forEach((function(t){n=n&&!!document.queryCommandSupported(t)})),n}}],(n=[{key:"resolveOptions",value:function(){var t=arguments.length>0&&void 0!==arguments[0]?arguments[0]:{};this.action="function"==typeof t.action?t.action:this.defaultAction,this.target="function"==typeof t.target?t.target:this.defaultTarget,this.text="function"==typeof t.text?t.text:this.defaultText,this.container="object"===f(t.container)?t.container:document.body}},{key:"listenClick",value:function(t){var e=this;this.listener=a()(t,"click",(function(t){return e.onClick(t)}))}},{key:"onClick",value:function(t){var e=t.delegateTarget||t.currentTarget;this.clipboardAction&&(this.clipboardAction=null),this.clipboardAction=new h({action:this.action(e),target:this.target(e),text:this.text(e),container:this.container,trigger:e,emitter:this})}},{key:"defaultAction",value:function(t){return m("action",t)}},{key:"defaultTarget",value:function(t){var e=m("target",t);if(e)return document.querySelector(e)}},{key:"defaultText",value:function(t){return m("text",t)}},{key:"destroy",value:function(){this.listener.destroy(),this.clipboardAction&&(this.clipboardAction.destroy(),this.clipboardAction=null)}}])&&d(e.prototype,n),r&&d(e,r),i}(o())},828:function(t){if("undefined"!=typeof Element&&!Element.prototype.matches){var e=Element.prototype;e.matches=e.matchesSelector||e.mozMatchesSelector||e.msMatchesSelector||e.oMatchesSelector||e.webkitMatchesSelector}t.exports=function(t,e){for(;t&&9!==t.nodeType;){if("function"==typeof t.matches&&t.matches(e))return t;t=t.parentNode}}},438:function(t,e,n){var r=n(828);function o(t,e,n,r,o){var a=i.apply(this,arguments);return t.addEventListener(n,a,o),{destroy:function(){t.removeEventListener(n,a,o)}}}function i(t,e,n,o){return function(n){n.delegateTarget=r(n.target,e),n.delegateTarget&&o.call(t,n)}}t.exports=function(t,e,n,r,i){return"function"==typeof t.addEventListener?o.apply(null,arguments):"function"==typeof n?o.bind(null,document).apply(null,arguments):("string"==typeof t&&(t=document.querySelectorAll(t)),Array.prototype.map.call(t,(function(t){return o(t,e,n,r,i)})))}},879:function(t,e){e.node=function(t){return void 0!==t&&t instanceof HTMLElement&&1===t.nodeType},e.nodeList=function(t){var n=Object.prototype.toString.call(t);return void 0!==t&&("[object NodeList]"===n||"[object HTMLCollection]"===n)&&"length"in t&&(0===t.length||e.node(t[0]))},e.string=function(t){return"string"==typeof t||t instanceof String},e.fn=function(t){return"[object Function]"===Object.prototype.toString.call(t)}},370:function(t,e,n){var r=n(879),o=n(438);t.exports=function(t,e,n){if(!t&&!e&&!n)throw new Error("Missing required arguments");if(!r.string(e))throw new TypeError("Second argument must be a String");if(!r.fn(n))throw new TypeError("Third argument must be a Function");if(r.node(t))return function(t,e,n){return t.addEventListener(e,n),{destroy:function(){t.removeEventListener(e,n)}}}(t,e,n);if(r.nodeList(t))return function(t,e,n){return Array.prototype.forEach.call(t,(function(t){t.addEventListener(e,n)})),{destroy:function(){Array.prototype.forEach.call(t,(function(t){t.removeEventListener(e,n)}))}}}(t,e,n);if(r.string(t))return function(t,e,n){return o(document.body,t,e,n)}(t,e,n);throw new TypeError("First argument must be a String, HTMLElement, HTMLCollection, or NodeList")}},817:function(t){t.exports=function(t){var e;if("SELECT"===t.nodeName)t.focus(),e=t.value;else if("INPUT"===t.nodeName||"TEXTAREA"===t.nodeName){var n=t.hasAttribute("readonly");n||t.setAttribute("readonly",""),t.select(),t.setSelectionRange(0,t.value.length),n||t.removeAttribute("readonly"),e=t.value}else{t.hasAttribute("contenteditable")&&t.focus();var r=window.getSelection(),o=document.createRange();o.selectNodeContents(t),r.removeAllRanges(),r.addRange(o),e=r.toString()}return e}},279:function(t){function e(){}e.prototype={on:function(t,e,n){var r=this.e||(this.e={});return(r[t]||(r[t]=[])).push({fn:e,ctx:n}),this},once:function(t,e,n){var r=this;function o(){r.off(t,o),e.apply(n,arguments)}return o._=e,this.on(t,o,n)},emit:function(t){for(var e=[].slice.call(arguments,1),n=((this.e||(this.e={}))[t]||[]).slice(),r=0,o=n.length;r<o;r++)n[r].fn.apply(n[r].ctx,e);return this},off:function(t,e){var n=this.e||(this.e={}),r=n[t],o=[];if(r&&e)for(var i=0,a=r.length;i<a;i++)r[i].fn!==e&&r[i].fn._!==e&&o.push(r[i]);return o.length?n[t]=o:delete n[t],this}},t.exports=e,t.exports.TinyEmitter=e}},e={};function n(r){if(e[r])return e[r].exports;var o=e[r]={exports:{}};return t[r](o,o.exports,n),o.exports}return n.n=function(t){var e=t&&t.__esModule?function(){return t.default}:function(){return t};return n.d(e,{a:e}),e},n.d=function(t,e){for(var r in e)n.o(e,r)&&!n.o(t,r)&&Object.defineProperty(t,r,{enumerable:!0,get:e[r]})},n.o=function(t,e){return Object.prototype.hasOwnProperty.call(t,e)},n(134)}().default},t.exports=e()}},e={};function n(r){var o=e[r];if(void 0!==o)return o.exports;var i=e[r]={exports:{}};return t[r].call(i.exports,i,i.exports,n),i.exports}n.n=function(t){var e=t&&t.__esModule?function(){return t.default}:function(){return t};return n.d(e,{a:e}),e},n.d=function(t,e){for(var r in e)n.o(e,r)&&!n.o(t,r)&&Object.defineProperty(t,r,{enumerable:!0,get:e[r]})},n.o=function(t,e){return Object.prototype.hasOwnProperty.call(t,e)},n.r=function(t){"undefined"!=typeof Symbol&&Symbol.toStringTag&&Object.defineProperty(t,Symbol.toStringTag,{value:"Module"}),Object.defineProperty(t,"__esModule",{value:!0})};var r={};return function(){"use strict";n.r(r),n.d(r,{initSnapshotNavigation:function(){return t.a},initOriginSearch:function(){return e.A},initBrowseNavbar:function(){return o.E},swhIdContextOptionToggled:function(){return i._},swhIdObjectTypeToggled:function(){return i.Z}});var t=n(60284),e=n(14444),o=n(12312),i=n(8694)}(),r}()}));
//# sourceMappingURL=browse.a4fd9215bdad775b95a9.js.map