!function(t,e){"object"==typeof exports&&"object"==typeof module?module.exports=e():"function"==typeof define&&define.amd?define([],e):"object"==typeof exports?exports.browse=e():(t.swh=t.swh||{},t.swh.browse=e())}(window,function(){return function(t){var e={};function s(n){if(e[n])return e[n].exports;var o=e[n]={i:n,l:!1,exports:{}};return t[n].call(o.exports,o,o.exports,s),o.l=!0,o.exports}return s.m=t,s.c=e,s.d=function(t,e,n){s.o(t,e)||Object.defineProperty(t,e,{configurable:!1,enumerable:!0,get:n})},s.r=function(t){Object.defineProperty(t,"__esModule",{value:!0})},s.n=function(t){var e=t&&t.__esModule?function(){return t.default}:function(){return t};return s.d(e,"a",e),e},s.o=function(t,e){return Object.prototype.hasOwnProperty.call(t,e)},s.p="/static/",s(s.s=469)}({207:function(t,e,s){"use strict";s.r(e);s(468),s(466),s(464),s(462);function n(t,e){function s(){$(".swh-releases-switch").removeClass("active"),$(".swh-branches-switch").addClass("active"),$("#swh-tab-releases").removeClass("active"),$("#swh-tab-branches").addClass("active")}function n(){$(".swh-branches-switch").removeClass("active"),$(".swh-releases-switch").addClass("active"),$("#swh-tab-branches").removeClass("active"),$("#swh-tab-releases").addClass("active")}$(document).ready(function(){$(".dropdown-menu a.swh-branches-switch").click(function(t){s(),t.stopPropagation()}),$(".dropdown-menu a.swh-releases-switch").click(function(t){n(),t.stopPropagation()});var o=!1;$("#swh-branches-releases-dd").on("show.bs.dropdown",function(){if(!o){var t=$(".swh-branches-releases").width();$(".swh-branches-releases").width(t+25),o=!0}}),t&&(e?s():n())})}function o(t,e,s){var n=t[e];t[e]=t[s],t[s]=n}var r=s(35),i=void 0,a=15,c=10*a,u=0,d=null,l=!1;function h(){setTimeout(function(){$("#origin-search-results tbody tr").removeAttr("style")})}function f(){$("#origin-search-results tbody tr").remove()}function p(t,e){var s=e%c;if(t.length>0){$("#swh-origin-search-results").show(),$("#swh-no-origins-found").hide(),f();for(var n=$("#origin-search-results tbody"),o=function(e){var s=t[e],o="<tr>";o+='<td style="width: 120px;">'+s.type+"</td>";var r=Urls.browse_origin(s.type,s.url);o+='<td style="white-space: nowrap;"><a href="'+r+'">'+r+"</a></td>",o+='<td id="visit-status-origin-'+s.id+'"><i title="Checking visit status" class="fa fa-refresh fa-spin"></i></td>',o+="</tr>",n.append(o);var i=Urls.browse_origin_latest_snapshot(s.id);fetch(i,{credentials:"same-origin"}).then(function(t){return t.json()}).then(function(t){var e=s.id;$("#visit-status-origin-"+e).children().remove(),t?$("#visit-status-origin-"+e).append('<i title="Origin has at least one full visit by Software Heritage" class="fa fa-check"></i>'):$("#visit-status-origin-"+e).append('<i title="Origin has not yet been visited by Software Heritage or does not have at least one full visit" class="fa fa-times"></i>')})},r=s;r<s+a&&r<t.length;++r)o(r);h()}else $("#swh-origin-search-results").hide(),$("#swh-no-origins-found").show();t.length-s<a||t.length<c&&s+a===t.length?$("#origins-next-results-button").addClass("disabled"):$("#origins-next-results-button").removeClass("disabled"),e>0?$("#origins-prev-results-button").removeClass("disabled"):$("#origins-prev-results-button").addClass("disabled"),l=!1,setTimeout(function(){window.scrollTo(0,0)})}function w(t,e,s,n){i=t;var a=[];!function t(e,s,n){if(1===(n=n||e.length))s(e);else for(var r=1;r<=n;r+=1)t(e,s,n-1),o(e,(n%2?1:r)-1,n-1)}(t.trim().replace(/\s+/g," ").split(" "),function(t){return a.push(t.join(".*"))});var c=a.join("|"),u=Urls.browse_origin_search(c)+"?limit="+e+"&offset="+s+"&regexp=true";$(".swh-loading").addClass("show"),fetch(u,{credentials:"same-origin"}).then(r.a).then(function(t){return t.json()}).then(function(e){d=e,"undefined"!=typeof Storage&&(sessionStorage.setItem("last-swh-origin-url-patterns",t),sessionStorage.setItem("last-swh-origin-search-results",JSON.stringify(e)),sessionStorage.setItem("last-swh-origin-search-offset",n)),$(".swh-loading").removeClass("show"),p(e,n)}).catch(function(){$(".swh-loading").removeClass("show"),l=!1})}function g(){$(document).ready(function(){if("undefined"!=typeof Storage){i=sessionStorage.getItem("last-swh-origin-url-patterns");var t=sessionStorage.getItem("last-swh-origin-search-results");u=sessionStorage.getItem("last-swh-origin-search-offset"),t&&($("#origins-url-patterns").val(i),u=parseInt(u),p(JSON.parse(t),u))}$("#search_origins").submit(function(t){var e=$("#origins-url-patterns").val();u=0,l=!0,f(),w(e,c,u,u),t.preventDefault()}),$("#origins-next-results-button").click(function(t){$("#origins-next-results-button").hasClass("disabled")||l||(l=!0,u+=a,d&&u%c!=0?p(d,u):w(i,c,u,u),t.preventDefault())}),$("#origins-prev-results-button").click(function(t){$("#origins-prev-results-button").hasClass("disabled")||l||(l=!0,u-=a,!d||u>0&&(u+a)%c==0?w(i,c,u+a-c,u):p(d,u),t.preventDefault())}),$(document).on("shown.bs.tab",'a[data-toggle="tab"]',function(t){"Search"===t.currentTarget.text.trim()&&h()})})}function v(t){$(document).ready(function(){$(".dropdown-submenu a.dropdown-item").on("click",function(t){$(t.target).next("div").toggle(),"none"!==$(t.target).next("div").css("display")?$(t.target).focus():$(t.target).blur(),t.stopPropagation(),t.preventDefault()}),$("#swh-branches-releases-dd").on("shown.bs.dropdown",function(){$("body").append($("#swh-branches-releases-dd").css({position:"absolute",left:$("#swh-branches-releases-dd").offset().left,top:$("#swh-branches-releases-dd").offset().top}).detach());var t=$("#swh-branches-releases-dd").offset().left+$("#swh-branches-releases-dd").width(),e=$(".swh-browse-bread-crumbs").offset().top;$(".swh-browse-bread-crumbs").css("position","absolute"),$(".swh-browse-bread-crumbs").offset({left:t,top:e})}),$(".swh-metadata-toggler").popover({boundary:"viewport",container:"body",html:!0,template:'<div class="popover" role="tooltip">\n                   <div class="arrow"></div>\n                   <h3 class="popover-header"></h3>\n                   <div class="popover-body swh-metadata"></div>\n                 </div>',content:function(){var t=$(this).attr("data-popover-content");return $(t).children(".popover-body").html()},title:function(){var t=$(this).attr("data-popover-content");return $(t).children(".popover-heading").html()},offset:"50vh"}),$(".swh-vault-menu a.dropdown-item").on("click",function(t){$(".swh-metadata-toggler").popover("hide")}),$(".swh-metadata-toggler").on("show.bs.popover",function(){$(".swh-vault-menu .dropdown-menu").hide()}),$(".swh-actions-dropdown").on("hide.bs.dropdown",function(){$(".swh-vault-menu .dropdown-menu").hide(),$(".swh-metadata-toggler").popover("hide")}),$("body").on("click",function(t){$(t.target).parents(".swh-metadata").length&&t.stopPropagation()}),$(".browse-"+t+"-item").addClass("active"),$(".browse-"+t+"-link").addClass("active"),$(".browse-main-link").click(function(t){var e=sessionStorage.getItem("last-browse-page");e&&(t.preventDefault(),window.location=e)}),window.onunload=function(){"main"===t&&sessionStorage.setItem("last-browse-page",window.location)}})}s.d(e,"initSnapshotNavigation",function(){return n}),s.d(e,"initOriginSearch",function(){return g}),s.d(e,"initBrowse",function(){return v})},35:function(t,e,s){"use strict";function n(t){if(!t.ok)throw Error(t.statusText);return t}function o(t){for(var e=0;e<t.length;++e)if(!t[e].ok)throw Error(t[e].statusText);return t}function r(t){return"/static/"+t}s.d(e,"a",function(){return n}),s.d(e,"b",function(){return o}),s.d(e,"c",function(){return r})},462:function(t,e,s){},464:function(t,e,s){},466:function(t,e,s){},468:function(t,e,s){},469:function(t,e,s){t.exports=s(207)}})});
//# browse.da339e9d2ee2e1647793.js.map