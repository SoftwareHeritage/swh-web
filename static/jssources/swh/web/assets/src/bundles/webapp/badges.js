/**
 * Copyright (C) 2019  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

export function showBadgeInfoModal(objectType, objectPid) {
  let badgeImageUrl;
  let badgeLinkUrl;
  if (objectType === 'origin') {
    badgeImageUrl = Urls.swh_badge(objectType, objectPid);
    badgeLinkUrl = Urls.browse_origin(objectPid);
  } else {
    badgeImageUrl = Urls.swh_badge_pid(objectPid);
    badgeLinkUrl = Urls.browse_swh_id(objectPid);
  }
  let urlPrefix = `${window.location.protocol}//${window.location.hostname}`;
  if (window.location.port) {
    urlPrefix += `:${window.location.port}`;
  }
  const absoluteBadgeImageUrl = `${urlPrefix}${badgeImageUrl}`;
  const absoluteBadgeLinkUrl = `${urlPrefix}${badgeLinkUrl}`;
  const html = `
  <a href="${absoluteBadgeLinkUrl}">
    <img class="swh-badge" src="${absoluteBadgeImageUrl}">
  </a>
  <div>
    <label>HTML</label>
    <pre class="swh-badge-html">&lt;a href="${absoluteBadgeLinkUrl}"&gt;
    &lt;img src="${absoluteBadgeImageUrl}"&gt;
&lt;/a&gt;</pre>
  </div>
  <div>
    <label>Markdown</label>
    <pre class="swh-badge-md">[![SWH](${absoluteBadgeImageUrl})](${absoluteBadgeLinkUrl})</pre>
  </div>
  <div>
    <label>reStructuredText</label>
    <pre class="swh-badge-rst">.. image:: ${absoluteBadgeImageUrl}
    :target: ${absoluteBadgeLinkUrl}</pre>
  </div>`;
  swh.webapp.showModalHtml('Software Heritage badge integration', html);
}
