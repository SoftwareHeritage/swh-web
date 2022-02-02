/*! For license information please see browse.947bb7896a305103ef07.js.LICENSE.txt */
!function(t,e){"object"==typeof exports&&"object"==typeof module?module.exports=e():"function"==typeof define&&define.amd?define([],e):"object"==typeof exports?exports.swh=e():(t.swh=t.swh||{},t.swh.browse=e())}(self,(function(){return function(){var t={87757:function(t,e,n){t.exports=n(35666)},70103:function(t,e,n){"use strict";n.d(e,{E:function(){return o}});var r=n(86515);function o(){window.location.pathname===Urls.browse_origin_visits()?$("#swh-browse-origin-visits-nav-link").addClass("active"):window.location.pathname===Urls.browse_origin_branches()||window.location.pathname===Urls.browse_snapshot_branches()||window.location.pathname.endsWith("branches/")?$("#swh-browse-snapshot-branches-nav-link").addClass("active"):window.location.pathname===Urls.browse_origin_releases()||window.location.pathname===Urls.browse_snapshot_releases()||window.location.pathname.endsWith("releases/")?$("#swh-browse-snapshot-releases-nav-link").addClass("active"):$("#swh-browse-code-nav-link").addClass("active")}$(document).ready((function(){$(".dropdown-submenu a.dropdown-item").on("click",(function(t){$(t.target).next("div").toggle(),"none"!==$(t.target).next("div").css("display")?$(t.target).focus():$(t.target).blur(),t.stopPropagation(),t.preventDefault()})),$(".swh-popover-toggler").popover({boundary:"viewport",container:"body",html:!0,placement:function(){return $(window).width()<r.Fg?"top":"right"},template:'<div class="popover" role="tooltip">\n                 <div class="arrow"></div>\n                 <h3 class="popover-header"></h3>\n                 <div class="popover-body swh-popover"></div>\n               </div>',content:function(){var t=$(this).attr("data-popover-content");return $(t).children(".popover-body").remove().html()},title:function(){var t=$(this).attr("data-popover-content");return $(t).children(".popover-heading").html()},offset:"50vh",sanitize:!1}),$(".swh-vault-menu a.dropdown-item").on("click",(function(t){$(".swh-popover-toggler").popover("hide")})),$(".swh-popover-toggler").on("show.bs.popover",(function(t){$(".swh-popover-toggler:not(#"+t.currentTarget.id+")").popover("hide"),$(".swh-vault-menu .dropdown-menu").hide()})),$(".swh-actions-dropdown").on("hide.bs.dropdown",(function(){$(".swh-vault-menu .dropdown-menu").hide(),$(".swh-popover-toggler").popover("hide")})),$("#swh-branch-search-form").submit((function(t){var e=new URLSearchParams(window.location.search);e.set("name_include",$("#swh-branch-search-string").val().trim()),window.location.search=e.toString(),t.preventDefault()})),$("body").on("click",(function(t){$(t.target).parents(".swh-popover").length&&t.stopPropagation()}))}))},84664:function(t,e,n){"use strict";n.d(e,{A:function(){return k}});var r=n(15861),o=n(87757),i=n.n(o),a=n(59537);function s(t,e){var n="undefined"!=typeof Symbol&&t[Symbol.iterator]||t["@@iterator"];if(n)return(n=n.call(t)).next.bind(n);if(Array.isArray(t)||(n=function(t,e){if(!t)return;if("string"==typeof t)return c(t,e);var n=Object.prototype.toString.call(t).slice(8,-1);"Object"===n&&t.constructor&&(n=t.constructor.name);if("Map"===n||"Set"===n)return Array.from(t);if("Arguments"===n||/^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n))return c(t,e)}(t))||e&&t&&"number"==typeof t.length){n&&(t=n);var r=0;return function(){return r>=t.length?{done:!0}:{done:!1,value:t[r++]}}}throw new TypeError("Invalid attempt to iterate non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.")}function c(t,e){(null==e||e>t.length)&&(e=t.length);for(var n=0,r=new Array(e);n<e;n++)r[n]=t[n];return r}var u=[],l=null,f=null,h=!1;function d(t){return t.match(/<(.+)>; rel="next"/)[1]}function p(){setTimeout((function(){$("#origin-search-results tbody tr").removeAttr("style")}))}function v(){$("#origin-search-results tbody tr").remove()}function g(t){return w.apply(this,arguments)}function w(){return(w=(0,r.Z)(i().mark((function t(e){var n,r,o,a,c,f,d,g,w,y,m,b,x,k,S;return i().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:if(!(e.length>0)){t.next=17;break}for($("#swh-origin-search-results").show(),$("#swh-no-result").hide(),v(),n=$("#origin-search-results tbody"),r=[],o=s(e.entries());!(a=o()).done;)c=a.value,f=c[0],d=c[1],g=Urls.browse_origin()+"?origin_url="+encodeURIComponent(d.url),w='<tr id="origin-'+f+'" class="swh-search-result-entry swh-tr-hover-highlight">',w+='<td id="visit-type-origin-'+f+'" class="swh-origin-visit-type" style="width: 120px;"><i title="Checking software origin type" class="mdi mdi-sync mdi-spin mdi-fw"></i>Checking</td>',w+='<td style="white-space: nowrap;"><a href="'+g+'">'+d.url+"</a></td>",w+='<td class="swh-visit-status" id="visit-status-origin-'+f+'"><i title="Checking archiving status" class="mdi mdi-sync mdi-spin mdi-fw"></i>Checking</td>',w+="</tr>",n.append(w),y=Urls.api_1_origin_visit_latest(d.url),y+="?require_snapshot=true",r.push(fetch(y));return t.next=9,Promise.all(r);case 9:return m=t.sent,t.next=12,Promise.all(m.map((function(t){return t.json()})));case 12:for(b=t.sent,x=0;x<m.length;++x)k=m[x],S=b[x],404!==k.status&&S.type?($("#visit-type-origin-"+x).html(S.type),$("#visit-status-origin-"+x).html('<i title="Software origin has been archived by Software Heritage" class="mdi mdi-check-bold mdi-fw"></i>Archived')):($("#visit-type-origin-"+x).html("unknown"),$("#visit-status-origin-"+x).html('<i title="Software origin archival by Software Heritage is pending" class="mdi mdi-close-thick mdi-fw"></i>Pending archival'),$("#swh-filter-empty-visits").prop("checked")&&$("#origin-"+x).remove());p(),t.next=20;break;case 17:$("#swh-origin-search-results").hide(),$("#swh-no-result").text("No origins matching the search criteria were found."),$("#swh-no-result").show();case 20:null===l?$("#origins-next-results-button").addClass("disabled"):$("#origins-next-results-button").removeClass("disabled"),0===u.length?$("#origins-prev-results-button").addClass("disabled"):$("#origins-prev-results-button").removeClass("disabled"),h=!1,setTimeout((function(){window.scrollTo(0,0)}));case 24:case"end":return t.stop()}}),t)})))).apply(this,arguments)}function y(t,e){var n;if($("#swh-search-origin-metadata").prop("checked"))(n=new URL(Urls.api_1_origin_metadata_search(),window.location)).searchParams.append("fulltext",t);else{var r=$("#swh-search-use-ql").prop("checked");(n=new URL(Urls.api_1_origin_search(t),window.location)).searchParams.append("use_ql",null!=r&&r)}var o=$("#swh-search-origins-with-visit").prop("checked");n.searchParams.append("limit",e),n.searchParams.append("with_visit",o);var i=$("#swh-search-visit-type").val();"any"!==i&&n.searchParams.append("visit_type",i),m(n.toString())}function m(t){return b.apply(this,arguments)}function b(){return(b=(0,r.Z)(i().mark((function t(e){var n,r,o;return i().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:return v(),$(".swh-loading").addClass("show"),t.prev=2,t.next=5,fetch(e);case 5:return n=t.sent,(0,a.ry)(n),t.next=9,n.json();case 9:r=t.sent,f=e,l=null,n.headers.has("Link")&&void 0!==(o=d(n.headers.get("Link")))&&(l=o),$(".swh-loading").removeClass("show"),g(r),t.next=24;break;case 17:t.prev=17,t.t0=t.catch(2),$(".swh-loading").removeClass("show"),h=!1,$("#swh-origin-search-results").hide(),$("#swh-no-result").text("Error "+t.t0.status+": "+t.t0.statusText),$("#swh-no-result").show();case 24:case"end":return t.stop()}}),t,null,[[2,17]])})))).apply(this,arguments)}function x(){return(x=(0,r.Z)(i().mark((function t(){var e,n,r,o,s;return i().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:if($("#swh-no-result").hide(),e=$("#swh-origins-url-patterns").val(),h=!0,!e.startsWith("swh:")){t.next=27;break}return t.prev=4,n=Urls.api_1_resolve_swhid(e),t.next=8,fetch(n);case 8:return r=t.sent,(0,a.ry)(r),t.next=12,r.json();case 12:o=t.sent,window.location=o.browse_url,t.next=25;break;case 16:return t.prev=16,t.t0=t.catch(4),t.next=20,t.t0.json();case 20:s=t.sent,$("#swh-origin-search-results").hide(),$(".swh-search-pagination").hide(),$("#swh-no-result").text(s.reason),$("#swh-no-result").show();case 25:t.next=36;break;case 27:return t.next=29,(0,a.Sv)(e);case 29:if(!t.sent){t.next=33;break}window.location.href=Urls.browse_origin()+"?origin_url="+encodeURIComponent(e),t.next=36;break;case 33:$("#swh-origin-search-results").show(),$(".swh-search-pagination").show(),y(e,100);case 36:case"end":return t.stop()}}),t,null,[[4,16]])})))).apply(this,arguments)}function k(){$(document).ready((function(){$("#swh-search-origins").submit((function(t){if(t.preventDefault(),t.target.checkValidity()){$(t.target).removeClass("was-validated");var e=$("#swh-origins-url-patterns").val().trim(),n=$("#swh-search-origins-with-visit").prop("checked"),r=$("#swh-filter-empty-visits").prop("checked"),o=$("#swh-search-use-ql").prop("checked"),i=$("#swh-search-origin-metadata").prop("checked"),a=$("#swh-search-visit-type").val(),s=new URLSearchParams;s.append("q",e),n&&s.append("with_visit",n),r&&s.append("with_content",r),o&&s.append("use_ql",null!=o&&o),i&&s.append("search_metadata",i),"any"!==a&&s.append("visit_type",a),window.location=Urls.browse_search()+"?"+s.toString()}else $(t.target).addClass("was-validated")})),$("#origins-next-results-button").click((function(t){$("#origins-next-results-button").hasClass("disabled")||h||(h=!0,u.push(f),m(l),t.preventDefault())})),$("#origins-prev-results-button").click((function(t){$("#origins-prev-results-button").hasClass("disabled")||h||(h=!0,m(u.pop()),t.preventDefault())}));var t=new URLSearchParams(window.location.search),e=t.get("q"),n=t.has("with_visit"),r=t.has("use_ql"),o=t.has("with_content"),i=t.has("search_metadata"),a=t.get("visit_type");e&&($("#swh-origins-url-patterns").val(e),$("#swh-search-origins-with-visit").prop("checked",n),$("#swh-search-use-ql").prop("checked",null!=r&&r),$("#swh-filter-empty-visits").prop("checked",o),$("#swh-search-origin-metadata").prop("checked",i),a&&$("#swh-search-visit-type").val(a),function(){x.apply(this,arguments)}())}))}},71523:function(t,e,n){"use strict";function r(t,e){function n(){$(".swh-releases-switch").removeClass("active"),$(".swh-branches-switch").addClass("active"),$("#swh-tab-releases").removeClass("active"),$("#swh-tab-branches").addClass("active")}function r(){$(".swh-branches-switch").removeClass("active"),$(".swh-releases-switch").addClass("active"),$("#swh-tab-branches").removeClass("active"),$("#swh-tab-releases").addClass("active")}$(document).ready((function(){$(".dropdown-menu a.swh-branches-switch").click((function(t){n(),t.stopPropagation()})),$(".dropdown-menu a.swh-releases-switch").click((function(t){r(),t.stopPropagation()}));var o=!1;$("#swh-branches-releases-dd").on("show.bs.dropdown",(function(){if(!o){var t=$(".swh-branches-releases").width();$(".swh-branches-releases").width(t+25),o=!0}})),t&&(e?n():r())}))}n.d(e,{a:function(){return r}})},32218:function(t,e,n){"use strict";n.d(e,{Z:function(){return a},_:function(){return s}});var r=n(42152),o=n.n(r),i=(n(14547),n(86515));function a(t){t.preventDefault(),$(t.target).tab("show")}function s(t){t.stopPropagation();var e=$(t.target).closest(".swhid-ui").find(".swhid"),n=$(t.target).data("swhid-with-context"),r=$(t.target).data("swhid-with-context-url"),o=e.text();if($(t.target).prop("checked"))e.attr("href",r),o=n.replace(/;/g,";\n");else{var i=o.indexOf(";");-1!==i&&(o=o.slice(0,i)),e.attr("href","/"+o)}e.text(o),c()}function c(){for(var t=$("#swhid-tab-content").find(".swhid"),e=t.text().replace(/;\n/g,";"),n=[],r=";lines=",o=new RegExp(/L(\d+)/g),i=o.exec(window.location.hash);i;)n.push(parseInt(i[1])),i=o.exec(window.location.hash);n.length>0&&(r+=n[0]),n.length>1&&(r+="-"+n[1]),$("#swhid-context-option-content").prop("checked")&&(e=e.replace(/;lines=\d+-*\d*/g,""),n.length>0&&(e+=r),t.text(e.replace(/;/g,";\n")),t.attr("href","/"+e))}$(document).ready((function(){new(o())(".btn-swhid-copy",{text:function(t){return $(t).closest(".swhid-ui").find(".swhid").text().replace(/;\n/g,";")}}),new(o())(".btn-swhid-url-copy",{text:function(t){var e=$(t).closest(".swhid-ui").find(".swhid").attr("href");return window.location.origin+e}}),.7*window.innerWidth>1e3&&$("#swh-identifiers").css("width","1000px");var t={tabLocation:"right",clickScreenToCloseFilters:[function(){return $(".introjs-overlay").length>0},".ui-slideouttab-panel",".modal"],offset:function(){return $(window).width()<i.Fg?"250px":"200px"}};(window.innerHeight<600||window.innerWidth<500)&&(t.otherOffset="20px"),$("#swh-identifiers").tabSlideOut(t),$("#swh-identifiers").addClass("d-none d-sm-block"),$(".swhid-context-option").trigger("click"),$(window).on("hashchange",(function(){c()})),$("body").click((function(){c()}))}))},14547:function(){!function(t){t.fn.tabSlideOut=function(e){function n(t){return parseInt(t.outerHeight()+1,10)+"px"}function r(){var e=t(window).height();return"top"!==s&&"bottom"!==s||(e=t(window).width()),e-parseInt(a.otherOffset)-parseInt(a.offset)}var o=this;function i(){return o.hasClass("ui-slideouttab-open")}if("string"==typeof e)switch(e){case"open":return this.trigger("open"),this;case"close":return this.trigger("close"),this;case"isOpen":return i();case"toggle":return this.trigger("toggle"),this;case"bounce":return this.trigger("bounce"),this;default:throw new Error("Invalid tabSlideOut command")}else{var a=t.extend({tabLocation:"left",tabHandle:".handle",action:"click",hoverTimeout:5e3,offset:"200px",offsetReverse:!1,otherOffset:null,handleOffset:null,handleOffsetReverse:!1,bounceDistance:"50px",bounceTimes:4,bounceSpeed:300,tabImage:null,tabImageHeight:null,tabImageWidth:null,onLoadSlideOut:!1,clickScreenToClose:!0,clickScreenToCloseFilters:[".ui-slideouttab-panel"],onOpen:function(){},onClose:function(){}},e||{}),s=a.tabLocation,c=a.tabHandle=t(a.tabHandle,o);if(o.addClass("ui-slideouttab-panel").addClass("ui-slideouttab-"+s),a.offsetReverse&&o.addClass("ui-slideouttab-panel-reverse"),c.addClass("ui-slideouttab-handle"),a.handleOffsetReverse&&c.addClass("ui-slideouttab-handle-reverse"),a.toggleButton=t(a.toggleButton),null!==a.tabImage){var u=0,l=0;if(null!==a.tabImageHeight&&null!==a.tabImageWidth)u=a.tabImageHeight,l=a.tabImageWidth;else{var f=new Image;f.src=a.tabImage,u=f.naturalHeight,l=f.naturalWidth}c.addClass("ui-slideouttab-handle-image"),c.css({background:"url("+a.tabImage+") no-repeat",width:l,height:u})}"top"===s||"bottom"===s?(a.panelOffsetFrom=a.offsetReverse?"right":"left",a.handleOffsetFrom=a.handleOffsetReverse?"right":"left"):(a.panelOffsetFrom=a.offsetReverse?"bottom":"top",a.handleOffsetFrom=a.handleOffsetReverse?"bottom":"top"),null===a.handleOffset&&(a.handleOffset="-"+function(t,e){return parseInt(t.css("border-"+e+"-width"),10)}(o,a.handleOffsetFrom)+"px"),"top"===s||"bottom"===s?(o.css(a.panelOffsetFrom,a.offset),c.css(a.handleOffsetFrom,a.handleOffset),null!==a.otherOffset&&(o.css("width",r()+"px"),t(window).resize((function(){o.css("width",r()+"px")}))),"top"===s?c.css({bottom:"-"+n(c)}):c.css({top:"-"+n(c)})):(o.css(a.panelOffsetFrom,a.offset),c.css(a.handleOffsetFrom,a.handleOffset),null!==a.otherOffset&&(o.css("height",r()+"px"),t(window).resize((function(){o.css("height",r()+"px")}))),"left"===s?c.css({right:"0"}):c.css({left:"0"})),c.click((function(t){t.preventDefault()})),a.toggleButton.click((function(t){t.preventDefault()})),o.addClass("ui-slideouttab-ready");var h=function(){o.removeClass("ui-slideouttab-open").trigger("slideouttabclose"),a.onClose()},d=function(){o.addClass("ui-slideouttab-open").trigger("slideouttabopen"),a.onOpen()},p=function(){i()?h():d()},v=[];v[s]="-="+a.bounceDistance;var g=[];g[s]="+="+a.bounceDistance;if(a.clickScreenToClose&&t(document).click((function(e){if(i()&&!o[0].contains(e.target)){for(var n=t(e.target),r=0;r<a.clickScreenToCloseFilters.length;r++){var s=a.clickScreenToCloseFilters[r];if("string"==typeof s){if(n.is(s)||n.parents().is(s))return}else if("function"==typeof s&&s.call(o,e))return}h()}})),"click"===a.action)c.click((function(t){p()}));else if("hover"===a.action){var w=null;o.hover((function(){i()||d(),w=null}),(function(){i()&&null===w&&(w=setTimeout((function(){w&&h(),w=null}),a.hoverTimeout))})),c.click((function(t){i()&&h()}))}a.onLoadSlideOut&&(d(),setTimeout(d,500)),o.on("open",(function(t){i()||d()})),o.on("close",(function(t){i()&&h()})),o.on("toggle",(function(t){p()})),o.on("bounce",(function(t){i()?function(){for(var t=o,e=0;e<a.bounceTimes;e++)t=t.animate(v,a.bounceSpeed).animate(g,a.bounceSpeed);o.trigger("slideouttabbounce")}():function(){for(var t=o,e=0;e<a.bounceTimes;e++)t=t.animate(g,a.bounceSpeed).animate(v,a.bounceSpeed);o.trigger("slideouttabbounce")}()}))}return this}}(jQuery)},86515:function(t,e,n){"use strict";n.d(e,{Fg:function(){return o}});var r=n(59537),o=768;(0,r.TT)("img/swh-spinner.gif")},59537:function(t,e,n){"use strict";n.d(e,{ry:function(){return a},TT:function(){return s},Sv:function(){return u}});var r=n(15861),o=n(87757),i=n.n(o);n(31955);function a(t){if(!t.ok)throw t;return t}function s(t){return"/static/"+t}function c(t){try{new URL(t)}catch(t){return!1}return!0}function u(t){return l.apply(this,arguments)}function l(){return(l=(0,r.Z)(i().mark((function t(e){var n;return i().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:if(c(e)){t.next=4;break}return t.abrupt("return",!1);case 4:return t.next=6,fetch(Urls.api_1_origin(e));case 6:return n=t.sent,t.abrupt("return",n.ok&&200===n.status);case 8:case"end":return t.stop()}}),t)})))).apply(this,arguments)}},42152:function(t){var e;e=function(){return function(){var t={686:function(t,e,n){"use strict";n.d(e,{default:function(){return $}});var r=n(279),o=n.n(r),i=n(370),a=n.n(i),s=n(817),c=n.n(s);function u(t){try{return document.execCommand(t)}catch(t){return!1}}var l=function(t){var e=c()(t);return u("cut"),e};function f(t){var e="rtl"===document.documentElement.getAttribute("dir"),n=document.createElement("textarea");n.style.fontSize="12pt",n.style.border="0",n.style.padding="0",n.style.margin="0",n.style.position="absolute",n.style[e?"right":"left"]="-9999px";var r=window.pageYOffset||document.documentElement.scrollTop;return n.style.top="".concat(r,"px"),n.setAttribute("readonly",""),n.value=t,n}var h=function(t){var e=arguments.length>1&&void 0!==arguments[1]?arguments[1]:{container:document.body},n="";if("string"==typeof t){var r=f(t);e.container.appendChild(r),n=c()(r),u("copy"),r.remove()}else n=c()(t),u("copy");return n};function d(t){return(d="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t})(t)}var p=function(){var t=arguments.length>0&&void 0!==arguments[0]?arguments[0]:{},e=t.action,n=void 0===e?"copy":e,r=t.container,o=t.target,i=t.text;if("copy"!==n&&"cut"!==n)throw new Error('Invalid "action" value, use either "copy" or "cut"');if(void 0!==o){if(!o||"object"!==d(o)||1!==o.nodeType)throw new Error('Invalid "target" value, use a valid Element');if("copy"===n&&o.hasAttribute("disabled"))throw new Error('Invalid "target" attribute. Please use "readonly" instead of "disabled" attribute');if("cut"===n&&(o.hasAttribute("readonly")||o.hasAttribute("disabled")))throw new Error('Invalid "target" attribute. You can\'t cut text from elements with "readonly" or "disabled" attributes')}return i?h(i,{container:r}):o?"cut"===n?l(o):h(o,{container:r}):void 0};function v(t){return(v="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t})(t)}function g(t,e){for(var n=0;n<e.length;n++){var r=e[n];r.enumerable=r.enumerable||!1,r.configurable=!0,"value"in r&&(r.writable=!0),Object.defineProperty(t,r.key,r)}}function w(t,e){return(w=Object.setPrototypeOf||function(t,e){return t.__proto__=e,t})(t,e)}function y(t){var e=function(){if("undefined"==typeof Reflect||!Reflect.construct)return!1;if(Reflect.construct.sham)return!1;if("function"==typeof Proxy)return!0;try{return Date.prototype.toString.call(Reflect.construct(Date,[],(function(){}))),!0}catch(t){return!1}}();return function(){var n,r=b(t);if(e){var o=b(this).constructor;n=Reflect.construct(r,arguments,o)}else n=r.apply(this,arguments);return m(this,n)}}function m(t,e){return!e||"object"!==v(e)&&"function"!=typeof e?function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t):e}function b(t){return(b=Object.setPrototypeOf?Object.getPrototypeOf:function(t){return t.__proto__||Object.getPrototypeOf(t)})(t)}function x(t,e){var n="data-clipboard-".concat(t);if(e.hasAttribute(n))return e.getAttribute(n)}var $=function(t){!function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),e&&w(t,e)}(i,t);var e,n,r,o=y(i);function i(t,e){var n;return function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,i),(n=o.call(this)).resolveOptions(e),n.listenClick(t),n}return e=i,r=[{key:"copy",value:function(t){var e=arguments.length>1&&void 0!==arguments[1]?arguments[1]:{container:document.body};return h(t,e)}},{key:"cut",value:function(t){return l(t)}},{key:"isSupported",value:function(){var t=arguments.length>0&&void 0!==arguments[0]?arguments[0]:["copy","cut"],e="string"==typeof t?[t]:t,n=!!document.queryCommandSupported;return e.forEach((function(t){n=n&&!!document.queryCommandSupported(t)})),n}}],(n=[{key:"resolveOptions",value:function(){var t=arguments.length>0&&void 0!==arguments[0]?arguments[0]:{};this.action="function"==typeof t.action?t.action:this.defaultAction,this.target="function"==typeof t.target?t.target:this.defaultTarget,this.text="function"==typeof t.text?t.text:this.defaultText,this.container="object"===v(t.container)?t.container:document.body}},{key:"listenClick",value:function(t){var e=this;this.listener=a()(t,"click",(function(t){return e.onClick(t)}))}},{key:"onClick",value:function(t){var e=t.delegateTarget||t.currentTarget,n=p({action:this.action(e),container:this.container,target:this.target(e),text:this.text(e)});this.emit(n?"success":"error",{action:this.action,text:n,trigger:e,clearSelection:function(){e&&e.focus(),document.activeElement.blur(),window.getSelection().removeAllRanges()}})}},{key:"defaultAction",value:function(t){return x("action",t)}},{key:"defaultTarget",value:function(t){var e=x("target",t);if(e)return document.querySelector(e)}},{key:"defaultText",value:function(t){return x("text",t)}},{key:"destroy",value:function(){this.listener.destroy()}}])&&g(e.prototype,n),r&&g(e,r),i}(o())},828:function(t){if("undefined"!=typeof Element&&!Element.prototype.matches){var e=Element.prototype;e.matches=e.matchesSelector||e.mozMatchesSelector||e.msMatchesSelector||e.oMatchesSelector||e.webkitMatchesSelector}t.exports=function(t,e){for(;t&&9!==t.nodeType;){if("function"==typeof t.matches&&t.matches(e))return t;t=t.parentNode}}},438:function(t,e,n){var r=n(828);function o(t,e,n,r,o){var a=i.apply(this,arguments);return t.addEventListener(n,a,o),{destroy:function(){t.removeEventListener(n,a,o)}}}function i(t,e,n,o){return function(n){n.delegateTarget=r(n.target,e),n.delegateTarget&&o.call(t,n)}}t.exports=function(t,e,n,r,i){return"function"==typeof t.addEventListener?o.apply(null,arguments):"function"==typeof n?o.bind(null,document).apply(null,arguments):("string"==typeof t&&(t=document.querySelectorAll(t)),Array.prototype.map.call(t,(function(t){return o(t,e,n,r,i)})))}},879:function(t,e){e.node=function(t){return void 0!==t&&t instanceof HTMLElement&&1===t.nodeType},e.nodeList=function(t){var n=Object.prototype.toString.call(t);return void 0!==t&&("[object NodeList]"===n||"[object HTMLCollection]"===n)&&"length"in t&&(0===t.length||e.node(t[0]))},e.string=function(t){return"string"==typeof t||t instanceof String},e.fn=function(t){return"[object Function]"===Object.prototype.toString.call(t)}},370:function(t,e,n){var r=n(879),o=n(438);t.exports=function(t,e,n){if(!t&&!e&&!n)throw new Error("Missing required arguments");if(!r.string(e))throw new TypeError("Second argument must be a String");if(!r.fn(n))throw new TypeError("Third argument must be a Function");if(r.node(t))return function(t,e,n){return t.addEventListener(e,n),{destroy:function(){t.removeEventListener(e,n)}}}(t,e,n);if(r.nodeList(t))return function(t,e,n){return Array.prototype.forEach.call(t,(function(t){t.addEventListener(e,n)})),{destroy:function(){Array.prototype.forEach.call(t,(function(t){t.removeEventListener(e,n)}))}}}(t,e,n);if(r.string(t))return function(t,e,n){return o(document.body,t,e,n)}(t,e,n);throw new TypeError("First argument must be a String, HTMLElement, HTMLCollection, or NodeList")}},817:function(t){t.exports=function(t){var e;if("SELECT"===t.nodeName)t.focus(),e=t.value;else if("INPUT"===t.nodeName||"TEXTAREA"===t.nodeName){var n=t.hasAttribute("readonly");n||t.setAttribute("readonly",""),t.select(),t.setSelectionRange(0,t.value.length),n||t.removeAttribute("readonly"),e=t.value}else{t.hasAttribute("contenteditable")&&t.focus();var r=window.getSelection(),o=document.createRange();o.selectNodeContents(t),r.removeAllRanges(),r.addRange(o),e=r.toString()}return e}},279:function(t){function e(){}e.prototype={on:function(t,e,n){var r=this.e||(this.e={});return(r[t]||(r[t]=[])).push({fn:e,ctx:n}),this},once:function(t,e,n){var r=this;function o(){r.off(t,o),e.apply(n,arguments)}return o._=e,this.on(t,o,n)},emit:function(t){for(var e=[].slice.call(arguments,1),n=((this.e||(this.e={}))[t]||[]).slice(),r=0,o=n.length;r<o;r++)n[r].fn.apply(n[r].ctx,e);return this},off:function(t,e){var n=this.e||(this.e={}),r=n[t],o=[];if(r&&e)for(var i=0,a=r.length;i<a;i++)r[i].fn!==e&&r[i].fn._!==e&&o.push(r[i]);return o.length?n[t]=o:delete n[t],this}},t.exports=e,t.exports.TinyEmitter=e}},e={};function n(r){if(e[r])return e[r].exports;var o=e[r]={exports:{}};return t[r](o,o.exports,n),o.exports}return n.n=function(t){var e=t&&t.__esModule?function(){return t.default}:function(){return t};return n.d(e,{a:e}),e},n.d=function(t,e){for(var r in e)n.o(e,r)&&!n.o(t,r)&&Object.defineProperty(t,r,{enumerable:!0,get:e[r]})},n.o=function(t,e){return Object.prototype.hasOwnProperty.call(t,e)},n(686)}().default},t.exports=e()},35666:function(t){var e=function(t){"use strict";var e,n=Object.prototype,r=n.hasOwnProperty,o="function"==typeof Symbol?Symbol:{},i=o.iterator||"@@iterator",a=o.asyncIterator||"@@asyncIterator",s=o.toStringTag||"@@toStringTag";function c(t,e,n){return Object.defineProperty(t,e,{value:n,enumerable:!0,configurable:!0,writable:!0}),t[e]}try{c({},"")}catch(t){c=function(t,e,n){return t[e]=n}}function u(t,e,n,r){var o=e&&e.prototype instanceof g?e:g,i=Object.create(o.prototype),a=new E(r||[]);return i._invoke=function(t,e,n){var r=f;return function(o,i){if(r===d)throw new Error("Generator is already running");if(r===p){if("throw"===o)throw i;return L()}for(n.method=o,n.arg=i;;){var a=n.delegate;if(a){var s=_(a,n);if(s){if(s===v)continue;return s}}if("next"===n.method)n.sent=n._sent=n.arg;else if("throw"===n.method){if(r===f)throw r=p,n.arg;n.dispatchException(n.arg)}else"return"===n.method&&n.abrupt("return",n.arg);r=d;var c=l(t,e,n);if("normal"===c.type){if(r=n.done?p:h,c.arg===v)continue;return{value:c.arg,done:n.done}}"throw"===c.type&&(r=p,n.method="throw",n.arg=c.arg)}}}(t,n,a),i}function l(t,e,n){try{return{type:"normal",arg:t.call(e,n)}}catch(t){return{type:"throw",arg:t}}}t.wrap=u;var f="suspendedStart",h="suspendedYield",d="executing",p="completed",v={};function g(){}function w(){}function y(){}var m={};m[i]=function(){return this};var b=Object.getPrototypeOf,x=b&&b(b(T([])));x&&x!==n&&r.call(x,i)&&(m=x);var $=y.prototype=g.prototype=Object.create(m);function k(t){["next","throw","return"].forEach((function(e){c(t,e,(function(t){return this._invoke(e,t)}))}))}function S(t,e){function n(o,i,a,s){var c=l(t[o],t,i);if("throw"!==c.type){var u=c.arg,f=u.value;return f&&"object"==typeof f&&r.call(f,"__await")?e.resolve(f.__await).then((function(t){n("next",t,a,s)}),(function(t){n("throw",t,a,s)})):e.resolve(f).then((function(t){u.value=t,a(u)}),(function(t){return n("throw",t,a,s)}))}s(c.arg)}var o;this._invoke=function(t,r){function i(){return new e((function(e,o){n(t,r,e,o)}))}return o=o?o.then(i,i):i()}}function _(t,n){var r=t.iterator[n.method];if(r===e){if(n.delegate=null,"throw"===n.method){if(t.iterator.return&&(n.method="return",n.arg=e,_(t,n),"throw"===n.method))return v;n.method="throw",n.arg=new TypeError("The iterator does not provide a 'throw' method")}return v}var o=l(r,t.iterator,n.arg);if("throw"===o.type)return n.method="throw",n.arg=o.arg,n.delegate=null,v;var i=o.arg;return i?i.done?(n[t.resultName]=i.value,n.next=t.nextLoc,"return"!==n.method&&(n.method="next",n.arg=e),n.delegate=null,v):i:(n.method="throw",n.arg=new TypeError("iterator result is not an object"),n.delegate=null,v)}function O(t){var e={tryLoc:t[0]};1 in t&&(e.catchLoc=t[1]),2 in t&&(e.finallyLoc=t[2],e.afterLoc=t[3]),this.tryEntries.push(e)}function C(t){var e=t.completion||{};e.type="normal",delete e.arg,t.completion=e}function E(t){this.tryEntries=[{tryLoc:"root"}],t.forEach(O,this),this.reset(!0)}function T(t){if(t){var n=t[i];if(n)return n.call(t);if("function"==typeof t.next)return t;if(!isNaN(t.length)){var o=-1,a=function n(){for(;++o<t.length;)if(r.call(t,o))return n.value=t[o],n.done=!1,n;return n.value=e,n.done=!0,n};return a.next=a}}return{next:L}}function L(){return{value:e,done:!0}}return w.prototype=$.constructor=y,y.constructor=w,w.displayName=c(y,s,"GeneratorFunction"),t.isGeneratorFunction=function(t){var e="function"==typeof t&&t.constructor;return!!e&&(e===w||"GeneratorFunction"===(e.displayName||e.name))},t.mark=function(t){return Object.setPrototypeOf?Object.setPrototypeOf(t,y):(t.__proto__=y,c(t,s,"GeneratorFunction")),t.prototype=Object.create($),t},t.awrap=function(t){return{__await:t}},k(S.prototype),S.prototype[a]=function(){return this},t.AsyncIterator=S,t.async=function(e,n,r,o,i){void 0===i&&(i=Promise);var a=new S(u(e,n,r,o),i);return t.isGeneratorFunction(n)?a:a.next().then((function(t){return t.done?t.value:a.next()}))},k($),c($,s,"Generator"),$[i]=function(){return this},$.toString=function(){return"[object Generator]"},t.keys=function(t){var e=[];for(var n in t)e.push(n);return e.reverse(),function n(){for(;e.length;){var r=e.pop();if(r in t)return n.value=r,n.done=!1,n}return n.done=!0,n}},t.values=T,E.prototype={constructor:E,reset:function(t){if(this.prev=0,this.next=0,this.sent=this._sent=e,this.done=!1,this.delegate=null,this.method="next",this.arg=e,this.tryEntries.forEach(C),!t)for(var n in this)"t"===n.charAt(0)&&r.call(this,n)&&!isNaN(+n.slice(1))&&(this[n]=e)},stop:function(){this.done=!0;var t=this.tryEntries[0].completion;if("throw"===t.type)throw t.arg;return this.rval},dispatchException:function(t){if(this.done)throw t;var n=this;function o(r,o){return s.type="throw",s.arg=t,n.next=r,o&&(n.method="next",n.arg=e),!!o}for(var i=this.tryEntries.length-1;i>=0;--i){var a=this.tryEntries[i],s=a.completion;if("root"===a.tryLoc)return o("end");if(a.tryLoc<=this.prev){var c=r.call(a,"catchLoc"),u=r.call(a,"finallyLoc");if(c&&u){if(this.prev<a.catchLoc)return o(a.catchLoc,!0);if(this.prev<a.finallyLoc)return o(a.finallyLoc)}else if(c){if(this.prev<a.catchLoc)return o(a.catchLoc,!0)}else{if(!u)throw new Error("try statement without catch or finally");if(this.prev<a.finallyLoc)return o(a.finallyLoc)}}}},abrupt:function(t,e){for(var n=this.tryEntries.length-1;n>=0;--n){var o=this.tryEntries[n];if(o.tryLoc<=this.prev&&r.call(o,"finallyLoc")&&this.prev<o.finallyLoc){var i=o;break}}i&&("break"===t||"continue"===t)&&i.tryLoc<=e&&e<=i.finallyLoc&&(i=null);var a=i?i.completion:{};return a.type=t,a.arg=e,i?(this.method="next",this.next=i.finallyLoc,v):this.complete(a)},complete:function(t,e){if("throw"===t.type)throw t.arg;return"break"===t.type||"continue"===t.type?this.next=t.arg:"return"===t.type?(this.rval=this.arg=t.arg,this.method="return",this.next="end"):"normal"===t.type&&e&&(this.next=e),v},finish:function(t){for(var e=this.tryEntries.length-1;e>=0;--e){var n=this.tryEntries[e];if(n.finallyLoc===t)return this.complete(n.completion,n.afterLoc),C(n),v}},catch:function(t){for(var e=this.tryEntries.length-1;e>=0;--e){var n=this.tryEntries[e];if(n.tryLoc===t){var r=n.completion;if("throw"===r.type){var o=r.arg;C(n)}return o}}throw new Error("illegal catch attempt")},delegateYield:function(t,n,r){return this.delegate={iterator:T(t),resultName:n,nextLoc:r},"next"===this.method&&(this.arg=e),v}},t}(t.exports);try{regeneratorRuntime=e}catch(t){Function("r","regeneratorRuntime = r")(e)}},15861:function(t,e,n){"use strict";function r(t,e,n,r,o,i,a){try{var s=t[i](a),c=s.value}catch(t){return void n(t)}s.done?e(c):Promise.resolve(c).then(r,o)}function o(t){return function(){var e=this,n=arguments;return new Promise((function(o,i){var a=t.apply(e,n);function s(t){r(a,o,i,s,c,"next",t)}function c(t){r(a,o,i,s,c,"throw",t)}s(void 0)}))}}n.d(e,{Z:function(){return o}})},31955:function(){"use strict";function t(t){for(var e=1;e<arguments.length;e++){var n=arguments[e];for(var r in n)t[r]=n[r]}return t}(function e(n,r){function o(e,o,i){if("undefined"!=typeof document){"number"==typeof(i=t({},r,i)).expires&&(i.expires=new Date(Date.now()+864e5*i.expires)),i.expires&&(i.expires=i.expires.toUTCString()),e=encodeURIComponent(e).replace(/%(2[346B]|5E|60|7C)/g,decodeURIComponent).replace(/[()]/g,escape);var a="";for(var s in i)i[s]&&(a+="; "+s,!0!==i[s]&&(a+="="+i[s].split(";")[0]));return document.cookie=e+"="+n.write(o,e)+a}}return Object.create({set:o,get:function(t){if("undefined"!=typeof document&&(!arguments.length||t)){for(var e=document.cookie?document.cookie.split("; "):[],r={},o=0;o<e.length;o++){var i=e[o].split("="),a=i.slice(1).join("=");try{var s=decodeURIComponent(i[0]);if(r[s]=n.read(a,s),t===s)break}catch(t){}}return t?r[t]:r}},remove:function(e,n){o(e,"",t({},n,{expires:-1}))},withAttributes:function(n){return e(this.converter,t({},this.attributes,n))},withConverter:function(n){return e(t({},this.converter,n),this.attributes)}},{attributes:{value:Object.freeze(r)},converter:{value:Object.freeze(n)}})})({read:function(t){return'"'===t[0]&&(t=t.slice(1,-1)),t.replace(/(%[\dA-F]{2})+/gi,decodeURIComponent)},write:function(t){return encodeURIComponent(t).replace(/%(2[346BF]|3[AC-F]|40|5[BDE]|60|7[BCD])/g,decodeURIComponent)}},{path:"/"})}},e={};function n(r){var o=e[r];if(void 0!==o)return o.exports;var i=e[r]={exports:{}};return t[r].call(i.exports,i,i.exports,n),i.exports}n.n=function(t){var e=t&&t.__esModule?function(){return t.default}:function(){return t};return n.d(e,{a:e}),e},n.d=function(t,e){for(var r in e)n.o(e,r)&&!n.o(t,r)&&Object.defineProperty(t,r,{enumerable:!0,get:e[r]})},n.o=function(t,e){return Object.prototype.hasOwnProperty.call(t,e)},n.r=function(t){"undefined"!=typeof Symbol&&Symbol.toStringTag&&Object.defineProperty(t,Symbol.toStringTag,{value:"Module"}),Object.defineProperty(t,"__esModule",{value:!0})};var r={};return function(){"use strict";n.r(r),n.d(r,{initSnapshotNavigation:function(){return t.a},initOriginSearch:function(){return e.A},initBrowseNavbar:function(){return o.E},swhIdContextOptionToggled:function(){return i._},swhIdObjectTypeToggled:function(){return i.Z}});var t=n(71523),e=n(84664),o=n(70103),i=n(32218)}(),r}()}));
//# sourceMappingURL=browse.947bb7896a305103ef07.js.map