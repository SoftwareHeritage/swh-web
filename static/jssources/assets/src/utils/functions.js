/**
 * Copyright (C) 2018-2020  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

// utility functions

import Cookies from 'js-cookie';

export function handleFetchError(response) {
  if (!response.ok) {
    throw response;
  }
  return response;
}

export function handleFetchErrors(responses) {
  for (let i = 0; i < responses.length; ++i) {
    if (!responses[i].ok) {
      throw responses[i];
    }
  }
  return responses;
}

export function staticAsset(asset) {
  return `${__STATIC__}${asset}`;
}

export function csrfPost(url, headers = {}, body = null) {
  headers['X-CSRFToken'] = Cookies.get('csrftoken');
  return fetch(url, {
    credentials: 'include',
    headers: headers,
    method: 'POST',
    body: body
  });
}

export function isGitRepoUrl(url, pathPrefix = '/') {
  const allowedProtocols = ['http:', 'https:', 'git:'];
  if (allowedProtocols.find(protocol => protocol === url.protocol) === undefined) {
    return false;
  }
  if (!url.pathname.startsWith(pathPrefix)) {
    return false;
  }
  const re = new RegExp('[\\w\\.-]+\\/?(?!=.git)(?:\\.git\\/?)?$');
  return re.test(url.pathname.slice(pathPrefix.length));
};

export function removeUrlFragment() {
  history.replaceState('', document.title, window.location.pathname + window.location.search);
}

export function selectText(startNode, endNode) {
  const selection = window.getSelection();
  selection.removeAllRanges();
  const range = document.createRange();
  range.setStart(startNode, 0);
  if (endNode.nodeName !== '#text') {
    range.setEnd(endNode, endNode.childNodes.length);
  } else {
    range.setEnd(endNode, endNode.textContent.length);
  }
  selection.addRange(range);
}

export function htmlAlert(type, message, closable = false) {
  let closeButton = '';
  let extraClasses = '';
  if (closable) {
    closeButton =
      `<button type="button" class="close" data-dismiss="alert" aria-label="Close">
        <span aria-hidden="true">&times;</span>
      </button>`;
    extraClasses = 'alert-dismissible';
  }
  return `<div class="alert alert-${type} ${extraClasses}" role="alert">${message}${closeButton}</div>`;
}

export function isValidURL(string) {
  try {
    new URL(string);
  } catch (_) {
    return false;
  }
  return true;
}

export async function isArchivedOrigin(originPath) {
  if (!isValidURL(originPath)) {
    // Not a valid URL, return immediately
    return false;
  } else {
    const response = await fetch(Urls.api_1_origin(originPath));
    return response.ok && response.status === 200; // Success response represents an archived origin
  }
}

export async function getCanonicalOriginURL(originUrl) {
  let originUrlLower = originUrl.toLowerCase();
  // github.com URL processing
  const ghUrlRegex = /^http[s]*:\/\/github.com\//;
  if (originUrlLower.match(ghUrlRegex)) {
    // remove trailing .git
    if (originUrlLower.endsWith('.git')) {
      originUrlLower = originUrlLower.slice(0, -4);
    }
    // remove trailing slash
    if (originUrlLower.endsWith('/')) {
      originUrlLower = originUrlLower.slice(0, -1);
    }
    // extract {owner}/{repo}
    const ownerRepo = originUrlLower.replace(ghUrlRegex, '');
    // fetch canonical URL from github Web API
    const ghApiResponse = await fetch(`https://api.github.com/repos/${ownerRepo}`);
    if (ghApiResponse.ok && ghApiResponse.status === 200) {
      const ghApiResponseData = await ghApiResponse.json();
      return ghApiResponseData.html_url;
    }
  }
  return originUrl;
}
