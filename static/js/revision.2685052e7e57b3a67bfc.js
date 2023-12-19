/*! For license information please see revision.2685052e7e57b3a67bfc.js.LICENSE.txt */
!function(){try{var e="undefined"!=typeof window?window:"undefined"!=typeof global?global:"undefined"!=typeof self?self:{},t=(new Error).stack;t&&(e._sentryDebugIds=e._sentryDebugIds||{},e._sentryDebugIds[t]="ee0b0292-a8fd-46d0-812a-ab1185211a40",e._sentryDebugIdIdentifier="sentry-dbid-ee0b0292-a8fd-46d0-812a-ab1185211a40")}catch(e){}}();var _global="undefined"!=typeof window?window:"undefined"!=typeof global?global:"undefined"!=typeof self?self:{};_global.SENTRY_RELEASE={id:"0.3.1"},function(e,t){"object"==typeof exports&&"object"==typeof module?module.exports=t():"function"==typeof define&&define.amd?define([],t):"object"==typeof exports?exports.swh=t():(e.swh=e.swh||{},e.swh.revision=t())}(self,(function(){return function(){var __webpack_modules__={86515:function(e,t,n){"use strict";n.d(t,{XC:function(){return r}});var r=(0,n(59537).TT)("img/swh-spinner.gif")},59537:function(e,t,n){"use strict";n.d(t,{L3:function(){return i},TT:function(){return r}});n(64687),n(31955);function r(e){return"/static/"+e}function i(){history.replaceState("",document.title,window.location.pathname+window.location.search)}},48299:function(e,t,n){"use strict";n.d(t,{D_:function(){return M},EV:function(){return F},Mo:function(){return N},OU:function(){return E},S0:function(){return P},St:function(){return G},n2:function(){return I},qo:function(){return Z},sr:function(){return q}});var r,i=n(15861),o=n(64687),a=n.n(o),s=(n(43511),n(86515)),l=n(59537),c=n(46322),u=n.n(c),f=null,d=0,p=0,h='<span class="no-nl-marker" style="color: red;" title="No newline at end of file"><i class="mdi mdi-rotate-90 mdi-cancel" aria-hidden="true"><i class="mdi mdi-keyboard-return" aria-hidden="true"></span>',_=0,w=0,g={},y={},m=null,v=null,b={},x=null,k="#fdf3da",S="#swh-revision-changes",j="Files";function T(e){var t=$(e).offset().top,n=t+$(e).outerHeight(),r=$(window).scrollTop(),i=r+$(window).height();return n>r&&t<i}function E(e,t,n){for(var r=b[e],i=A(t),o=A(n),a="",s=0;s<r-i.length;++s)a+=" ";a+=i,a+="  ";for(var l=0;l<r-o.length;++l)a+=" ";return a+=o}function C(e){var t,n;if(e.startsWith("@@")){var r=new RegExp(/^@@ -(\d+),(\d+) \+(\d+),(\d+) @@$/gm),i=new RegExp(/^@@ -(\d+) \+(\d+),(\d+) @@$/gm),o=new RegExp(/^@@ -(\d+),(\d+) \+(\d+) @@$/gm),a=new RegExp(/^@@ -(\d+) \+(\d+) @@$/gm),s=r.exec(e),l=i.exec(e),c=o.exec(e),u=a.exec(e);s?(t=parseInt(s[1])-1,n=parseInt(s[3])-1):l?(t=parseInt(l[1])-1,n=parseInt(l[2])-1):c?(t=parseInt(c[1])-1,n=parseInt(c[3])-1):u&&(t=parseInt(u[1])-1,n=parseInt(u[2])-1)}return void 0!==t?[t,n]:null}function L(e){return e?parseInt(e):0}function A(e){return e?e.toString():""}function q(e,t,n){var r;if(t||n){var i=L(e.trim());t?r=[i,0]:n&&(r=[0,i])}else(r=e.replace(/[ ]+/g," ").split(" ")).length>2&&r.shift(),r=r.map((function(e){return L(e)}));return r}function P(e,t,n){var r="";return r+="F"+(e[0]||0),r+="T"+(e[1]||0),r+="-F"+(t[0]||0),r+="T"+(t[1]||0),r+=n?"-unified":"-split"}function F(e){var t=/F([0-9]+)T([0-9]+)-F([0-9]+)T([0-9]+)-([a-z]+)/.exec(e);return 6===t.length?{startLines:[parseInt(t[1]),parseInt(t[2])],endLines:[parseInt(t[3]),parseInt(t[4])],unified:"unified"===t[5]}:null}function O(e,t){var n=$("#"+e+' .hljs-ln-line[data-line-number="'+t+'"]'),r=$("#"+e+' .hljs-ln-numbers[data-line-number="'+t+'"]');return r.css("color","black"),r.css("font-weight","bold"),n.css("background-color",k),n.css("mix-blend-mode","multiply"),n}function D(e){void 0===e&&(e=!0),e&&(x=null,m=null,v=null),$(".hljs-ln-line[data-line-number]").css("background-color","initial"),$(".hljs-ln-line[data-line-number]").css("mix-blend-mode","initial"),$(".hljs-ln-numbers[data-line-number]").css("color","#aaa"),$(".hljs-ln-numbers[data-line-number]").css("font-weight","initial"),"Changes"===j&&window.location.hash!==S&&window.history.replaceState("",document.title,window.location.pathname+window.location.search+S)}function R(e,t,n,r){var i;if(r){var o=E(e,t[0],t[1]),a=E(e,n[0],n[1]),s=$("#"+e+' .hljs-ln-line[data-line-number="'+o+'"]'),l=$("#"+e+' .hljs-ln-line[data-line-number="'+a+'"]');if($(l).position().top<$(s).position().top){var c=[a,o];o=c[0],a=c[1],i=l}else i=s;for(var u=O(e,o),f=$(u).closest("tr"),d=$(f).children(".hljs-ln-line").data("line-number").toString();d!==a;)d.trim()&&O(e,d),f=$(f).next(),d=$(f).children(".hljs-ln-line").data("line-number").toString();O(e,a)}else if(t[0]&&n[0]){for(var p=Math.min(t[0],n[0]),h=Math.max(t[0],n[0]),_=p;_<=h;++_)O(e+"-from",_);i=$("#"+e+'-from .hljs-ln-line[data-line-number="'+p+'"]')}else if(t[1]&&n[1]){for(var w=Math.min(t[1],n[1]),g=Math.max(t[1],n[1]),y=w;y<=g;++y)O(e+"-to",y);i=$("#"+e+'-to .hljs-ln-line[data-line-number="'+w+'"]')}else{var m,v;t[0]&&n[1]?(m=t[0],v=n[1]):(m=n[0],v=t[1]);var b=$("#"+e+'-from .hljs-ln-line[data-line-number="'+m+'"]'),x=$("#"+e+'-to .hljs-ln-line[data-line-number="'+v+'"]'),k=$(b).position().top<$(x).position().top;i=k?b:x;for(var S=$("#"+e+"-from tr").first(),j=$(S).children(".hljs-ln-line").data("line-number"),T=$("#"+e+"-to tr").first(),C=$(T).children(".hljs-ln-line").data("line-number"),L=!1;k&&j===m?L=!0:k||C!==v||(L=!0),L&&j&&O(e+"-from",j),L&&C&&O(e+"-to",C),!(k&&C===v||!k&&j===m);)S=$(S).next(),j=$(S).children(".hljs-ln-line").data("line-number"),T=$(T).next(),C=$(T).children(".hljs-ln-line").data("line-number")}var A=P(t,n,r);return window.location.hash="diff_"+e+"+"+A,i}function I(e){$("#"+e+"-split-diff").css("display","none"),$("#"+e+"-unified-diff").css("display","block")}function N(e){$("#"+e+"-unified-diff").css("display","none"),$("#"+e+"-split-diff").css("display","block")}function M(e,t){return W.apply(this,arguments)}function W(){return(W=(0,i.Z)(a().mark((function e(t,n){var i,o,s,l,c,u,d,y,m,v,x,k,S;return a().wrap((function(e){for(;;)switch(e.prev=e.next){case 0:if(i=function(e,t){$(e).attr("data-line-number",t||""),$(e).children().attr("data-line-number",t||""),$(e).siblings().attr("data-line-number",t||"")},-1!==t.indexOf("force=true")||!g.hasOwnProperty(n)){e.next=4;break}return e.abrupt("return");case 4:return g[n]=!0,$("#"+n+"-loading").css("visibility","visible"),$("#"+n+"-loading").css("display","block"),$("#"+n+"-highlightjs").css("display","none"),e.next=10,fetch(t);case 10:return o=e.sent,e.next=13,o.json();case 13:s=e.sent,++p===f.length&&$("#swh-compute-all-diffs").addClass("active"),0===s.diff_str.indexOf("Large diff")?($("#"+n)[0].innerHTML=s.diff_str+'<br/><button class="btn btn-default btn-sm" type="button"\n           onclick="swh.revision.computeDiff(\''+t+"&force=true', '"+n+"')\">Request diff</button>",H(n)):0!==s.diff_str.indexOf("@@")?($("#"+n).text(s.diff_str),H(n)):($("."+n).removeClass("plaintext"),$("."+n).addClass(s.language),$("#"+n).text(s.diff_str),$("#"+n).each((function(e,t){hljs.highlightElement(t),hljs.lineNumbersElementSync(t)})),l="",c="",u=[],d=[],y=[],m=0,v="",x="",k=0,$("#"+n+" .hljs-ln-numbers").each((function(e,t){var n=t.nextSibling.innerText,r=C(n),i="",o="";if(r)l=r[0],c=r[1],k=0,v+=n+"\n",x+=n+"\n",d.push(""),y.push("");else if(n.length>0&&"-"===n[0])i=(l+=1).toString(),d.push(i),++w,v+=n+"\n",++k;else if(n.length>0&&"+"===n[0])o=(c+=1).toString(),y.push(o),++_,x+=n+"\n",--k;else{c+=1,i=(l+=1).toString(),o=c.toString();for(var a=0;a<Math.abs(k);++a)k>0?(x+="\n",y.push("")):(v+="\n",d.push(""));k=0,v+=n+"\n",x+=n+"\n",y.push(o),d.push(i)}l||(i=""),c||(o=""),u[e]=[i,o],m=Math.max(m,i.length),m=Math.max(m,o.length)})),b[n]=m,$("#"+n+"-from").text(v),$("#"+n+"-to").text(x),$("#"+n+"-from, #"+n+"-to").each((function(e,t){hljs.highlightElement(t),hljs.lineNumbersElementSync(t)})),$("."+n+" .hljs-ln-numbers").each((function(e,t){var n=t.nextSibling.innerText;if(n.startsWith("@@")){$(t).parent().addClass("swh-diff-lines-info");var r=$(t).parent().find(".hljs-ln-code .hljs-ln-line").text();$(t).parent().find(".hljs-ln-code .hljs-ln-line").children().remove(),$(t).parent().find(".hljs-ln-code .hljs-ln-line").text(""),$(t).parent().find(".hljs-ln-code .hljs-ln-line").append('<span class="hljs-meta">'+r+"</span>")}else n.length>0&&"-"===n[0]?$(t).parent().addClass("swh-diff-removed-line"):n.length>0&&"+"===n[0]&&$(t).parent().addClass("swh-diff-added-line")})),$("#"+n+" .hljs-ln-numbers").each((function(e,t){var r=E(n,u[e][0],u[e][1]);i(t,r)})),$("#"+n+"-from .hljs-ln-numbers").each((function(e,t){i(t,d[e])})),$("#"+n+"-to .hljs-ln-numbers").each((function(e,t){i(t,y[e])})),$("."+n+" .hljs-ln-code").each((function(e,t){if(t.firstChild){if("#text"!==t.firstChild.nodeName){var n=t.firstChild.innerHTML;if("-"===n[0]||"+"===n[0]){t.firstChild.innerHTML=n.substr(1);var r=document.createTextNode(n[0]);$(t).prepend(r)}}$(t).contents().filter((function(e,t){return 3===t.nodeType})).each((function(e,n){var r="[swh-no-nl-marker]";-1!==n.textContent.indexOf(r)&&(n.textContent=n.textContent.replace(r,""),$(t).append($(h)))}))}})),0!==s.diff_str.indexOf("Diffs are not generated for non textual content")&&$("#diff_"+n+" .diff-styles").css("visibility","visible"),H(n),r&&-1!==r.diffPanelId.indexOf(n)&&(r.unified||N(n),S=R(n,r.startLines,r.endLines,r.unified),$("html, body").animate({scrollTop:S.offset().top-50},{duration:500})));case 17:case"end":return e.stop()}}),e)})))).apply(this,arguments)}function H(e){$("#"+e+"-loading").css("display","none"),$("#"+e+"-highlightjs").css("display","block"),$("#swh-revision-lines-added").text(_+" additions"),$("#swh-revision-lines-deleted").text(w+" deletions"),$("#swh-nb-diffs-computed").text(p),Waypoint.refreshAll()}function z(){$(".swh-file-diff-panel").each((function(e,t){if(T(t)){var n=t.id.replace("diff_","");M(y[n],n)}}))}function U(e){var t=e.path;return"rename"===e.type&&(t=e.from_path+" &rarr; "+e.to_path),u()({diffData:e,diffPanelTitle:t,swhSpinnerSrc:s.XC})}function B(){for(var e=0;e<f.length;++e){var t=f[e];$("#diff_"+t.id).waypoint({handler:function(){if(T(this.element)){var e=this.element.id.replace("diff_","");M(y[e],e),this.destroy()}},offset:"100%"}),$("#diff_"+t.id).waypoint({handler:function(){if(T(this.element)){var e=this.element.id.replace("diff_","");M(y[e],e),this.destroy()}},offset:function(){return-$(this.element).height()}})}Waypoint.refreshAll()}function Q(e,t){void 0===t&&(t=!0),Waypoint.disableAll(),$("html, body").animate({scrollTop:$(e).offset().top},{duration:500,complete:function(){t&&(window.location.hash=e),Waypoint.enableAll(),z()}})}function G(e){for(var t in $(e.currentTarget).addClass("active"),y)y.hasOwnProperty(t)&&M(y[t],t);e.stopPropagation()}function Z(e,t){return K.apply(this,arguments)}function K(){return K=(0,i.Z)(a().mark((function e(t,o){return a().wrap((function(e){for(;;)switch(e.prev=e.next){case 0:return e.next=2,n.e(399).then(n.bind(n,68480));case 2:$(document).on("shown.bs.tab",'a[data-toggle="tab"]',function(){var e=(0,i.Z)(a().mark((function e(t){var n,i,s,c,u;return a().wrap((function(e){for(;;)switch(e.prev=e.next){case 0:if("Changes"!==(j=t.currentTarget.text.trim())){e.next=30;break}if(window.location.hash=S,$("#readme-panel").css("display","none"),!f){e.next=6;break}return e.abrupt("return");case 6:return e.next=8,fetch(o);case 8:return n=e.sent,e.next=11,n.json();case 11:for(i=e.sent,f=i.changes,d=i.total_nb_changes,s=d+" changed file",1!==d&&(s+="s"),$("#swh-revision-changed-files").text(s),$("#swh-total-nb-diffs").text(f.length),$("#swh-revision-changes-list pre")[0].innerHTML=i.changes_msg,$("#swh-revision-changes-loading").css("display","none"),$("#swh-revision-changes-list pre").css("display","block"),$("#swh-compute-all-diffs").css("visibility","visible"),$("#swh-revision-changes-list").removeClass("in"),d>f.length&&($("#swh-too-large-revision-diff").css("display","block"),$("#swh-nb-loaded-diffs").text(f.length)),c=0;c<f.length;++c)u=f[c],y[u.id]=u.diff_url,$("#swh-revision-diffs").append(U(u));B(),z(),r&&Q(r.diffPanelId,!1),e.next=31;break;case 30:"Files"===j&&((0,l.L3)(),$("#readme-panel").css("display","block"));case 31:case"end":return e.stop()}}),e)})));return function(t){return e.apply(this,arguments)}}()),$(document).ready((function(){t.length>0?$("#swh-revision-message").addClass("in"):$("#swh-collapse-revision-message").attr("data-toggle",""),$('#swh-revision-changes-list a[href^="#"], #back-to-top a[href^="#"]').click((function(e){return Q($.attr(e.currentTarget,"href")),!1})),$("body").click((function(e){if("Changes"===j)if(e.target.classList.contains("hljs-ln-n")){var t=$(e.target).closest("code").prop("id"),n=-1!==t.indexOf("-from"),r=-1!==t.indexOf("-to"),i=$(e.target).data("line-number").toString(),o=t.replace("-from","").replace("-to","");e.shiftKey&&o===x&&i.trim()||(D(),x=o),o===x&&i.trim()&&(e.shiftKey?m&&(D(!1),v=q(i,n,r),R(o,m,v,!n&&!r)):R(o,m=q(i,n,r),m,!n&&!r))}else D()}));var e=window.location.hash;if(e){var n=e.split("+");2===n.length&&(r=F(n[1]))&&(r.diffPanelId=n[0],$('.nav-tabs a[href="'+S+'"]').tab("show")),e===S&&$('.nav-tabs a[href="'+S+'"]').tab("show")}}));case 4:case"end":return e.stop()}}),e)}))),K.apply(this,arguments)}},3637:function(e,t,n){"use strict";function r(e){var t=new URLSearchParams(window.location.search);$(e.target).val()?t.set("revs_ordering",$(e.target).val()):t.has("revs_ordering")&&t.delete("revs_ordering"),window.location.search=t.toString()}function i(){$(document).ready((function(){var e=new URLSearchParams(window.location.search).get("revs_ordering");e&&$(':input[value="'+e+'"]').prop("checked",!0)}))}n.d(t,{i:function(){return r},o:function(){return i}})},46322:function(module){module.exports=function anonymous(locals,escapeFn,include,rethrow){escapeFn=escapeFn||function(e){return null==e?"":String(e).replace(_MATCH_HTML,encode_char)};var _ENCODE_HTML_RULES={"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&#34;","'":"&#39;"},_MATCH_HTML=/[&<>'"]/g;function encode_char(e){return _ENCODE_HTML_RULES[e]||e}var __output="";function __append(e){null!=e&&(__output+=e)}with(locals||{})__append('\n<div id="diff_'),__append(escapeFn(diffData.id)),__append('" class="card swh-file-diff-panel">\n  <div class="card-header swh-background-gray border-bottom-0">\n    <a data-toggle="collapse" href="#diff_'),__append(escapeFn(diffData.id)),__append('_content">\n      <div class="float-left swh-title-color">\n        <strong>'),__append(escapeFn(diffPanelTitle)),__append('</strong>\n      </div>\n    </a>\n    <div class="ml-auto float-right">\n      <div class="btn-group btn-group-toggle diff-styles" data-toggle="buttons" style="visibility: hidden;">\n        <label class="btn btn-default btn-sm form-check-label active unified-diff-button" onclick="swh.revision.showUnifiedDiff(\''),__append(escapeFn(diffData.id)),__append('\')">\n          <input type="radio" name="diffs-switch" id="unified" autocomplete="off" checked="checked"> Unified\n        </label>\n        <label class="btn btn-default btn-sm form-check-label split-diff-button" onclick="swh.revision.showSplitDiff(\''),__append(escapeFn(diffData.id)),__append('\')">\n          <input type="radio" name="diffs-switch" id="side-by-side" autocomplete="off"> Side-by-side\n        </label>\n      </div>\n      <a href="'),__append(escapeFn(diffData.content_url)),__append('" class="btn btn-default btn-sm" role="button">View file</a>\n    </div>\n    <div class="clearfix"></div>\n  </div>\n  <div id="diff_'),__append(escapeFn(diffData.id)),__append('_content" class="collapse show">\n    <div class="swh-diff-loading text-center" id="'),__append(escapeFn(diffData.id)),__append('-loading" style="visibility: hidden;">\n      <img src="'),__append(escapeFn(swhSpinnerSrc)),__append('">\n      <p>Loading diff ...</p>\n    </div>\n    <div class="highlightjs swh-content" style="display: none;" id="'),__append(escapeFn(diffData.id)),__append('-highlightjs">\n      <div id="'),__append(escapeFn(diffData.id)),__append('-unified-diff">\n        <pre><code class="'),__append(escapeFn(diffData.id)),__append('" id="'),__append(escapeFn(diffData.id)),__append('"></code></pre>\n      </div>\n      <div style="width: 100%; display: none;" id="'),__append(escapeFn(diffData.id)),__append('-split-diff">\n        <pre class="float-left" style="width: 50%;"><code class="'),__append(escapeFn(diffData.id)),__append('" id="'),__append(escapeFn(diffData.id)),__append('-from"></code></pre>\n        <pre style="width: 50%;"><code class="'),__append(escapeFn(diffData.id)),__append('" id="'),__append(escapeFn(diffData.id)),__append('-to"></code></pre>\n      </div>\n    </div>\n  </div>\n</div>');return __output}},43511:function(){!function(){"use strict";var e=0,t={};function n(r){if(!r)throw new Error("No options passed to Waypoint constructor");if(!r.element)throw new Error("No element option passed to Waypoint constructor");if(!r.handler)throw new Error("No handler option passed to Waypoint constructor");this.key="waypoint-"+e,this.options=n.Adapter.extend({},n.defaults,r),this.element=this.options.element,this.adapter=new n.Adapter(this.element),this.callback=r.handler,this.axis=this.options.horizontal?"horizontal":"vertical",this.enabled=this.options.enabled,this.triggerPoint=null,this.group=n.Group.findOrCreate({name:this.options.group,axis:this.axis}),this.context=n.Context.findOrCreateByElement(this.options.context),n.offsetAliases[this.options.offset]&&(this.options.offset=n.offsetAliases[this.options.offset]),this.group.add(this),this.context.add(this),t[this.key]=this,e+=1}n.prototype.queueTrigger=function(e){this.group.queueTrigger(this,e)},n.prototype.trigger=function(e){this.enabled&&this.callback&&this.callback.apply(this,e)},n.prototype.destroy=function(){this.context.remove(this),this.group.remove(this),delete t[this.key]},n.prototype.disable=function(){return this.enabled=!1,this},n.prototype.enable=function(){return this.context.refresh(),this.enabled=!0,this},n.prototype.next=function(){return this.group.next(this)},n.prototype.previous=function(){return this.group.previous(this)},n.invokeAll=function(e){var n=[];for(var r in t)n.push(t[r]);for(var i=0,o=n.length;i<o;i++)n[i][e]()},n.destroyAll=function(){n.invokeAll("destroy")},n.disableAll=function(){n.invokeAll("disable")},n.enableAll=function(){for(var e in n.Context.refreshAll(),t)t[e].enabled=!0;return this},n.refreshAll=function(){n.Context.refreshAll()},n.viewportHeight=function(){return window.innerHeight||document.documentElement.clientHeight},n.viewportWidth=function(){return document.documentElement.clientWidth},n.adapters=[],n.defaults={context:window,continuous:!0,enabled:!0,group:"default",horizontal:!1,offset:0},n.offsetAliases={"bottom-in-view":function(){return this.context.innerHeight()-this.adapter.outerHeight()},"right-in-view":function(){return this.context.innerWidth()-this.adapter.outerWidth()}},window.Waypoint=n}(),function(){"use strict";function e(e){window.setTimeout(e,1e3/60)}var t=0,n={},r=window.Waypoint,i=window.onload;function o(e){this.element=e,this.Adapter=r.Adapter,this.adapter=new this.Adapter(e),this.key="waypoint-context-"+t,this.didScroll=!1,this.didResize=!1,this.oldScroll={x:this.adapter.scrollLeft(),y:this.adapter.scrollTop()},this.waypoints={vertical:{},horizontal:{}},e.waypointContextKey=this.key,n[e.waypointContextKey]=this,t+=1,r.windowContext||(r.windowContext=!0,r.windowContext=new o(window)),this.createThrottledScrollHandler(),this.createThrottledResizeHandler()}o.prototype.add=function(e){var t=e.options.horizontal?"horizontal":"vertical";this.waypoints[t][e.key]=e,this.refresh()},o.prototype.checkEmpty=function(){var e=this.Adapter.isEmptyObject(this.waypoints.horizontal),t=this.Adapter.isEmptyObject(this.waypoints.vertical),r=this.element==this.element.window;e&&t&&!r&&(this.adapter.off(".waypoints"),delete n[this.key])},o.prototype.createThrottledResizeHandler=function(){var e=this;function t(){e.handleResize(),e.didResize=!1}this.adapter.on("resize.waypoints",(function(){e.didResize||(e.didResize=!0,r.requestAnimationFrame(t))}))},o.prototype.createThrottledScrollHandler=function(){var e=this;function t(){e.handleScroll(),e.didScroll=!1}this.adapter.on("scroll.waypoints",(function(){e.didScroll&&!r.isTouch||(e.didScroll=!0,r.requestAnimationFrame(t))}))},o.prototype.handleResize=function(){r.Context.refreshAll()},o.prototype.handleScroll=function(){var e={},t={horizontal:{newScroll:this.adapter.scrollLeft(),oldScroll:this.oldScroll.x,forward:"right",backward:"left"},vertical:{newScroll:this.adapter.scrollTop(),oldScroll:this.oldScroll.y,forward:"down",backward:"up"}};for(var n in t){var r=t[n],i=r.newScroll>r.oldScroll?r.forward:r.backward;for(var o in this.waypoints[n]){var a=this.waypoints[n][o];if(null!==a.triggerPoint){var s=r.oldScroll<a.triggerPoint,l=r.newScroll>=a.triggerPoint;(s&&l||!s&&!l)&&(a.queueTrigger(i),e[a.group.id]=a.group)}}}for(var c in e)e[c].flushTriggers();this.oldScroll={x:t.horizontal.newScroll,y:t.vertical.newScroll}},o.prototype.innerHeight=function(){return this.element==this.element.window?r.viewportHeight():this.adapter.innerHeight()},o.prototype.remove=function(e){delete this.waypoints[e.axis][e.key],this.checkEmpty()},o.prototype.innerWidth=function(){return this.element==this.element.window?r.viewportWidth():this.adapter.innerWidth()},o.prototype.destroy=function(){var e=[];for(var t in this.waypoints)for(var n in this.waypoints[t])e.push(this.waypoints[t][n]);for(var r=0,i=e.length;r<i;r++)e[r].destroy()},o.prototype.refresh=function(){var e,t=this.element==this.element.window,n=t?void 0:this.adapter.offset(),i={};for(var o in this.handleScroll(),e={horizontal:{contextOffset:t?0:n.left,contextScroll:t?0:this.oldScroll.x,contextDimension:this.innerWidth(),oldScroll:this.oldScroll.x,forward:"right",backward:"left",offsetProp:"left"},vertical:{contextOffset:t?0:n.top,contextScroll:t?0:this.oldScroll.y,contextDimension:this.innerHeight(),oldScroll:this.oldScroll.y,forward:"down",backward:"up",offsetProp:"top"}}){var a=e[o];for(var s in this.waypoints[o]){var l,c,u,f,d=this.waypoints[o][s],p=d.options.offset,h=d.triggerPoint,_=0,w=null==h;d.element!==d.element.window&&(_=d.adapter.offset()[a.offsetProp]),"function"==typeof p?p=p.apply(d):"string"==typeof p&&(p=parseFloat(p),d.options.offset.indexOf("%")>-1&&(p=Math.ceil(a.contextDimension*p/100))),l=a.contextScroll-a.contextOffset,d.triggerPoint=Math.floor(_+l-p),c=h<a.oldScroll,u=d.triggerPoint>=a.oldScroll,f=!c&&!u,!w&&(c&&u)?(d.queueTrigger(a.backward),i[d.group.id]=d.group):(!w&&f||w&&a.oldScroll>=d.triggerPoint)&&(d.queueTrigger(a.forward),i[d.group.id]=d.group)}}return r.requestAnimationFrame((function(){for(var e in i)i[e].flushTriggers()})),this},o.findOrCreateByElement=function(e){return o.findByElement(e)||new o(e)},o.refreshAll=function(){for(var e in n)n[e].refresh()},o.findByElement=function(e){return n[e.waypointContextKey]},window.onload=function(){i&&i(),o.refreshAll()},r.requestAnimationFrame=function(t){(window.requestAnimationFrame||window.mozRequestAnimationFrame||window.webkitRequestAnimationFrame||e).call(window,t)},r.Context=o}(),function(){"use strict";function e(e,t){return e.triggerPoint-t.triggerPoint}function t(e,t){return t.triggerPoint-e.triggerPoint}var n={vertical:{},horizontal:{}},r=window.Waypoint;function i(e){this.name=e.name,this.axis=e.axis,this.id=this.name+"-"+this.axis,this.waypoints=[],this.clearTriggerQueues(),n[this.axis][this.name]=this}i.prototype.add=function(e){this.waypoints.push(e)},i.prototype.clearTriggerQueues=function(){this.triggerQueues={up:[],down:[],left:[],right:[]}},i.prototype.flushTriggers=function(){for(var n in this.triggerQueues){var r=this.triggerQueues[n],i="up"===n||"left"===n;r.sort(i?t:e);for(var o=0,a=r.length;o<a;o+=1){var s=r[o];(s.options.continuous||o===r.length-1)&&s.trigger([n])}}this.clearTriggerQueues()},i.prototype.next=function(t){this.waypoints.sort(e);var n=r.Adapter.inArray(t,this.waypoints);return n===this.waypoints.length-1?null:this.waypoints[n+1]},i.prototype.previous=function(t){this.waypoints.sort(e);var n=r.Adapter.inArray(t,this.waypoints);return n?this.waypoints[n-1]:null},i.prototype.queueTrigger=function(e,t){this.triggerQueues[t].push(e)},i.prototype.remove=function(e){var t=r.Adapter.inArray(e,this.waypoints);t>-1&&this.waypoints.splice(t,1)},i.prototype.first=function(){return this.waypoints[0]},i.prototype.last=function(){return this.waypoints[this.waypoints.length-1]},i.findOrCreate=function(e){return n[e.axis][e.name]||new i(e)},r.Group=i}(),function(){"use strict";var e=window.jQuery,t=window.Waypoint;function n(t){this.$element=e(t)}e.each(["innerHeight","innerWidth","off","offset","on","outerHeight","outerWidth","scrollLeft","scrollTop"],(function(e,t){n.prototype[t]=function(){var e=Array.prototype.slice.call(arguments);return this.$element[t].apply(this.$element,e)}})),e.each(["extend","inArray","isEmptyObject"],(function(t,r){n[r]=e[r]})),t.adapters.push({name:"jquery",Adapter:n}),t.Adapter=n}(),function(){"use strict";var e=window.Waypoint;function t(t){return function(){var n=[],r=arguments[0];return t.isFunction(arguments[0])&&((r=t.extend({},arguments[1])).handler=arguments[0]),this.each((function(){var i=t.extend({},r,{element:this});"string"==typeof i.context&&(i.context=t(this).closest(i.context)[0]),n.push(new e(i))})),n}}window.jQuery&&(window.jQuery.fn.waypoint=t(window.jQuery)),window.Zepto&&(window.Zepto.fn.waypoint=t(window.Zepto))}()},17061:function(e,t,n){var r=n(18698).default;function i(){"use strict";e.exports=i=function(){return n},e.exports.__esModule=!0,e.exports.default=e.exports;var t,n={},o=Object.prototype,a=o.hasOwnProperty,s=Object.defineProperty||function(e,t,n){e[t]=n.value},l="function"==typeof Symbol?Symbol:{},c=l.iterator||"@@iterator",u=l.asyncIterator||"@@asyncIterator",f=l.toStringTag||"@@toStringTag";function d(e,t,n){return Object.defineProperty(e,t,{value:n,enumerable:!0,configurable:!0,writable:!0}),e[t]}try{d({},"")}catch(t){d=function(e,t,n){return e[t]=n}}function p(e,t,n,r){var i=t&&t.prototype instanceof v?t:v,o=Object.create(i.prototype),a=new P(r||[]);return s(o,"_invoke",{value:C(e,n,a)}),o}function h(e,t,n){try{return{type:"normal",arg:e.call(t,n)}}catch(e){return{type:"throw",arg:e}}}n.wrap=p;var _="suspendedStart",w="suspendedYield",g="executing",y="completed",m={};function v(){}function b(){}function x(){}var k={};d(k,c,(function(){return this}));var $=Object.getPrototypeOf,S=$&&$($(F([])));S&&S!==o&&a.call(S,c)&&(k=S);var j=x.prototype=v.prototype=Object.create(k);function T(e){["next","throw","return"].forEach((function(t){d(e,t,(function(e){return this._invoke(t,e)}))}))}function E(e,t){function n(i,o,s,l){var c=h(e[i],e,o);if("throw"!==c.type){var u=c.arg,f=u.value;return f&&"object"==r(f)&&a.call(f,"__await")?t.resolve(f.__await).then((function(e){n("next",e,s,l)}),(function(e){n("throw",e,s,l)})):t.resolve(f).then((function(e){u.value=e,s(u)}),(function(e){return n("throw",e,s,l)}))}l(c.arg)}var i;s(this,"_invoke",{value:function(e,r){function o(){return new t((function(t,i){n(e,r,t,i)}))}return i=i?i.then(o,o):o()}})}function C(e,n,r){var i=_;return function(o,a){if(i===g)throw new Error("Generator is already running");if(i===y){if("throw"===o)throw a;return{value:t,done:!0}}for(r.method=o,r.arg=a;;){var s=r.delegate;if(s){var l=L(s,r);if(l){if(l===m)continue;return l}}if("next"===r.method)r.sent=r._sent=r.arg;else if("throw"===r.method){if(i===_)throw i=y,r.arg;r.dispatchException(r.arg)}else"return"===r.method&&r.abrupt("return",r.arg);i=g;var c=h(e,n,r);if("normal"===c.type){if(i=r.done?y:w,c.arg===m)continue;return{value:c.arg,done:r.done}}"throw"===c.type&&(i=y,r.method="throw",r.arg=c.arg)}}}function L(e,n){var r=n.method,i=e.iterator[r];if(i===t)return n.delegate=null,"throw"===r&&e.iterator.return&&(n.method="return",n.arg=t,L(e,n),"throw"===n.method)||"return"!==r&&(n.method="throw",n.arg=new TypeError("The iterator does not provide a '"+r+"' method")),m;var o=h(i,e.iterator,n.arg);if("throw"===o.type)return n.method="throw",n.arg=o.arg,n.delegate=null,m;var a=o.arg;return a?a.done?(n[e.resultName]=a.value,n.next=e.nextLoc,"return"!==n.method&&(n.method="next",n.arg=t),n.delegate=null,m):a:(n.method="throw",n.arg=new TypeError("iterator result is not an object"),n.delegate=null,m)}function A(e){var t={tryLoc:e[0]};1 in e&&(t.catchLoc=e[1]),2 in e&&(t.finallyLoc=e[2],t.afterLoc=e[3]),this.tryEntries.push(t)}function q(e){var t=e.completion||{};t.type="normal",delete t.arg,e.completion=t}function P(e){this.tryEntries=[{tryLoc:"root"}],e.forEach(A,this),this.reset(!0)}function F(e){if(e||""===e){var n=e[c];if(n)return n.call(e);if("function"==typeof e.next)return e;if(!isNaN(e.length)){var i=-1,o=function n(){for(;++i<e.length;)if(a.call(e,i))return n.value=e[i],n.done=!1,n;return n.value=t,n.done=!0,n};return o.next=o}}throw new TypeError(r(e)+" is not iterable")}return b.prototype=x,s(j,"constructor",{value:x,configurable:!0}),s(x,"constructor",{value:b,configurable:!0}),b.displayName=d(x,f,"GeneratorFunction"),n.isGeneratorFunction=function(e){var t="function"==typeof e&&e.constructor;return!!t&&(t===b||"GeneratorFunction"===(t.displayName||t.name))},n.mark=function(e){return Object.setPrototypeOf?Object.setPrototypeOf(e,x):(e.__proto__=x,d(e,f,"GeneratorFunction")),e.prototype=Object.create(j),e},n.awrap=function(e){return{__await:e}},T(E.prototype),d(E.prototype,u,(function(){return this})),n.AsyncIterator=E,n.async=function(e,t,r,i,o){void 0===o&&(o=Promise);var a=new E(p(e,t,r,i),o);return n.isGeneratorFunction(t)?a:a.next().then((function(e){return e.done?e.value:a.next()}))},T(j),d(j,f,"Generator"),d(j,c,(function(){return this})),d(j,"toString",(function(){return"[object Generator]"})),n.keys=function(e){var t=Object(e),n=[];for(var r in t)n.push(r);return n.reverse(),function e(){for(;n.length;){var r=n.pop();if(r in t)return e.value=r,e.done=!1,e}return e.done=!0,e}},n.values=F,P.prototype={constructor:P,reset:function(e){if(this.prev=0,this.next=0,this.sent=this._sent=t,this.done=!1,this.delegate=null,this.method="next",this.arg=t,this.tryEntries.forEach(q),!e)for(var n in this)"t"===n.charAt(0)&&a.call(this,n)&&!isNaN(+n.slice(1))&&(this[n]=t)},stop:function(){this.done=!0;var e=this.tryEntries[0].completion;if("throw"===e.type)throw e.arg;return this.rval},dispatchException:function(e){if(this.done)throw e;var n=this;function r(r,i){return s.type="throw",s.arg=e,n.next=r,i&&(n.method="next",n.arg=t),!!i}for(var i=this.tryEntries.length-1;i>=0;--i){var o=this.tryEntries[i],s=o.completion;if("root"===o.tryLoc)return r("end");if(o.tryLoc<=this.prev){var l=a.call(o,"catchLoc"),c=a.call(o,"finallyLoc");if(l&&c){if(this.prev<o.catchLoc)return r(o.catchLoc,!0);if(this.prev<o.finallyLoc)return r(o.finallyLoc)}else if(l){if(this.prev<o.catchLoc)return r(o.catchLoc,!0)}else{if(!c)throw new Error("try statement without catch or finally");if(this.prev<o.finallyLoc)return r(o.finallyLoc)}}}},abrupt:function(e,t){for(var n=this.tryEntries.length-1;n>=0;--n){var r=this.tryEntries[n];if(r.tryLoc<=this.prev&&a.call(r,"finallyLoc")&&this.prev<r.finallyLoc){var i=r;break}}i&&("break"===e||"continue"===e)&&i.tryLoc<=t&&t<=i.finallyLoc&&(i=null);var o=i?i.completion:{};return o.type=e,o.arg=t,i?(this.method="next",this.next=i.finallyLoc,m):this.complete(o)},complete:function(e,t){if("throw"===e.type)throw e.arg;return"break"===e.type||"continue"===e.type?this.next=e.arg:"return"===e.type?(this.rval=this.arg=e.arg,this.method="return",this.next="end"):"normal"===e.type&&t&&(this.next=t),m},finish:function(e){for(var t=this.tryEntries.length-1;t>=0;--t){var n=this.tryEntries[t];if(n.finallyLoc===e)return this.complete(n.completion,n.afterLoc),q(n),m}},catch:function(e){for(var t=this.tryEntries.length-1;t>=0;--t){var n=this.tryEntries[t];if(n.tryLoc===e){var r=n.completion;if("throw"===r.type){var i=r.arg;q(n)}return i}}throw new Error("illegal catch attempt")},delegateYield:function(e,n,r){return this.delegate={iterator:F(e),resultName:n,nextLoc:r},"next"===this.method&&(this.arg=t),m}},n}e.exports=i,e.exports.__esModule=!0,e.exports.default=e.exports},18698:function(e){function t(n){return e.exports=t="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(e){return typeof e}:function(e){return e&&"function"==typeof Symbol&&e.constructor===Symbol&&e!==Symbol.prototype?"symbol":typeof e},e.exports.__esModule=!0,e.exports.default=e.exports,t(n)}e.exports=t,e.exports.__esModule=!0,e.exports.default=e.exports},64687:function(e,t,n){var r=n(17061)();e.exports=r;try{regeneratorRuntime=r}catch(e){"object"==typeof globalThis?globalThis.regeneratorRuntime=r:Function("r","regeneratorRuntime = r")(r)}},15861:function(e,t,n){"use strict";function r(e,t,n,r,i,o,a){try{var s=e[o](a),l=s.value}catch(e){return void n(e)}s.done?t(l):Promise.resolve(l).then(r,i)}function i(e){return function(){var t=this,n=arguments;return new Promise((function(i,o){var a=e.apply(t,n);function s(e){r(a,i,o,s,l,"next",e)}function l(e){r(a,i,o,s,l,"throw",e)}s(void 0)}))}}n.d(t,{Z:function(){return i}})},31955:function(e,t,n){"use strict";function r(e){for(var t=1;t<arguments.length;t++){var n=arguments[t];for(var r in n)e[r]=n[r]}return e}(function e(t,n){function i(e,i,o){if("undefined"!=typeof document){"number"==typeof(o=r({},n,o)).expires&&(o.expires=new Date(Date.now()+864e5*o.expires)),o.expires&&(o.expires=o.expires.toUTCString()),e=encodeURIComponent(e).replace(/%(2[346B]|5E|60|7C)/g,decodeURIComponent).replace(/[()]/g,escape);var a="";for(var s in o)o[s]&&(a+="; "+s,!0!==o[s]&&(a+="="+o[s].split(";")[0]));return document.cookie=e+"="+t.write(i,e)+a}}return Object.create({set:i,get:function(e){if("undefined"!=typeof document&&(!arguments.length||e)){for(var n=document.cookie?document.cookie.split("; "):[],r={},i=0;i<n.length;i++){var o=n[i].split("="),a=o.slice(1).join("=");try{var s=decodeURIComponent(o[0]);if(r[s]=t.read(a,s),e===s)break}catch(e){}}return e?r[e]:r}},remove:function(e,t){i(e,"",r({},t,{expires:-1}))},withAttributes:function(t){return e(this.converter,r({},this.attributes,t))},withConverter:function(t){return e(r({},this.converter,t),this.attributes)}},{attributes:{value:Object.freeze(n)},converter:{value:Object.freeze(t)}})})({read:function(e){return'"'===e[0]&&(e=e.slice(1,-1)),e.replace(/(%[\dA-F]{2})+/gi,decodeURIComponent)},write:function(e){return encodeURIComponent(e).replace(/%(2[346BF]|3[AC-F]|40|5[BDE]|60|7[BCD])/g,decodeURIComponent)}},{path:"/"})}},__webpack_module_cache__={},inProgress,dataWebpackPrefix;function __webpack_require__(e){var t=__webpack_module_cache__[e];if(void 0!==t)return t.exports;var n=__webpack_module_cache__[e]={exports:{}};return __webpack_modules__[e].call(n.exports,n,n.exports,__webpack_require__),n.exports}__webpack_require__.m=__webpack_modules__,__webpack_require__.n=function(e){var t=e&&e.__esModule?function(){return e.default}:function(){return e};return __webpack_require__.d(t,{a:t}),t},__webpack_require__.d=function(e,t){for(var n in t)__webpack_require__.o(t,n)&&!__webpack_require__.o(e,n)&&Object.defineProperty(e,n,{enumerable:!0,get:t[n]})},__webpack_require__.f={},__webpack_require__.e=function(e){return Promise.all(Object.keys(__webpack_require__.f).reduce((function(t,n){return __webpack_require__.f[n](e,t),t}),[]))},__webpack_require__.u=function(e){return"js/highlightjs.0646e75a810eab53c100.js"},__webpack_require__.miniCssF=function(e){return"css/highlightjs.ed8cb52757e055b1a33b.css"},__webpack_require__.g=function(){if("object"==typeof globalThis)return globalThis;try{return this||new Function("return this")()}catch(e){if("object"==typeof window)return window}}(),__webpack_require__.o=function(e,t){return Object.prototype.hasOwnProperty.call(e,t)},inProgress={},dataWebpackPrefix="swh:",__webpack_require__.l=function(e,t,n,r){if(inProgress[e])inProgress[e].push(t);else{var i,o;if(void 0!==n)for(var a=document.getElementsByTagName("script"),s=0;s<a.length;s++){var l=a[s];if(l.getAttribute("src")==e||l.getAttribute("data-webpack")==dataWebpackPrefix+n){i=l;break}}i||(o=!0,(i=document.createElement("script")).charset="utf-8",i.timeout=120,__webpack_require__.nc&&i.setAttribute("nonce",__webpack_require__.nc),i.setAttribute("data-webpack",dataWebpackPrefix+n),i.src=e),inProgress[e]=[t];var c=function(t,n){i.onerror=i.onload=null,clearTimeout(u);var r=inProgress[e];if(delete inProgress[e],i.parentNode&&i.parentNode.removeChild(i),r&&r.forEach((function(e){return e(n)})),t)return t(n)},u=setTimeout(c.bind(null,void 0,{type:"timeout",target:i}),12e4);i.onerror=c.bind(null,i.onerror),i.onload=c.bind(null,i.onload),o&&document.head.appendChild(i)}},__webpack_require__.r=function(e){"undefined"!=typeof Symbol&&Symbol.toStringTag&&Object.defineProperty(e,Symbol.toStringTag,{value:"Module"}),Object.defineProperty(e,"__esModule",{value:!0})},__webpack_require__.p="/static/",function(){if("undefined"!=typeof document){var e=function(e){return new Promise((function(t,n){var r=__webpack_require__.miniCssF(e),i=__webpack_require__.p+r;if(function(e,t){for(var n=document.getElementsByTagName("link"),r=0;r<n.length;r++){var i=(a=n[r]).getAttribute("data-href")||a.getAttribute("href");if("stylesheet"===a.rel&&(i===e||i===t))return a}var o=document.getElementsByTagName("style");for(r=0;r<o.length;r++){var a;if((i=(a=o[r]).getAttribute("data-href"))===e||i===t)return a}}(r,i))return t();!function(e,t,n,r,i){var o=document.createElement("link");o.rel="stylesheet",o.type="text/css",o.onerror=o.onload=function(n){if(o.onerror=o.onload=null,"load"===n.type)r();else{var a=n&&("load"===n.type?"missing":n.type),s=n&&n.target&&n.target.href||t,l=new Error("Loading CSS chunk "+e+" failed.\n("+s+")");l.code="CSS_CHUNK_LOAD_FAILED",l.type=a,l.request=s,o.parentNode&&o.parentNode.removeChild(o),i(l)}},o.href=t,n?n.parentNode.insertBefore(o,n.nextSibling):document.head.appendChild(o)}(e,i,null,t,n)}))},t={679:0};__webpack_require__.f.miniCss=function(n,r){t[n]?r.push(t[n]):0!==t[n]&&{399:1}[n]&&r.push(t[n]=e(n).then((function(){t[n]=0}),(function(e){throw delete t[n],e})))}}}(),function(){var e={679:0};__webpack_require__.f.j=function(t,n){var r=__webpack_require__.o(e,t)?e[t]:void 0;if(0!==r)if(r)n.push(r[2]);else{var i=new Promise((function(n,i){r=e[t]=[n,i]}));n.push(r[2]=i);var o=__webpack_require__.p+__webpack_require__.u(t),a=new Error;__webpack_require__.l(o,(function(n){if(__webpack_require__.o(e,t)&&(0!==(r=e[t])&&(e[t]=void 0),r)){var i=n&&("load"===n.type?"missing":n.type),o=n&&n.target&&n.target.src;a.message="Loading chunk "+t+" failed.\n("+i+": "+o+")",a.name="ChunkLoadError",a.type=i,a.request=o,r[1](a)}}),"chunk-"+t,t)}};var t=function(t,n){var r,i,o=n[0],a=n[1],s=n[2],l=0;if(o.some((function(t){return 0!==e[t]}))){for(r in a)__webpack_require__.o(a,r)&&(__webpack_require__.m[r]=a[r]);if(s)s(__webpack_require__)}for(t&&t(n);l<o.length;l++)i=o[l],__webpack_require__.o(e,i)&&e[i]&&e[i][0](),e[i]=0},n=self.webpackChunkswh=self.webpackChunkswh||[];n.forEach(t.bind(null,0)),n.push=t.bind(null,n.push.bind(n))}();var __webpack_exports__={};return function(){"use strict";__webpack_require__.r(__webpack_exports__),__webpack_require__.d(__webpack_exports__,{computeAllDiffs:function(){return e.St},computeDiff:function(){return e.D_},formatDiffLineNumbers:function(){return e.OU},fragmentToSelectedDiffLines:function(){return e.EV},initRevisionDiff:function(){return e.qo},initRevisionsLog:function(){return t.o},parseDiffLineNumbers:function(){return e.sr},revsOrderingTypeClicked:function(){return t.i},selectedDiffLinesToFragment:function(){return e.S0},showSplitDiff:function(){return e.Mo},showUnifiedDiff:function(){return e.n2}});var e=__webpack_require__(48299),t=__webpack_require__(3637)}(),__webpack_exports__}()}));
//# sourceMappingURL=revision.2685052e7e57b3a67bfc.js.map