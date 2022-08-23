/**
 * Copyright (C) 2021-2022  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

export function showIframeInfoModal(objectType, objectSWHID) {
  const html = `
    <p>
      You can embed that ${objectType} view in an external website
      through the use of an iframe. Use the following HTML code
      to do so.
    </p>
    <pre><code class="swh-iframe-html html">&lt;iframe style="width: 100%; height: 500px; border: 1px solid rgba(0, 0, 0, 0.125);"
        src="${window.location.origin}${Urls.browse_swhid_iframe(objectSWHID.replaceAll('\n', ''))}"&gt;
&lt;/iframe&gt;</code></pre>
    <iframe style="width: 100%; height: 500px; border: 1px solid rgba(0, 0, 0, 0.125);"
            src="${window.location.origin}${Urls.browse_swhid_iframe(objectSWHID.replaceAll('\n', ''))}">
    </iframe>`;
  swh.webapp.showModalHtml(`Software Heritage ${objectType} iframe`, html, '1000px');
  swh.webapp.highlightCode(false, '.swh-iframe-html');
}
