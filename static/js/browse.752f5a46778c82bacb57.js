/*! For license information please see browse.752f5a46778c82bacb57.js.LICENSE.txt */
!function(t,e){"object"==typeof exports&&"object"==typeof module?module.exports=e():"function"==typeof define&&define.amd?define([],e):"object"==typeof exports?exports.swh=e():(t.swh=t.swh||{},t.swh.browse=e())}(self,(function(){return function(){var t={81808:function(t,e,n){"use strict";n.d(e,{E:function(){return i}});var o=n(91386);function i(){window.location.pathname===Urls.browse_origin_visits()?$("#swh-browse-origin-visits-nav-link").addClass("active"):window.location.pathname===Urls.browse_origin_branches()||window.location.pathname===Urls.browse_snapshot_branches()?$("#swh-browse-snapshot-branches-nav-link").addClass("active"):window.location.pathname===Urls.browse_origin_releases()||window.location.pathname===Urls.browse_snapshot_releases()?$("#swh-browse-snapshot-releases-nav-link").addClass("active"):$("#swh-browse-code-nav-link").addClass("active")}$(document).ready((function(){$(".dropdown-submenu a.dropdown-item").on("click",(function(t){$(t.target).next("div").toggle(),"none"!==$(t.target).next("div").css("display")?$(t.target).focus():$(t.target).blur(),t.stopPropagation(),t.preventDefault()})),$(".swh-popover-toggler").popover({boundary:"viewport",container:"body",html:!0,placement:function(){return $(window).width()<o.Fg?"top":"right"},template:'<div class="popover" role="tooltip">\n                 <div class="arrow"></div>\n                 <h3 class="popover-header"></h3>\n                 <div class="popover-body swh-popover"></div>\n               </div>',content:function(){var t=$(this).attr("data-popover-content");return $(t).children(".popover-body").remove().html()},title:function(){var t=$(this).attr("data-popover-content");return $(t).children(".popover-heading").html()},offset:"50vh",sanitize:!1}),$(".swh-vault-menu a.dropdown-item").on("click",(function(t){$(".swh-popover-toggler").popover("hide")})),$(".swh-popover-toggler").on("show.bs.popover",(function(t){$(".swh-popover-toggler:not(#"+t.currentTarget.id+")").popover("hide"),$(".swh-vault-menu .dropdown-menu").hide()})),$(".swh-actions-dropdown").on("hide.bs.dropdown",(function(){$(".swh-vault-menu .dropdown-menu").hide(),$(".swh-popover-toggler").popover("hide")})),$("body").on("click",(function(t){$(t.target).parents(".swh-popover").length&&t.stopPropagation()}))}))},80:function(t,e,n){"use strict";n.r(e),n.d(e,{initSnapshotNavigation:function(){return o.a},initOriginSearch:function(){return i.A},initBrowseNavbar:function(){return r.E},swhIdContextOptionToggled:function(){return s._},swhIdObjectTypeToggled:function(){return s.Z}});var o=n(47458),i=n(83891),r=n(81808),s=n(66257)},83891:function(t,e,n){"use strict";n.d(e,{A:function(){return p}});var o=n(45149);function i(t,e){var n;if("undefined"==typeof Symbol||null==t[Symbol.iterator]){if(Array.isArray(t)||(n=function(t,e){if(!t)return;if("string"==typeof t)return r(t,e);var n=Object.prototype.toString.call(t).slice(8,-1);"Object"===n&&t.constructor&&(n=t.constructor.name);if("Map"===n||"Set"===n)return Array.from(t);if("Arguments"===n||/^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n))return r(t,e)}(t))||e&&t&&"number"==typeof t.length){n&&(t=n);var o=0;return function(){return o>=t.length?{done:!0}:{done:!1,value:t[o++]}}}throw new TypeError("Invalid attempt to iterate non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.")}return(n=t[Symbol.iterator]()).next.bind(n)}function r(t,e){(null==e||e>t.length)&&(e=t.length);for(var n=0,o=new Array(e);n<e;n++)o[n]=t[n];return o}var s=[],a=null,c=null,l=!1;function u(){$("#origin-search-results tbody tr").remove()}function h(t){if(t.length>0){$("#swh-origin-search-results").show(),$("#swh-no-result").hide(),u();for(var e,n=$("#origin-search-results tbody"),o=function(){var t=e.value,o=t[0],i=t[1],r=Urls.browse_origin()+"?origin_url="+encodeURIComponent(i.url),s='<tr id="origin-'+o+'" class="swh-search-result-entry swh-tr-hover-highlight">';s+='<td id="visit-type-origin-'+o+'" style="width: 120px;"><i title="Checking software origin type" class="mdi mdi-sync mdi-spin mdi-fw"></i>Checking</td>',s+='<td style="white-space: nowrap;"><a href="'+r+'">'+i.url+"</a></td>",s+='<td class="swh-visit-status" id="visit-status-origin-'+o+'"><i title="Checking archiving status" class="mdi mdi-sync mdi-spin mdi-fw"></i>Checking</td>',s+="</tr>",n.append(s);var a=Urls.api_1_origin_visit_latest(i.url);fetch(a+="?require_snapshot=true").then((function(t){return t.json()})).then((function(t){$("#visit-type-origin-"+o).html(t.type),$("#visit-status-origin-"+o).children().remove(),t?$("#visit-status-origin-"+o).html('<i title="Software origin has been archived by Software Heritage" class="mdi mdi-check-bold mdi-fw"></i>Archived'):($("#visit-status-origin-"+o).html('<i title="Software origin archival by Software Heritage is pending" class="mdi mdi-close-thick mdi-fw"></i>Pending archival'),$("#swh-filter-empty-visits").prop("checked")&&$("#origin-"+o).remove())}))},r=i(t.entries());!(e=r()).done;)o();setTimeout((function(){$("#origin-search-results tbody tr").removeAttr("style")}))}else $("#swh-origin-search-results").hide(),$("#swh-no-result").text("No origins matching the search criteria were found."),$("#swh-no-result").show();null===a?$("#origins-next-results-button").addClass("disabled"):$("#origins-next-results-button").removeClass("disabled"),0===s.length?$("#origins-prev-results-button").addClass("disabled"):$("#origins-prev-results-button").removeClass("disabled"),l=!1,setTimeout((function(){window.scrollTo(0,0)}))}function f(t){u(),$(".swh-loading").addClass("show");var e=fetch(t).then(o.ry).then((function(t){return(e=t).json()})).then((function(n){if(c=t,a=null,e.headers.has("Link")){var o=e.headers.get("Link").match(/<(.+)>; rel="next"/)[1];void 0!==o&&(a=o)}$(".swh-loading").removeClass("show"),h(n)})).catch((function(t){$(".swh-loading").removeClass("show"),l=!1,$("#swh-origin-search-results").hide(),$("#swh-no-result").text("Error "+t.status+": "+t.statusText),$("#swh-no-result").show()}))}function d(){$("#swh-no-result").hide();var t=$("#origins-url-patterns").val();if(l=!0,t.startsWith("swh:")){var e=Urls.api_1_resolve_swhid(t);fetch(e).then(o.ry).then((function(t){return t.json()})).then((function(t){window.location=t.browse_url})).catch((function(t){t.json().then((function(t){$("#swh-origin-search-results").hide(),$(".swh-search-pagination").hide(),$("#swh-no-result").text(t.reason),$("#swh-no-result").show()}))}))}else $("#swh-origin-search-results").show(),$(".swh-search-pagination").show(),function(t,e){var n;$("#swh-search-origin-metadata").prop("checked")?(n=new URL(Urls.api_1_origin_metadata_search(),window.location)).searchParams.append("fulltext",t):n=new URL(Urls.api_1_origin_search(t),window.location);var o=$("#swh-search-origins-with-visit").prop("checked");n.searchParams.append("limit",e),n.searchParams.append("with_visit",o),f(n.toString())}(t,100)}function p(){$(document).ready((function(){$("#swh-search-origins").submit((function(t){t.preventDefault();var e=$("#origins-url-patterns").val().trim(),n=$("#swh-search-origins-with-visit").prop("checked"),o=$("#swh-filter-empty-visits").prop("checked"),i=$("#swh-search-origin-metadata").prop("checked"),r=new URLSearchParams;r.append("q",e),n&&r.append("with_visit",n),o&&r.append("with_content",o),i&&r.append("search_metadata",i),window.location=Urls.browse_search()+"?"+r.toString()})),$("#origins-next-results-button").click((function(t){$("#origins-next-results-button").hasClass("disabled")||l||(l=!0,s.push(c),f(a),t.preventDefault())})),$("#origins-prev-results-button").click((function(t){$("#origins-prev-results-button").hasClass("disabled")||l||(l=!0,f(s.pop()),t.preventDefault())}));var t=new URLSearchParams(window.location.search),e=t.get("q"),n=t.has("with_visit"),o=t.has("with_content"),i=t.has("search_metadata");e&&($("#origins-url-patterns").val(e),$("#swh-search-origins-with-visit").prop("checked",n),$("#swh-filter-empty-visits").prop("checked",o),$("#swh-search-origin-metadata").prop("checked",i),d())}))}},47458:function(t,e,n){"use strict";function o(t,e){function n(){$(".swh-releases-switch").removeClass("active"),$(".swh-branches-switch").addClass("active"),$("#swh-tab-releases").removeClass("active"),$("#swh-tab-branches").addClass("active")}function o(){$(".swh-branches-switch").removeClass("active"),$(".swh-releases-switch").addClass("active"),$("#swh-tab-branches").removeClass("active"),$("#swh-tab-releases").addClass("active")}$(document).ready((function(){$(".dropdown-menu a.swh-branches-switch").click((function(t){n(),t.stopPropagation()})),$(".dropdown-menu a.swh-releases-switch").click((function(t){o(),t.stopPropagation()}));var i=!1;$("#swh-branches-releases-dd").on("show.bs.dropdown",(function(){if(!i){var t=$(".swh-branches-releases").width();$(".swh-branches-releases").width(t+25),i=!0}})),t&&(e?n():o())}))}n.d(e,{a:function(){return o}})},66257:function(t,e,n){"use strict";n.d(e,{Z:function(){return s},_:function(){return a}});var o=n(42152),i=n.n(o),r=(n(51902),n(91386));function s(t){t.preventDefault(),$(t.target).tab("show")}function a(t){t.stopPropagation();var e=$(t.target).closest(".swhid-ui").find(".swhid"),n=$(t.target).data("swhid-with-context"),o=$(t.target).data("swhid-with-context-url"),i=e.text();if($(t.target).prop("checked"))e.attr("href",o),i=n.replace(/;/g,";\n");else{var r=i.indexOf(";");-1!==r&&(i=i.slice(0,r)),e.attr("href","/"+i+"/")}e.text(i),c()}function c(){for(var t=$("#swhid-tab-content").find(".swhid"),e=t.text().replace(/;\n/g,";"),n=[],o=";lines=",i=new RegExp(/L(\d+)/g),r=i.exec(window.location.hash);r;)n.push(parseInt(r[1])),r=i.exec(window.location.hash);n.length>0&&(o+=n[0]),n.length>1&&(o+="-"+n[1]),$("#swhid-context-option-content").prop("checked")&&(e=e.replace(/;lines=\d+-*\d*/g,""),n.length>0&&(e+=o),t.text(e.replace(/;/g,";\n")),t.attr("href","/"+e+"/"))}$(document).ready((function(){new(i())(".btn-swhid-copy",{text:function(t){return $(t).closest(".swhid-ui").find(".swhid").text().replace(/;\n/g,";")}}),new(i())(".btn-swhid-url-copy",{text:function(t){var e=$(t).closest(".swhid-ui").find(".swhid").attr("href");return window.location.origin+e}}),.7*window.innerWidth>1e3&&$("#swh-identifiers").css("width","1000px");var t={tabLocation:"right",clickScreenToCloseFilters:[".ui-slideouttab-panel",".modal"],offset:function(){return $(window).width()<r.Fg?"250px":"200px"}};(window.innerHeight<600||window.innerWidth<500)&&(t.otherOffset="20px"),$("#swh-identifiers").tabSlideOut(t),$("#swh-identifiers").css("display","block"),$(".swhid-context-option").trigger("click"),$(window).on("hashchange",(function(){c()})),$("body").click((function(){c()}))}))},51902:function(){!function(t){t.fn.tabSlideOut=function(e){function n(t){return parseInt(t.outerHeight()+1,10)+"px"}function o(){var e=t(window).height();return"top"!==a&&"bottom"!==a||(e=t(window).width()),e-parseInt(s.otherOffset)-parseInt(s.offset)}var i=this;function r(){return i.hasClass("ui-slideouttab-open")}if("string"==typeof e)switch(e){case"open":return this.trigger("open"),this;case"close":return this.trigger("close"),this;case"isOpen":return r();case"toggle":return this.trigger("toggle"),this;case"bounce":return this.trigger("bounce"),this;default:throw new Error("Invalid tabSlideOut command")}else{var s=t.extend({tabLocation:"left",tabHandle:".handle",action:"click",hoverTimeout:5e3,offset:"200px",offsetReverse:!1,otherOffset:null,handleOffset:null,handleOffsetReverse:!1,bounceDistance:"50px",bounceTimes:4,bounceSpeed:300,tabImage:null,tabImageHeight:null,tabImageWidth:null,onLoadSlideOut:!1,clickScreenToClose:!0,clickScreenToCloseFilters:[".ui-slideouttab-panel"],onOpen:function(){},onClose:function(){}},e||{}),a=s.tabLocation,c=s.tabHandle=t(s.tabHandle,i);if(i.addClass("ui-slideouttab-panel").addClass("ui-slideouttab-"+a),s.offsetReverse&&i.addClass("ui-slideouttab-panel-reverse"),c.addClass("ui-slideouttab-handle"),s.handleOffsetReverse&&c.addClass("ui-slideouttab-handle-reverse"),s.toggleButton=t(s.toggleButton),null!==s.tabImage){var l=0,u=0;if(null!==s.tabImageHeight&&null!==s.tabImageWidth)l=s.tabImageHeight,u=s.tabImageWidth;else{var h=new Image;h.src=s.tabImage,l=h.naturalHeight,u=h.naturalWidth}c.addClass("ui-slideouttab-handle-image"),c.css({background:"url("+s.tabImage+") no-repeat",width:u,height:l})}"top"===a||"bottom"===a?(s.panelOffsetFrom=s.offsetReverse?"right":"left",s.handleOffsetFrom=s.handleOffsetReverse?"right":"left"):(s.panelOffsetFrom=s.offsetReverse?"bottom":"top",s.handleOffsetFrom=s.handleOffsetReverse?"bottom":"top"),null===s.handleOffset&&(s.handleOffset="-"+function(t,e){return parseInt(t.css("border-"+e+"-width"),10)}(i,s.handleOffsetFrom)+"px"),"top"===a||"bottom"===a?(i.css(s.panelOffsetFrom,s.offset),c.css(s.handleOffsetFrom,s.handleOffset),null!==s.otherOffset&&(i.css("width",o()+"px"),t(window).resize((function(){i.css("width",o()+"px")}))),"top"===a?c.css({bottom:"-"+n(c)}):c.css({top:"-"+n(c)})):(i.css(s.panelOffsetFrom,s.offset),c.css(s.handleOffsetFrom,s.handleOffset),null!==s.otherOffset&&(i.css("height",o()+"px"),t(window).resize((function(){i.css("height",o()+"px")}))),"left"===a?c.css({right:"0"}):c.css({left:"0"})),c.click((function(t){t.preventDefault()})),s.toggleButton.click((function(t){t.preventDefault()})),i.addClass("ui-slideouttab-ready");var f=function(){i.removeClass("ui-slideouttab-open").trigger("slideouttabclose"),s.onClose()},d=function(){i.addClass("ui-slideouttab-open").trigger("slideouttabopen"),s.onOpen()},p=function(){r()?f():d()},g=[];g[a]="-="+s.bounceDistance;var v=[];v[a]="+="+s.bounceDistance;if(s.clickScreenToClose&&t(document).click((function(e){if(r()&&!i[0].contains(e.target)){for(var n=t(e.target),o=0;o<s.clickScreenToCloseFilters.length;o++){var a=s.clickScreenToCloseFilters[o];if("string"==typeof a){if(n.is(a)||n.parents().is(a))return}else if("function"==typeof a&&a.call(i,e))return}f()}})),"click"===s.action)c.click((function(t){p()}));else if("hover"===s.action){var w=null;i.hover((function(){r()||d(),w=null}),(function(){r()&&null===w&&(w=setTimeout((function(){w&&f(),w=null}),s.hoverTimeout))})),c.click((function(t){r()&&f()}))}s.onLoadSlideOut&&(d(),setTimeout(d,500)),i.on("open",(function(t){r()||d()})),i.on("close",(function(t){r()&&f()})),i.on("toggle",(function(t){p()})),i.on("bounce",(function(t){r()?function(){for(var t=i,e=0;e<s.bounceTimes;e++)t=t.animate(g,s.bounceSpeed).animate(v,s.bounceSpeed);i.trigger("slideouttabbounce")}():function(){for(var t=i,e=0;e<s.bounceTimes;e++)t=t.animate(v,s.bounceSpeed).animate(g,s.bounceSpeed);i.trigger("slideouttabbounce")}()}))}return this}}(jQuery)},91386:function(t,e,n){"use strict";n.d(e,{Fg:function(){return i}});var o=n(45149),i=768;(0,o.TT)("img/swh-spinner.gif")},45149:function(t,e,n){"use strict";function o(t){if(!t.ok)throw t;return t}function i(t){return"/static/"+t}n.d(e,{ry:function(){return o},TT:function(){return i}})},42152:function(t){var e;e=function(){return function(t){var e={};function n(o){if(e[o])return e[o].exports;var i=e[o]={i:o,l:!1,exports:{}};return t[o].call(i.exports,i,i.exports,n),i.l=!0,i.exports}return n.m=t,n.c=e,n.d=function(t,e,o){n.o(t,e)||Object.defineProperty(t,e,{enumerable:!0,get:o})},n.r=function(t){"undefined"!=typeof Symbol&&Symbol.toStringTag&&Object.defineProperty(t,Symbol.toStringTag,{value:"Module"}),Object.defineProperty(t,"__esModule",{value:!0})},n.t=function(t,e){if(1&e&&(t=n(t)),8&e)return t;if(4&e&&"object"==typeof t&&t&&t.__esModule)return t;var o=Object.create(null);if(n.r(o),Object.defineProperty(o,"default",{enumerable:!0,value:t}),2&e&&"string"!=typeof t)for(var i in t)n.d(o,i,function(e){return t[e]}.bind(null,i));return o},n.n=function(t){var e=t&&t.__esModule?function(){return t.default}:function(){return t};return n.d(e,"a",e),e},n.o=function(t,e){return Object.prototype.hasOwnProperty.call(t,e)},n.p="",n(n.s=6)}([function(t,e){t.exports=function(t){var e;if("SELECT"===t.nodeName)t.focus(),e=t.value;else if("INPUT"===t.nodeName||"TEXTAREA"===t.nodeName){var n=t.hasAttribute("readonly");n||t.setAttribute("readonly",""),t.select(),t.setSelectionRange(0,t.value.length),n||t.removeAttribute("readonly"),e=t.value}else{t.hasAttribute("contenteditable")&&t.focus();var o=window.getSelection(),i=document.createRange();i.selectNodeContents(t),o.removeAllRanges(),o.addRange(i),e=o.toString()}return e}},function(t,e){function n(){}n.prototype={on:function(t,e,n){var o=this.e||(this.e={});return(o[t]||(o[t]=[])).push({fn:e,ctx:n}),this},once:function(t,e,n){var o=this;function i(){o.off(t,i),e.apply(n,arguments)}return i._=e,this.on(t,i,n)},emit:function(t){for(var e=[].slice.call(arguments,1),n=((this.e||(this.e={}))[t]||[]).slice(),o=0,i=n.length;o<i;o++)n[o].fn.apply(n[o].ctx,e);return this},off:function(t,e){var n=this.e||(this.e={}),o=n[t],i=[];if(o&&e)for(var r=0,s=o.length;r<s;r++)o[r].fn!==e&&o[r].fn._!==e&&i.push(o[r]);return i.length?n[t]=i:delete n[t],this}},t.exports=n,t.exports.TinyEmitter=n},function(t,e,n){var o=n(3),i=n(4);t.exports=function(t,e,n){if(!t&&!e&&!n)throw new Error("Missing required arguments");if(!o.string(e))throw new TypeError("Second argument must be a String");if(!o.fn(n))throw new TypeError("Third argument must be a Function");if(o.node(t))return function(t,e,n){return t.addEventListener(e,n),{destroy:function(){t.removeEventListener(e,n)}}}(t,e,n);if(o.nodeList(t))return function(t,e,n){return Array.prototype.forEach.call(t,(function(t){t.addEventListener(e,n)})),{destroy:function(){Array.prototype.forEach.call(t,(function(t){t.removeEventListener(e,n)}))}}}(t,e,n);if(o.string(t))return function(t,e,n){return i(document.body,t,e,n)}(t,e,n);throw new TypeError("First argument must be a String, HTMLElement, HTMLCollection, or NodeList")}},function(t,e){e.node=function(t){return void 0!==t&&t instanceof HTMLElement&&1===t.nodeType},e.nodeList=function(t){var n=Object.prototype.toString.call(t);return void 0!==t&&("[object NodeList]"===n||"[object HTMLCollection]"===n)&&"length"in t&&(0===t.length||e.node(t[0]))},e.string=function(t){return"string"==typeof t||t instanceof String},e.fn=function(t){return"[object Function]"===Object.prototype.toString.call(t)}},function(t,e,n){var o=n(5);function i(t,e,n,o,i){var s=r.apply(this,arguments);return t.addEventListener(n,s,i),{destroy:function(){t.removeEventListener(n,s,i)}}}function r(t,e,n,i){return function(n){n.delegateTarget=o(n.target,e),n.delegateTarget&&i.call(t,n)}}t.exports=function(t,e,n,o,r){return"function"==typeof t.addEventListener?i.apply(null,arguments):"function"==typeof n?i.bind(null,document).apply(null,arguments):("string"==typeof t&&(t=document.querySelectorAll(t)),Array.prototype.map.call(t,(function(t){return i(t,e,n,o,r)})))}},function(t,e){if("undefined"!=typeof Element&&!Element.prototype.matches){var n=Element.prototype;n.matches=n.matchesSelector||n.mozMatchesSelector||n.msMatchesSelector||n.oMatchesSelector||n.webkitMatchesSelector}t.exports=function(t,e){for(;t&&9!==t.nodeType;){if("function"==typeof t.matches&&t.matches(e))return t;t=t.parentNode}}},function(t,e,n){"use strict";n.r(e);var o=n(0),i=n.n(o),r="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},s=function(){function t(t,e){for(var n=0;n<e.length;n++){var o=e[n];o.enumerable=o.enumerable||!1,o.configurable=!0,"value"in o&&(o.writable=!0),Object.defineProperty(t,o.key,o)}}return function(e,n,o){return n&&t(e.prototype,n),o&&t(e,o),e}}(),a=function(){function t(e){!function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,t),this.resolveOptions(e),this.initSelection()}return s(t,[{key:"resolveOptions",value:function(){var t=arguments.length>0&&void 0!==arguments[0]?arguments[0]:{};this.action=t.action,this.container=t.container,this.emitter=t.emitter,this.target=t.target,this.text=t.text,this.trigger=t.trigger,this.selectedText=""}},{key:"initSelection",value:function(){this.text?this.selectFake():this.target&&this.selectTarget()}},{key:"selectFake",value:function(){var t=this,e="rtl"==document.documentElement.getAttribute("dir");this.removeFake(),this.fakeHandlerCallback=function(){return t.removeFake()},this.fakeHandler=this.container.addEventListener("click",this.fakeHandlerCallback)||!0,this.fakeElem=document.createElement("textarea"),this.fakeElem.style.fontSize="12pt",this.fakeElem.style.border="0",this.fakeElem.style.padding="0",this.fakeElem.style.margin="0",this.fakeElem.style.position="absolute",this.fakeElem.style[e?"right":"left"]="-9999px";var n=window.pageYOffset||document.documentElement.scrollTop;this.fakeElem.style.top=n+"px",this.fakeElem.setAttribute("readonly",""),this.fakeElem.value=this.text,this.container.appendChild(this.fakeElem),this.selectedText=i()(this.fakeElem),this.copyText()}},{key:"removeFake",value:function(){this.fakeHandler&&(this.container.removeEventListener("click",this.fakeHandlerCallback),this.fakeHandler=null,this.fakeHandlerCallback=null),this.fakeElem&&(this.container.removeChild(this.fakeElem),this.fakeElem=null)}},{key:"selectTarget",value:function(){this.selectedText=i()(this.target),this.copyText()}},{key:"copyText",value:function(){var t=void 0;try{t=document.execCommand(this.action)}catch(e){t=!1}this.handleResult(t)}},{key:"handleResult",value:function(t){this.emitter.emit(t?"success":"error",{action:this.action,text:this.selectedText,trigger:this.trigger,clearSelection:this.clearSelection.bind(this)})}},{key:"clearSelection",value:function(){this.trigger&&this.trigger.focus(),document.activeElement.blur(),window.getSelection().removeAllRanges()}},{key:"destroy",value:function(){this.removeFake()}},{key:"action",set:function(){var t=arguments.length>0&&void 0!==arguments[0]?arguments[0]:"copy";if(this._action=t,"copy"!==this._action&&"cut"!==this._action)throw new Error('Invalid "action" value, use either "copy" or "cut"')},get:function(){return this._action}},{key:"target",set:function(t){if(void 0!==t){if(!t||"object"!==(void 0===t?"undefined":r(t))||1!==t.nodeType)throw new Error('Invalid "target" value, use a valid Element');if("copy"===this.action&&t.hasAttribute("disabled"))throw new Error('Invalid "target" attribute. Please use "readonly" instead of "disabled" attribute');if("cut"===this.action&&(t.hasAttribute("readonly")||t.hasAttribute("disabled")))throw new Error('Invalid "target" attribute. You can\'t cut text from elements with "readonly" or "disabled" attributes');this._target=t}},get:function(){return this._target}}]),t}(),c=n(1),l=n.n(c),u=n(2),h=n.n(u),f="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t},d=function(){function t(t,e){for(var n=0;n<e.length;n++){var o=e[n];o.enumerable=o.enumerable||!1,o.configurable=!0,"value"in o&&(o.writable=!0),Object.defineProperty(t,o.key,o)}}return function(e,n,o){return n&&t(e.prototype,n),o&&t(e,o),e}}(),p=function(t){function e(t,n){!function(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}(this,e);var o=function(t,e){if(!t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return!e||"object"!=typeof e&&"function"!=typeof e?t:e}(this,(e.__proto__||Object.getPrototypeOf(e)).call(this));return o.resolveOptions(n),o.listenClick(t),o}return function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function, not "+typeof e);t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,enumerable:!1,writable:!0,configurable:!0}}),e&&(Object.setPrototypeOf?Object.setPrototypeOf(t,e):t.__proto__=e)}(e,t),d(e,[{key:"resolveOptions",value:function(){var t=arguments.length>0&&void 0!==arguments[0]?arguments[0]:{};this.action="function"==typeof t.action?t.action:this.defaultAction,this.target="function"==typeof t.target?t.target:this.defaultTarget,this.text="function"==typeof t.text?t.text:this.defaultText,this.container="object"===f(t.container)?t.container:document.body}},{key:"listenClick",value:function(t){var e=this;this.listener=h()(t,"click",(function(t){return e.onClick(t)}))}},{key:"onClick",value:function(t){var e=t.delegateTarget||t.currentTarget;this.clipboardAction&&(this.clipboardAction=null),this.clipboardAction=new a({action:this.action(e),target:this.target(e),text:this.text(e),container:this.container,trigger:e,emitter:this})}},{key:"defaultAction",value:function(t){return g("action",t)}},{key:"defaultTarget",value:function(t){var e=g("target",t);if(e)return document.querySelector(e)}},{key:"defaultText",value:function(t){return g("text",t)}},{key:"destroy",value:function(){this.listener.destroy(),this.clipboardAction&&(this.clipboardAction.destroy(),this.clipboardAction=null)}}],[{key:"isSupported",value:function(){var t=arguments.length>0&&void 0!==arguments[0]?arguments[0]:["copy","cut"],e="string"==typeof t?[t]:t,n=!!document.queryCommandSupported;return e.forEach((function(t){n=n&&!!document.queryCommandSupported(t)})),n}}]),e}(l.a);function g(t,e){var n="data-clipboard-"+t;if(e.hasAttribute(n))return e.getAttribute(n)}e.default=p}]).default},t.exports=e()}},e={};function n(o){if(e[o])return e[o].exports;var i=e[o]={exports:{}};return t[o].call(i.exports,i,i.exports,n),i.exports}return n.n=function(t){var e=t&&t.__esModule?function(){return t.default}:function(){return t};return n.d(e,{a:e}),e},n.d=function(t,e){for(var o in e)n.o(e,o)&&!n.o(t,o)&&Object.defineProperty(t,o,{enumerable:!0,get:e[o]})},n.o=function(t,e){return Object.prototype.hasOwnProperty.call(t,e)},n.r=function(t){"undefined"!=typeof Symbol&&Symbol.toStringTag&&Object.defineProperty(t,Symbol.toStringTag,{value:"Module"}),Object.defineProperty(t,"__esModule",{value:!0})},n(80)}()}));
//# sourceMappingURL=browse.752f5a46778c82bacb57.js.map