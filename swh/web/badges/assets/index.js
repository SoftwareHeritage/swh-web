/**
 * Copyright (C) 2019-2025  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import ClipboardJS from 'clipboard';

import './badges.css';

export function showBadgeInfoModal(objectType, objectSWHID) {
  let badgeImageUrl;
  let badgeLinkUrl;
  let objectCoreSWHID = objectSWHID;
  if (objectType === 'origin') {
    badgeImageUrl = Urls.swh_badge(objectType, objectSWHID);
    badgeLinkUrl = `${Urls.browse_origin()}?origin_url=${objectSWHID}`;
  } else {
    const pos = objectSWHID.indexOf(';');
    if (pos !== -1) {
      objectCoreSWHID = objectSWHID.slice(0, pos);
      badgeImageUrl = Urls.swh_badge_swhid(objectCoreSWHID);
      $('.swhid').each((i, swhid) => {
        if (swhid.id === objectCoreSWHID) {
          badgeLinkUrl = swhid.pathname;
        }
      });
    } else {
      badgeImageUrl = Urls.swh_badge_swhid(objectSWHID);
      badgeLinkUrl = Urls.browse_swhid(objectSWHID);
    }
  }
  const absoluteBadgeImageUrl = `${window.location.origin}${badgeImageUrl}`;
  const absoluteBadgeLinkUrl = `${window.location.origin}${badgeLinkUrl}`;
  const html = `
  <a href="${absoluteBadgeLinkUrl}">
    <img class="swh-badge" src="${absoluteBadgeImageUrl}" alt="Archived | ${objectSWHID}"/>
  </a>
  <ul class="nav nav-tabs">
    <li class="nav-item">
      <a class="nav-link active" data-bs-toggle="tab" href="#swh-badge-html">HTML</a>
    </li>
    <li class="nav-item">
      <a class="nav-link" data-bs-toggle="tab" href="#swh-badge-markdown">Markdown</a>
    </li>
    <li class="nav-item">
      <a class="nav-link" data-bs-toggle="tab" href="#swh-badge-rst">reStructuredText</a>
    </li>
  </ul>
  <div class="tab-content swh-badges-integrations">
    <div class="tab-pane active" id="swh-badge-html">
      <pre><code class="swh-badge-html html">&lt;a href="${absoluteBadgeLinkUrl}"&gt;
  &lt;img src="${absoluteBadgeImageUrl}" alt="Archived | ${objectCoreSWHID}"/&gt;
&lt;/a&gt;</code></pre>
    </div>
    <div class="tab-pane" id="swh-badge-markdown">
      <pre><code class="swh-badge-md markdown">[![SWH](${absoluteBadgeImageUrl})](${absoluteBadgeLinkUrl})</code></pre>
    </div>
    <div class="tab-pane" id="swh-badge-rst">
      <pre class="swh-badge-rst">.. image:: ${absoluteBadgeImageUrl}
   :target: ${absoluteBadgeLinkUrl}</pre>
    </div>
    <button type="button"
            class="btn btn-secondary btn-sm btn-swh-copy-badge-code float-end"
            title="Copy badge code to clipboard">
      <i class="mdi mdi-content-copy mdi-fw" aria-hidden="true"></i>Copy badge code
    </button>
  </div>`;
  swh.webapp.showModalHtml('Software Heritage badge integration', html);
  swh.webapp.highlightCode(false, '.swh-badge-html');
  swh.webapp.highlightCode(false, '.swh-badge-md');
  new ClipboardJS('.btn-swh-copy-badge-code', {
    text: () => {
      return $('.swh-badges-integrations .tab-pane.active pre').text();
    },
    container: document.getElementById('swh-web-modal-html')
  }).on('success', function(e) {
    swh.webapp.toggleButtonText(e.trigger, 'Copied!');
    e.clearSelection();
  });
}
