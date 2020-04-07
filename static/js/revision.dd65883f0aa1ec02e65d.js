/*! For license information please see revision.dd65883f0aa1ec02e65d.js.LICENSE.txt */
!function(t,e){"object"==typeof exports&&"object"==typeof module?module.exports=e():"function"==typeof define&&define.amd?define([],e):"object"==typeof exports?exports.revision=e():(t.swh=t.swh||{},t.swh.revision=e())}(window,(function(){return function(t){function e(e){for(var n,r,o=e[0],s=e[1],a=0,l=[];a<o.length;a++)r=o[a],Object.prototype.hasOwnProperty.call(i,r)&&i[r]&&l.push(i[r][0]),i[r]=0;for(n in s)Object.prototype.hasOwnProperty.call(s,n)&&(t[n]=s[n]);for(c&&c(e);l.length;)l.shift()()}var n={},r={8:0},i={8:0};function o(e){if(n[e])return n[e].exports;var r=n[e]={i:e,l:!1,exports:{}};return t[e].call(r.exports,r,r.exports,o),r.l=!0,r.exports}o.e=function(t){var e=[];r[t]?e.push(r[t]):0!==r[t]&&{0:1,4:1}[t]&&e.push(r[t]=new Promise((function(e,n){for(var i="css/"+({0:"vendors",4:"highlightjs"}[t]||t)+"."+{0:"16c5faca7f1aaeb3f3b3",4:"a98fddf4f9839f376ace"}[t]+".css",s=o.p+i,a=document.getElementsByTagName("link"),l=0;l<a.length;l++){var c=(f=a[l]).getAttribute("data-href")||f.getAttribute("href");if("stylesheet"===f.rel&&(c===i||c===s))return e()}var u=document.getElementsByTagName("style");for(l=0;l<u.length;l++){var f;if((c=(f=u[l]).getAttribute("data-href"))===i||c===s)return e()}var d=document.createElement("link");d.rel="stylesheet",d.type="text/css",d.onload=e,d.onerror=function(e){var i=e&&e.target&&e.target.src||s,o=new Error("Loading CSS chunk "+t+" failed.\n("+i+")");o.code="CSS_CHUNK_LOAD_FAILED",o.request=i,delete r[t],d.parentNode.removeChild(d),n(o)},d.href=s,document.getElementsByTagName("head")[0].appendChild(d)})).then((function(){r[t]=0})));var n=i[t];if(0!==n)if(n)e.push(n[2]);else{var s=new Promise((function(e,r){n=i[t]=[e,r]}));e.push(n[2]=s);var a,l=document.createElement("script");l.charset="utf-8",l.timeout=120,o.nc&&l.setAttribute("nonce",o.nc),l.src=function(t){return o.p+"js/"+({0:"vendors",4:"highlightjs"}[t]||t)+"."+{0:"16c5faca7f1aaeb3f3b3",4:"a98fddf4f9839f376ace"}[t]+".js"}(t);var c=new Error;a=function(e){l.onerror=l.onload=null,clearTimeout(u);var n=i[t];if(0!==n){if(n){var r=e&&("load"===e.type?"missing":e.type),o=e&&e.target&&e.target.src;c.message="Loading chunk "+t+" failed.\n("+r+": "+o+")",c.name="ChunkLoadError",c.type=r,c.request=o,n[1](c)}i[t]=void 0}};var u=setTimeout((function(){a({type:"timeout",target:l})}),12e4);l.onerror=l.onload=a,document.head.appendChild(l)}return Promise.all(e)},o.m=t,o.c=n,o.d=function(t,e,n){o.o(t,e)||Object.defineProperty(t,e,{enumerable:!0,get:n})},o.r=function(t){"undefined"!=typeof Symbol&&Symbol.toStringTag&&Object.defineProperty(t,Symbol.toStringTag,{value:"Module"}),Object.defineProperty(t,"__esModule",{value:!0})},o.t=function(t,e){if(1&e&&(t=o(t)),8&e)return t;if(4&e&&"object"==typeof t&&t&&t.__esModule)return t;var n=Object.create(null);if(o.r(n),Object.defineProperty(n,"default",{enumerable:!0,value:t}),2&e&&"string"!=typeof t)for(var r in t)o.d(n,r,function(e){return t[e]}.bind(null,r));return n},o.n=function(t){var e=t&&t.__esModule?function(){return t.default}:function(){return t};return o.d(e,"a",e),e},o.o=function(t,e){return Object.prototype.hasOwnProperty.call(t,e)},o.p="/static/",o.oe=function(t){throw console.error(t),t};var s=window.webpackJsonp=window.webpackJsonp||[],a=s.push.bind(s);s.push=e,s=s.slice();for(var l=0;l<s.length;l++)e(s[l]);var c=a;return o(o.s=251)}({15:function(t,e,n){t.exports=n(77)},162:function(t,e,n){"use strict";n.d(e,"b",(function(){return y})),n.d(e,"e",(function(){return k})),n.d(e,"d",(function(){return S})),n.d(e,"a",(function(){return j})),n.d(e,"c",(function(){return A}));var r=n(15),i=n.n(r),o=n(24),s=n.n(o),a=(n(254),n(21)),l=null,c=0,u=0,f=0,d=0,h={},p={};function g(t){var e=$(t).offset().top,n=e+$(t).outerHeight(),r=$(window).scrollTop(),i=r+$(window).height();return n>r&&e<i}function v(t,e,n){var r="";if(null!=t){for(var i=0;i<n-t.length;++i)r+=" ";r+=t}if(null!=t&&null!=e&&(r+="  "),null!=e){for(var o=0;o<n-e.length;++o)r+=" ";r+=e}return r}function y(t,e){-1===t.indexOf("force=true")&&h.hasOwnProperty(e)||(h[e]=!0,$("#"+e+"-loading").css("visibility","visible"),$("#"+e+"-loading").css("display","block"),$("#"+e+"-highlightjs").css("display","none"),fetch(t).then((function(t){return t.json()})).then((function(n){++u===l.length&&$("#swh-compute-all-diffs").addClass("active"),0===n.diff_str.indexOf("Large diff")?($("#"+e)[0].innerHTML=n.diff_str+'<br/><button class="btn btn-default btn-sm" type="button"\n           onclick="swh.revision.computeDiff(\''+t+"&force=true', '"+e+"')\">Request diff</button>",w(e)):0!==n.diff_str.indexOf("@@")?($("#"+e).text(n.diff_str),w(e)):($("."+e).removeClass("nohighlight"),$("."+e).addClass(n.language),$("#"+e).text(n.diff_str),$("#"+e).each((function(t,e){hljs.highlightBlock(e),hljs.lineNumbersBlock(e)})),setTimeout((function(){var t="",r="",i=[],o=[],s=[],a=0,l="",c="",u=0;$("#"+e+" .hljs-ln-numbers").each((function(e,n){var h=n.nextSibling.innerText,p=function(t){var e,n;if(t.startsWith("@@")){var r=new RegExp(/^@@ -(\d+),(\d+) \+(\d+),(\d+) @@$/gm),i=new RegExp(/^@@ -(\d+) \+(\d+),(\d+) @@$/gm),o=new RegExp(/^@@ -(\d+),(\d+) \+(\d+) @@$/gm),s=new RegExp(/^@@ -(\d+) \+(\d+) @@$/gm),a=r.exec(t),l=i.exec(t),c=o.exec(t),u=s.exec(t);a?(e=parseInt(a[1])-1,n=parseInt(a[3])-1):l?(e=parseInt(l[1])-1,n=parseInt(l[2])-1):c?(e=parseInt(c[1])-1,n=parseInt(c[3])-1):u&&(e=parseInt(u[1])-1,n=parseInt(u[2])-1)}return void 0!==e?[e,n]:null}(h),g="",v="";if(p)t=p[0],r=p[1],u=0,l+=h+"\n",c+=h+"\n",o.push(""),s.push("");else if(h.length>0&&"-"===h[0])g=(t+=1).toString(),o.push(g),++d,l+=h+"\n",++u;else if(h.length>0&&"+"===h[0])v=(r+=1).toString(),s.push(v),++f,c+=h+"\n",--u;else{r+=1,g=(t+=1).toString(),v=r.toString();for(var y=0;y<Math.abs(u);++y)u>0?(c+="\n",s.push("")):(l+="\n",o.push(""));u=0,l+=h+"\n",c+=h+"\n",s.push(v),o.push(g)}t||(g=""),r||(v=""),i[e]=[g,v],a=Math.max(a,g.length),a=Math.max(a,v.length)})),$("#"+e+"-from").text(l),$("#"+e+"-to").text(c),$("#"+e+"-from, #"+e+"-to").each((function(t,e){hljs.highlightBlock(e),hljs.lineNumbersBlock(e)})),setTimeout((function(){$("."+e+" .hljs-ln-numbers").each((function(t,e){var n=e.nextSibling.innerText;if(n.startsWith("@@")){$(e).parent().addClass("swh-diff-lines-info");var r=$(e).parent().find(".hljs-ln-code .hljs-ln-line").text();$(e).parent().find(".hljs-ln-code .hljs-ln-line").children().remove(),$(e).parent().find(".hljs-ln-code .hljs-ln-line").text(""),$(e).parent().find(".hljs-ln-code .hljs-ln-line").append('<span class="hljs-meta">'+r+"</span>")}else n.length>0&&"-"===n[0]?$(e).parent().addClass("swh-diff-removed-line"):n.length>0&&"+"===n[0]&&$(e).parent().addClass("swh-diff-added-line")})),$("#"+e+" .hljs-ln-numbers").each((function(t,e){$(e).children().attr("data-line-number",v(i[t][0],i[t][1],a))})),$("#"+e+"-from .hljs-ln-numbers").each((function(t,e){$(e).children().attr("data-line-number",v(o[t],null,a))})),$("#"+e+"-to .hljs-ln-numbers").each((function(t,e){$(e).children().attr("data-line-number",v(null,s[t],a))})),$("."+e+" .hljs-ln-code").each((function(t,e){if(e.firstChild){if("#text"!==e.firstChild.nodeName){var n=e.firstChild.innerHTML;if("-"===n[0]||"+"===n[0]){e.firstChild.innerHTML=n.substr(1);var r=document.createTextNode(n[0]);$(e).prepend(r)}}$(e).contents().filter((function(t,e){return 3===e.nodeType})).each((function(t,n){-1!==n.textContent.indexOf("[swh-no-nl-marker]")&&(n.textContent=n.textContent.replace("[swh-no-nl-marker]",""),$(e).append($('<span class="no-nl-marker" title="No newline at end of file"><svg aria-hidden="true" height="16" version="1.1" viewBox="0 0 16 16" width="16"><path fill-rule="evenodd" d="M16 5v3c0 .55-.45 1-1 1h-3v2L9 8l3-3v2h2V5h2zM8 8c0 2.2-1.8 4-4 4s-4-1.8-4-4 1.8-4 4-4 4 1.8 4 4zM1.5 9.66L5.66 5.5C5.18 5.19 4.61 5 4 5 2.34 5 1 6.34 1 8c0 .61.19 1.17.5 1.66zM7 8c0-.61-.19-1.17-.5-1.66L2.34 10.5c.48.31 1.05.5 1.66.5 1.66 0 3-1.34 3-3z"></path></svg></span>')))}))}})),0!==n.diff_str.indexOf("Diffs are not generated for non textual content")&&$("#panel_"+e+" .diff-styles").css("visibility","visible"),w(e)}))})))})))}function w(t){$("#"+t+"-loading").css("display","none"),$("#"+t+"-highlightjs").css("display","block"),$("#swh-revision-lines-added").text(f+" additions"),$("#swh-revision-lines-deleted").text(d+" deletions"),$("#swh-nb-diffs-computed").text(u),Waypoint.refreshAll()}function m(){$(".swh-file-diff-panel").each((function(t,e){if(g(e)){var n=e.id.replace("panel_","");y(p[n],n)}}))}function b(t){var e=t.path;return"rename"===t.type&&(e=t.from_path+" &rarr; "+t.to_path),'<div id="panel_'+t.id+'" class="card swh-file-diff-panel">\n    <div class="card-header bg-gray-light border-bottom-0">\n      <a data-toggle="collapse" href="#panel_'+t.id+'_content">\n        <div class="pull-left swh-title-color">\n          <strong>'+e+'</strong>\n        </div>\n      </a>\n      <div class="pull-right">\n        <div class="btn-group btn-group-toggle diff-styles" data-toggle="buttons" style="visibility: hidden;">\n          <label class="btn btn-default btn-sm form-check-label active unified-diff-button" onclick="swh.revision.showUnifiedDiff(event, \''+t.id+'\')">\n            <input type="radio" name="diffs-switch" id="unified" autocomplete="off" checked> Unified\n          </label>\n          <label class="btn btn-default btn-sm form-check-label splitted-diff-button" onclick="swh.revision.showSplittedDiff(event, \''+t.id+'\')">\n            <input type="radio" name="diffs-switch" id="side-by-side" autocomplete="off"> Side-by-side\n          </label>\n        </div>\n        <a href="'+t.content_url+'" class="btn btn-default btn-sm" role="button">View file</a>\n      </div>\n      <div class="clearfix"></div>\n    </div>\n    <div id="panel_'+t.id+'_content" class="collapse show">\n      <div class="swh-diff-loading text-center" id="'+t.id+'-loading" style="visibility: hidden;">\n        <img src='+a.c+'></img>\n        <p>Loading diff ...</p>\n      </div>\n      <div class="highlightjs swh-content" style="display: none;" id="'+t.id+'-highlightjs">\n        <div id="'+t.id+'-unified-diff">\n          <pre><code class="'+t.id+'" id="'+t.id+'"></code></pre>\n        </div>\n        <div style="width: 100%; display: none;" id="'+t.id+'-splitted-diff">\n          <pre class="float-left" style="width: 50%;"><code class="'+t.id+'" id="'+t.id+'-from"></code></pre>\n          <pre style="width: 50%"><code class="'+t.id+'" id="'+t.id+'-to"></code></pre>\n        </div>\n      </div>\n    </div>\n  </div>'}function x(){for(var t=0;t<l.length;++t){var e=l[t];$("#panel_"+e.id).waypoint({handler:function(){if(g(this.element)){var t=this.element.id.replace("panel_","");y(p[t],t),this.destroy()}},offset:"100%"}),$("#panel_"+e.id).waypoint({handler:function(){if(g(this.element)){var t=this.element.id.replace("panel_","");y(p[t],t),this.destroy()}},offset:function(){return-$(this.element).height()}})}Waypoint.refreshAll()}function k(t,e){$("#"+e+"-splitted-diff").css("display","none"),$("#"+e+"-unified-diff").css("display","block")}function S(t,e){$("#"+e+"-unified-diff").css("display","none"),$("#"+e+"-splitted-diff").css("display","block")}function j(t){for(var e in $(t.currentTarget).addClass("active"),p)p.hasOwnProperty(e)&&y(p[e],e);t.stopPropagation()}function A(t,e){return T.apply(this,arguments)}function T(){return(T=s()(i.a.mark((function t(e,r){return i.a.wrap((function(t){for(;;)switch(t.prev=t.next){case 0:return t.next=2,Promise.all([n.e(0),n.e(4)]).then(n.bind(null,118));case 2:$(document).on("shown.bs.tab",'a[data-toggle="tab"]',(function(t){if("Changes"===t.currentTarget.text.trim()){if($("#readme-panel").css("display","none"),l)return;fetch(r).then((function(t){return t.json()})).then((function(t){l=t.changes;var e=(c=t.total_nb_changes)+" changed file";1!==c&&(e+="s"),$("#swh-revision-changed-files").text(e),$("#swh-total-nb-diffs").text(l.length),$("#swh-revision-changes-list pre")[0].innerHTML=t.changes_msg,$("#swh-revision-changes-loading").css("display","none"),$("#swh-revision-changes-list pre").css("display","block"),$("#swh-compute-all-diffs").css("visibility","visible"),$("#swh-revision-changes-list").removeClass("in"),c>l.length&&($("#swh-too-large-revision-diff").css("display","block"),$("#swh-nb-loaded-diffs").text(l.length));for(var n=0;n<l.length;++n){var r=l[n];p[r.id]=r.diff_url,$("#swh-revision-diffs").append(b(r))}x(),m()}))}else"Files"===t.currentTarget.text.trim()&&$("#readme-panel").css("display","block")})),$(document).ready((function(){e.length>0?$("#swh-revision-message").addClass("in"):$("#swh-collapse-revision-message").attr("data-toggle","");var t=$("html, body");$('#swh-revision-changes-list a[href^="#"], #back-to-top a[href^="#"]').click((function(e){var n=$.attr(e.currentTarget,"href");return Waypoint.disableAll(),t.animate({scrollTop:$(n).offset().top},{duration:500,complete:function(){window.location.hash=n,Waypoint.enableAll(),m()}}),!1}))}));case 4:case"end":return t.stop()}}),t)})))).apply(this,arguments)}},163:function(t,e,n){"use strict";function r(t){var e=new URLSearchParams(window.location.search);$(t.target).val()?e.set("revs_ordering",$(t.target).val()):e.has("revs_ordering")&&e.delete("revs_ordering"),window.location.search=e.toString()}function i(){$(document).ready((function(){var t=new URLSearchParams(window.location.search).get("revs_ordering");t&&$(':input[value="'+t+'"]').prop("checked",!0)}))}n.d(e,"b",(function(){return r})),n.d(e,"a",(function(){return i}))},2:function(t,e,n){"use strict";function r(t){if(!t.ok)throw t;return t}function i(t){for(var e=0;e<t.length;++e)if(!t[e].ok)throw t[e];return t}function o(t){return"/static/"+t}function s(t,e,n){return void 0===e&&(e={}),void 0===n&&(n=null),e["X-CSRFToken"]=Cookies.get("csrftoken"),fetch(t,{credentials:"include",headers:e,method:"POST",body:n})}function a(t,e){return new RegExp("(?:git|https?|git@)(?:\\:\\/\\/)?"+e+"[/|:][A-Za-z0-9-/]+?\\/[\\w\\.-]+\\/?(?!=.git)(?:\\.git(?:\\/?|\\#[\\w\\.\\-_]+)?)?$").test(t)}function l(){history.replaceState("",document.title,window.location.pathname+window.location.search)}function c(t,e){var n=window.getSelection();n.removeAllRanges();var r=document.createRange();r.setStart(t,0),"#text"!==e.nodeName?r.setEnd(e,e.childNodes.length):r.setEnd(e,e.textContent.length),n.addRange(r)}function u(t,e,n){void 0===n&&(n=!1);var r="",i="";return n&&(r='<button type="button" class="close" data-dismiss="alert" aria-label="Close">\n        <span aria-hidden="true">&times;</span>\n      </button>',i="alert-dismissible"),'<div class="alert alert-'+t+" "+i+'" role="alert">'+e+r+"</div>"}n.d(e,"b",(function(){return r})),n.d(e,"c",(function(){return i})),n.d(e,"h",(function(){return o})),n.d(e,"a",(function(){return s})),n.d(e,"e",(function(){return a})),n.d(e,"f",(function(){return l})),n.d(e,"g",(function(){return c})),n.d(e,"d",(function(){return u}))},21:function(t,e,n){"use strict";n.d(e,"b",(function(){return i})),n.d(e,"a",(function(){return o})),n.d(e,"c",(function(){return s}));var r=n(2),i=768,o=992,s=Object(r.h)("img/swh-spinner.gif")},24:function(t,e){function n(t,e,n,r,i,o,s){try{var a=t[o](s),l=a.value}catch(t){return void n(t)}a.done?e(l):Promise.resolve(l).then(r,i)}t.exports=function(t){return function(){var e=this,r=arguments;return new Promise((function(i,o){var s=t.apply(e,r);function a(t){n(s,i,o,a,l,"next",t)}function l(t){n(s,i,o,a,l,"throw",t)}a(void 0)}))}}},251:function(t,e,n){t.exports=n(252)},252:function(t,e,n){"use strict";n.r(e);n(253);var r=n(162);n.d(e,"computeDiff",(function(){return r.b})),n.d(e,"showUnifiedDiff",(function(){return r.e})),n.d(e,"showSplittedDiff",(function(){return r.d})),n.d(e,"computeAllDiffs",(function(){return r.a})),n.d(e,"initRevisionDiff",(function(){return r.c}));var i=n(163);n.d(e,"revsOrderingTypeClicked",(function(){return i.b})),n.d(e,"initRevisionsLog",(function(){return i.a}))},253:function(t,e,n){},254:function(t,e){!function(){"use strict";var t=0,e={};function n(r){if(!r)throw new Error("No options passed to Waypoint constructor");if(!r.element)throw new Error("No element option passed to Waypoint constructor");if(!r.handler)throw new Error("No handler option passed to Waypoint constructor");this.key="waypoint-"+t,this.options=n.Adapter.extend({},n.defaults,r),this.element=this.options.element,this.adapter=new n.Adapter(this.element),this.callback=r.handler,this.axis=this.options.horizontal?"horizontal":"vertical",this.enabled=this.options.enabled,this.triggerPoint=null,this.group=n.Group.findOrCreate({name:this.options.group,axis:this.axis}),this.context=n.Context.findOrCreateByElement(this.options.context),n.offsetAliases[this.options.offset]&&(this.options.offset=n.offsetAliases[this.options.offset]),this.group.add(this),this.context.add(this),e[this.key]=this,t+=1}n.prototype.queueTrigger=function(t){this.group.queueTrigger(this,t)},n.prototype.trigger=function(t){this.enabled&&this.callback&&this.callback.apply(this,t)},n.prototype.destroy=function(){this.context.remove(this),this.group.remove(this),delete e[this.key]},n.prototype.disable=function(){return this.enabled=!1,this},n.prototype.enable=function(){return this.context.refresh(),this.enabled=!0,this},n.prototype.next=function(){return this.group.next(this)},n.prototype.previous=function(){return this.group.previous(this)},n.invokeAll=function(t){var n=[];for(var r in e)n.push(e[r]);for(var i=0,o=n.length;i<o;i++)n[i][t]()},n.destroyAll=function(){n.invokeAll("destroy")},n.disableAll=function(){n.invokeAll("disable")},n.enableAll=function(){for(var t in n.Context.refreshAll(),e)e[t].enabled=!0;return this},n.refreshAll=function(){n.Context.refreshAll()},n.viewportHeight=function(){return window.innerHeight||document.documentElement.clientHeight},n.viewportWidth=function(){return document.documentElement.clientWidth},n.adapters=[],n.defaults={context:window,continuous:!0,enabled:!0,group:"default",horizontal:!1,offset:0},n.offsetAliases={"bottom-in-view":function(){return this.context.innerHeight()-this.adapter.outerHeight()},"right-in-view":function(){return this.context.innerWidth()-this.adapter.outerWidth()}},window.Waypoint=n}(),function(){"use strict";function t(t){window.setTimeout(t,1e3/60)}var e=0,n={},r=window.Waypoint,i=window.onload;function o(t){this.element=t,this.Adapter=r.Adapter,this.adapter=new this.Adapter(t),this.key="waypoint-context-"+e,this.didScroll=!1,this.didResize=!1,this.oldScroll={x:this.adapter.scrollLeft(),y:this.adapter.scrollTop()},this.waypoints={vertical:{},horizontal:{}},t.waypointContextKey=this.key,n[t.waypointContextKey]=this,e+=1,r.windowContext||(r.windowContext=!0,r.windowContext=new o(window)),this.createThrottledScrollHandler(),this.createThrottledResizeHandler()}o.prototype.add=function(t){var e=t.options.horizontal?"horizontal":"vertical";this.waypoints[e][t.key]=t,this.refresh()},o.prototype.checkEmpty=function(){var t=this.Adapter.isEmptyObject(this.waypoints.horizontal),e=this.Adapter.isEmptyObject(this.waypoints.vertical),r=this.element==this.element.window;t&&e&&!r&&(this.adapter.off(".waypoints"),delete n[this.key])},o.prototype.createThrottledResizeHandler=function(){var t=this;function e(){t.handleResize(),t.didResize=!1}this.adapter.on("resize.waypoints",(function(){t.didResize||(t.didResize=!0,r.requestAnimationFrame(e))}))},o.prototype.createThrottledScrollHandler=function(){var t=this;function e(){t.handleScroll(),t.didScroll=!1}this.adapter.on("scroll.waypoints",(function(){t.didScroll&&!r.isTouch||(t.didScroll=!0,r.requestAnimationFrame(e))}))},o.prototype.handleResize=function(){r.Context.refreshAll()},o.prototype.handleScroll=function(){var t={},e={horizontal:{newScroll:this.adapter.scrollLeft(),oldScroll:this.oldScroll.x,forward:"right",backward:"left"},vertical:{newScroll:this.adapter.scrollTop(),oldScroll:this.oldScroll.y,forward:"down",backward:"up"}};for(var n in e){var r=e[n],i=r.newScroll>r.oldScroll?r.forward:r.backward;for(var o in this.waypoints[n]){var s=this.waypoints[n][o];if(null!==s.triggerPoint){var a=r.oldScroll<s.triggerPoint,l=r.newScroll>=s.triggerPoint;(a&&l||!a&&!l)&&(s.queueTrigger(i),t[s.group.id]=s.group)}}}for(var c in t)t[c].flushTriggers();this.oldScroll={x:e.horizontal.newScroll,y:e.vertical.newScroll}},o.prototype.innerHeight=function(){return this.element==this.element.window?r.viewportHeight():this.adapter.innerHeight()},o.prototype.remove=function(t){delete this.waypoints[t.axis][t.key],this.checkEmpty()},o.prototype.innerWidth=function(){return this.element==this.element.window?r.viewportWidth():this.adapter.innerWidth()},o.prototype.destroy=function(){var t=[];for(var e in this.waypoints)for(var n in this.waypoints[e])t.push(this.waypoints[e][n]);for(var r=0,i=t.length;r<i;r++)t[r].destroy()},o.prototype.refresh=function(){var t,e=this.element==this.element.window,n=e?void 0:this.adapter.offset(),i={};for(var o in this.handleScroll(),t={horizontal:{contextOffset:e?0:n.left,contextScroll:e?0:this.oldScroll.x,contextDimension:this.innerWidth(),oldScroll:this.oldScroll.x,forward:"right",backward:"left",offsetProp:"left"},vertical:{contextOffset:e?0:n.top,contextScroll:e?0:this.oldScroll.y,contextDimension:this.innerHeight(),oldScroll:this.oldScroll.y,forward:"down",backward:"up",offsetProp:"top"}}){var s=t[o];for(var a in this.waypoints[o]){var l,c,u,f,d=this.waypoints[o][a],h=d.options.offset,p=d.triggerPoint,g=0,v=null==p;d.element!==d.element.window&&(g=d.adapter.offset()[s.offsetProp]),"function"==typeof h?h=h.apply(d):"string"==typeof h&&(h=parseFloat(h),d.options.offset.indexOf("%")>-1&&(h=Math.ceil(s.contextDimension*h/100))),l=s.contextScroll-s.contextOffset,d.triggerPoint=Math.floor(g+l-h),c=p<s.oldScroll,u=d.triggerPoint>=s.oldScroll,f=!c&&!u,!v&&(c&&u)?(d.queueTrigger(s.backward),i[d.group.id]=d.group):!v&&f?(d.queueTrigger(s.forward),i[d.group.id]=d.group):v&&s.oldScroll>=d.triggerPoint&&(d.queueTrigger(s.forward),i[d.group.id]=d.group)}}return r.requestAnimationFrame((function(){for(var t in i)i[t].flushTriggers()})),this},o.findOrCreateByElement=function(t){return o.findByElement(t)||new o(t)},o.refreshAll=function(){for(var t in n)n[t].refresh()},o.findByElement=function(t){return n[t.waypointContextKey]},window.onload=function(){i&&i(),o.refreshAll()},r.requestAnimationFrame=function(e){(window.requestAnimationFrame||window.mozRequestAnimationFrame||window.webkitRequestAnimationFrame||t).call(window,e)},r.Context=o}(),function(){"use strict";function t(t,e){return t.triggerPoint-e.triggerPoint}function e(t,e){return e.triggerPoint-t.triggerPoint}var n={vertical:{},horizontal:{}},r=window.Waypoint;function i(t){this.name=t.name,this.axis=t.axis,this.id=this.name+"-"+this.axis,this.waypoints=[],this.clearTriggerQueues(),n[this.axis][this.name]=this}i.prototype.add=function(t){this.waypoints.push(t)},i.prototype.clearTriggerQueues=function(){this.triggerQueues={up:[],down:[],left:[],right:[]}},i.prototype.flushTriggers=function(){for(var n in this.triggerQueues){var r=this.triggerQueues[n],i="up"===n||"left"===n;r.sort(i?e:t);for(var o=0,s=r.length;o<s;o+=1){var a=r[o];(a.options.continuous||o===r.length-1)&&a.trigger([n])}}this.clearTriggerQueues()},i.prototype.next=function(e){this.waypoints.sort(t);var n=r.Adapter.inArray(e,this.waypoints);return n===this.waypoints.length-1?null:this.waypoints[n+1]},i.prototype.previous=function(e){this.waypoints.sort(t);var n=r.Adapter.inArray(e,this.waypoints);return n?this.waypoints[n-1]:null},i.prototype.queueTrigger=function(t,e){this.triggerQueues[e].push(t)},i.prototype.remove=function(t){var e=r.Adapter.inArray(t,this.waypoints);e>-1&&this.waypoints.splice(e,1)},i.prototype.first=function(){return this.waypoints[0]},i.prototype.last=function(){return this.waypoints[this.waypoints.length-1]},i.findOrCreate=function(t){return n[t.axis][t.name]||new i(t)},r.Group=i}(),function(){"use strict";var t=window.jQuery,e=window.Waypoint;function n(e){this.$element=t(e)}t.each(["innerHeight","innerWidth","off","offset","on","outerHeight","outerWidth","scrollLeft","scrollTop"],(function(t,e){n.prototype[e]=function(){var t=Array.prototype.slice.call(arguments);return this.$element[e].apply(this.$element,t)}})),t.each(["extend","inArray","isEmptyObject"],(function(e,r){n[r]=t[r]})),e.adapters.push({name:"jquery",Adapter:n}),e.Adapter=n}(),function(){"use strict";var t=window.Waypoint;function e(e){return function(){var n=[],r=arguments[0];return e.isFunction(arguments[0])&&((r=e.extend({},arguments[1])).handler=arguments[0]),this.each((function(){var i=e.extend({},r,{element:this});"string"==typeof i.context&&(i.context=e(this).closest(i.context)[0]),n.push(new t(i))})),n}}window.jQuery&&(window.jQuery.fn.waypoint=e(window.jQuery)),window.Zepto&&(window.Zepto.fn.waypoint=e(window.Zepto))}()},77:function(t,e,n){var r=function(){return this||"object"==typeof self&&self}()||Function("return this")(),i=r.regeneratorRuntime&&Object.getOwnPropertyNames(r).indexOf("regeneratorRuntime")>=0,o=i&&r.regeneratorRuntime;if(r.regeneratorRuntime=void 0,t.exports=n(78),i)r.regeneratorRuntime=o;else try{delete r.regeneratorRuntime}catch(t){r.regeneratorRuntime=void 0}},78:function(t,e){!function(e){"use strict";var n=Object.prototype,r=n.hasOwnProperty,i="function"==typeof Symbol?Symbol:{},o=i.iterator||"@@iterator",s=i.asyncIterator||"@@asyncIterator",a=i.toStringTag||"@@toStringTag",l="object"==typeof t,c=e.regeneratorRuntime;if(c)l&&(t.exports=c);else{(c=e.regeneratorRuntime=l?t.exports:{}).wrap=g;var u={},f={};f[o]=function(){return this};var d=Object.getPrototypeOf,h=d&&d(d(A([])));h&&h!==n&&r.call(h,o)&&(f=h);var p=m.prototype=y.prototype=Object.create(f);w.prototype=p.constructor=m,m.constructor=w,m[a]=w.displayName="GeneratorFunction",c.isGeneratorFunction=function(t){var e="function"==typeof t&&t.constructor;return!!e&&(e===w||"GeneratorFunction"===(e.displayName||e.name))},c.mark=function(t){return Object.setPrototypeOf?Object.setPrototypeOf(t,m):(t.__proto__=m,a in t||(t[a]="GeneratorFunction")),t.prototype=Object.create(p),t},c.awrap=function(t){return{__await:t}},b(x.prototype),x.prototype[s]=function(){return this},c.AsyncIterator=x,c.async=function(t,e,n,r){var i=new x(g(t,e,n,r));return c.isGeneratorFunction(e)?i:i.next().then((function(t){return t.done?t.value:i.next()}))},b(p),p[a]="Generator",p[o]=function(){return this},p.toString=function(){return"[object Generator]"},c.keys=function(t){var e=[];for(var n in t)e.push(n);return e.reverse(),function n(){for(;e.length;){var r=e.pop();if(r in t)return n.value=r,n.done=!1,n}return n.done=!0,n}},c.values=A,j.prototype={constructor:j,reset:function(t){if(this.prev=0,this.next=0,this.sent=this._sent=void 0,this.done=!1,this.delegate=null,this.method="next",this.arg=void 0,this.tryEntries.forEach(S),!t)for(var e in this)"t"===e.charAt(0)&&r.call(this,e)&&!isNaN(+e.slice(1))&&(this[e]=void 0)},stop:function(){this.done=!0;var t=this.tryEntries[0].completion;if("throw"===t.type)throw t.arg;return this.rval},dispatchException:function(t){if(this.done)throw t;var e=this;function n(n,r){return s.type="throw",s.arg=t,e.next=n,r&&(e.method="next",e.arg=void 0),!!r}for(var i=this.tryEntries.length-1;i>=0;--i){var o=this.tryEntries[i],s=o.completion;if("root"===o.tryLoc)return n("end");if(o.tryLoc<=this.prev){var a=r.call(o,"catchLoc"),l=r.call(o,"finallyLoc");if(a&&l){if(this.prev<o.catchLoc)return n(o.catchLoc,!0);if(this.prev<o.finallyLoc)return n(o.finallyLoc)}else if(a){if(this.prev<o.catchLoc)return n(o.catchLoc,!0)}else{if(!l)throw new Error("try statement without catch or finally");if(this.prev<o.finallyLoc)return n(o.finallyLoc)}}}},abrupt:function(t,e){for(var n=this.tryEntries.length-1;n>=0;--n){var i=this.tryEntries[n];if(i.tryLoc<=this.prev&&r.call(i,"finallyLoc")&&this.prev<i.finallyLoc){var o=i;break}}o&&("break"===t||"continue"===t)&&o.tryLoc<=e&&e<=o.finallyLoc&&(o=null);var s=o?o.completion:{};return s.type=t,s.arg=e,o?(this.method="next",this.next=o.finallyLoc,u):this.complete(s)},complete:function(t,e){if("throw"===t.type)throw t.arg;return"break"===t.type||"continue"===t.type?this.next=t.arg:"return"===t.type?(this.rval=this.arg=t.arg,this.method="return",this.next="end"):"normal"===t.type&&e&&(this.next=e),u},finish:function(t){for(var e=this.tryEntries.length-1;e>=0;--e){var n=this.tryEntries[e];if(n.finallyLoc===t)return this.complete(n.completion,n.afterLoc),S(n),u}},catch:function(t){for(var e=this.tryEntries.length-1;e>=0;--e){var n=this.tryEntries[e];if(n.tryLoc===t){var r=n.completion;if("throw"===r.type){var i=r.arg;S(n)}return i}}throw new Error("illegal catch attempt")},delegateYield:function(t,e,n){return this.delegate={iterator:A(t),resultName:e,nextLoc:n},"next"===this.method&&(this.arg=void 0),u}}}function g(t,e,n,r){var i=e&&e.prototype instanceof y?e:y,o=Object.create(i.prototype),s=new j(r||[]);return o._invoke=function(t,e,n){var r="suspendedStart";return function(i,o){if("executing"===r)throw new Error("Generator is already running");if("completed"===r){if("throw"===i)throw o;return T()}for(n.method=i,n.arg=o;;){var s=n.delegate;if(s){var a=$(s,n);if(a){if(a===u)continue;return a}}if("next"===n.method)n.sent=n._sent=n.arg;else if("throw"===n.method){if("suspendedStart"===r)throw r="completed",n.arg;n.dispatchException(n.arg)}else"return"===n.method&&n.abrupt("return",n.arg);r="executing";var l=v(t,e,n);if("normal"===l.type){if(r=n.done?"completed":"suspendedYield",l.arg===u)continue;return{value:l.arg,done:n.done}}"throw"===l.type&&(r="completed",n.method="throw",n.arg=l.arg)}}}(t,n,s),o}function v(t,e,n){try{return{type:"normal",arg:t.call(e,n)}}catch(t){return{type:"throw",arg:t}}}function y(){}function w(){}function m(){}function b(t){["next","throw","return"].forEach((function(e){t[e]=function(t){return this._invoke(e,t)}}))}function x(t){var e;this._invoke=function(n,i){function o(){return new Promise((function(e,o){!function e(n,i,o,s){var a=v(t[n],t,i);if("throw"!==a.type){var l=a.arg,c=l.value;return c&&"object"==typeof c&&r.call(c,"__await")?Promise.resolve(c.__await).then((function(t){e("next",t,o,s)}),(function(t){e("throw",t,o,s)})):Promise.resolve(c).then((function(t){l.value=t,o(l)}),(function(t){return e("throw",t,o,s)}))}s(a.arg)}(n,i,e,o)}))}return e=e?e.then(o,o):o()}}function $(t,e){var n=t.iterator[e.method];if(void 0===n){if(e.delegate=null,"throw"===e.method){if(t.iterator.return&&(e.method="return",e.arg=void 0,$(t,e),"throw"===e.method))return u;e.method="throw",e.arg=new TypeError("The iterator does not provide a 'throw' method")}return u}var r=v(n,t.iterator,e.arg);if("throw"===r.type)return e.method="throw",e.arg=r.arg,e.delegate=null,u;var i=r.arg;return i?i.done?(e[t.resultName]=i.value,e.next=t.nextLoc,"return"!==e.method&&(e.method="next",e.arg=void 0),e.delegate=null,u):i:(e.method="throw",e.arg=new TypeError("iterator result is not an object"),e.delegate=null,u)}function k(t){var e={tryLoc:t[0]};1 in t&&(e.catchLoc=t[1]),2 in t&&(e.finallyLoc=t[2],e.afterLoc=t[3]),this.tryEntries.push(e)}function S(t){var e=t.completion||{};e.type="normal",delete e.arg,t.completion=e}function j(t){this.tryEntries=[{tryLoc:"root"}],t.forEach(k,this),this.reset(!0)}function A(t){if(t){var e=t[o];if(e)return e.call(t);if("function"==typeof t.next)return t;if(!isNaN(t.length)){var n=-1,i=function e(){for(;++n<t.length;)if(r.call(t,n))return e.value=t[n],e.done=!1,e;return e.value=void 0,e.done=!0,e};return i.next=i}}return{next:T}}function T(){return{value:void 0,done:!0}}}(function(){return this||"object"==typeof self&&self}()||Function("return this")())}})}));
//# sourceMappingURL=revision.dd65883f0aa1ec02e65d.js.map