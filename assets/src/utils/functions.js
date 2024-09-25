/**
 * Copyright (C) 2018-2022  The Software Heritage developers
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

export function errorMessageFromResponse(errorData, defaultMessage) {
  let errorMessage = '';
  try {
    const reason = JSON.parse(errorData['reason']);
    Object.entries(reason).forEach((keys, _) => {
      const key = keys[0];
      const message = keys[1][0]; // take only the first issue
      errorMessage += `\n${key}: ${message}`;
    });
  } catch (_) {
    errorMessage = errorData['reason']; // can't parse it, leave it raw
  }
  return errorMessage ? `Error: ${errorMessage}` : defaultMessage;
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
      `<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>`;
    extraClasses = 'alert-dismissible';
  }
  return `<div class="alert alert-${type} ${extraClasses}" role="alert">${message}${closeButton}</div>`;
}

export function validateUrl(url, allowedProtocols = []) {
  let originUrl = null;
  let validUrl = true;

  try {
    originUrl = new URL(url);
  } catch (TypeError) {
    validUrl = false;
  }

  if (validUrl && allowedProtocols.length) {
    validUrl = (
      allowedProtocols.find(protocol => protocol === originUrl.protocol) !== undefined
    );
  }

  return validUrl ? originUrl : null;
}

export async function isArchivedOrigin(originPath, visitType) {
  if (!validateUrl(originPath)) {
    // Not a valid URL, return immediately
    return false;
  } else {
    const response = await fetch(Urls.api_1_origin(originPath));
    if (!response.ok || response.status !== 200) {
      return false;
    } else {
      const originData = await response.json();
      return !visitType || visitType === 'any' || originData.visit_types.includes(visitType);
    }
  }
}

async function getCanonicalGithubOriginURL(ownerRepo) {
  const ghApiResponse = await fetch(`https://api.github.com/repos/${ownerRepo}`);
  if (ghApiResponse.ok && ghApiResponse.status === 200) {
    const ghApiResponseData = await ghApiResponse.json();
    return ghApiResponseData.html_url;
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
    const url = await getCanonicalGithubOriginURL(ownerRepo);
    if (url) {
      return url;
    }
  }

  const ghpagesUrlRegex = /^http[s]*:\/\/(?<owner>[^/]+).github.io\/(?<repo>[^/]+)\/?.*/;
  const parsedUrl = originUrlLower.match(ghpagesUrlRegex);
  if (parsedUrl) {
    const ownerRepo = `${parsedUrl.groups.owner}/${parsedUrl.groups.repo}`;
    // fetch canonical URL from github Web API
    const url = await getCanonicalGithubOriginURL(ownerRepo);
    if (url) {
      return url;
    }
  }

  return originUrl;
}

export function getHumanReadableDate(data) {
  // Display iso format date string into a human readable date
  // This is expected to be used by date field in datatable listing views
  // Example: 3/24/2022, 10:31:08 AM
  const date = new Date(data);
  return date.toLocaleString();
}

export function genLink(sanitizedUrl, type, openInNewTab = false, linkText = '') {
  // Display link. It's up to the caller to sanitize sanitizedUrl first.
  if (type === 'display' && sanitizedUrl) {
    const encodedSanitizedUrl = encodeURI(sanitizedUrl);
    if (!linkText) {
      linkText = encodedSanitizedUrl;
    }
    let attrs = '';
    if (openInNewTab) {
      attrs = 'target="_blank" rel="noopener noreferrer"';
    }
    return `<a href="${encodedSanitizedUrl}" ${attrs}>${linkText}</a>`;
  }
  return sanitizedUrl;
}
