!function(e,n){"object"==typeof exports&&"object"==typeof module?module.exports=n():"function"==typeof define&&define.amd?define([],n):"object"==typeof exports?exports.swh=n():(e.swh=e.swh||{},e.swh.badges=n())}(self,(function(){return function(){var e={d:function(n,t){for(var o in t)e.o(t,o)&&!e.o(n,o)&&Object.defineProperty(n,o,{enumerable:!0,get:t[o]})}};e.g=function(){if("object"==typeof globalThis)return globalThis;try{return this||new Function("return this")()}catch(e){if("object"==typeof window)return window}}(),e.o=function(e,n){return Object.prototype.hasOwnProperty.call(e,n)},e.r=function(e){"undefined"!=typeof Symbol&&Symbol.toStringTag&&Object.defineProperty(e,Symbol.toStringTag,{value:"Module"}),Object.defineProperty(e,"__esModule",{value:!0})};var n,t={};return(n="undefined"!=typeof window?window:void 0!==e.g?e.g:"undefined"!=typeof self?self:{}).SENTRY_RELEASE={id:"0.2.20"},n.SENTRY_RELEASES=n.SENTRY_RELEASES||{},n.SENTRY_RELEASES["swh-webapp@swh"]={id:"0.2.20"},function(){"use strict";function n(e,n){var t,o,i=n;if("origin"===e)t=Urls.swh_badge(e,n),o=Urls.browse_origin()+"?origin_url="+n;else{var r=n.indexOf(";");-1!==r?(i=n.slice(0,r),t=Urls.swh_badge_swhid(i),$(".swhid").each((function(e,n){n.id===i&&(o=n.pathname)}))):(t=Urls.swh_badge_swhid(n),o=Urls.browse_swhid(n))}var d=""+window.location.origin+t,a=""+window.location.origin+o,s='\n  <a href="'+a+'">\n    <img class="swh-badge" src="'+d+'" alt="Archived | '+n+'"/>\n  </a>\n  <div>\n    <label>HTML</label>\n    <pre><code class="swh-badge-html html">&lt;a href="'+a+'"&gt;\n    &lt;img src="'+d+'" alt="Archived | '+i+'"/&gt;\n&lt;/a&gt;</code></pre>\n  </div>\n  <div>\n    <label>Markdown</label>\n    <pre><code class="swh-badge-md markdown">[![SWH]('+d+")]("+a+')</code></pre>\n  </div>\n  <div>\n    <label>reStructuredText</label>\n    <pre class="swh-badge-rst">.. image:: '+d+"\n    :target: "+a+"</pre>\n  </div>";swh.webapp.showModalHtml("Software Heritage badge integration",s),swh.webapp.highlightCode(!1,".swh-badge-html"),swh.webapp.highlightCode(!1,".swh-badge-md")}e.r(t),e.d(t,{showBadgeInfoModal:function(){return n}})}(),t}()}));
//# sourceMappingURL=badges.593dfd559f821d46d02c.js.map