/**
 * Copyright (C) 2018-2026  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

// utility functions

import Cookies from 'js-cookie';

export function handleFetchError(response, noRaiseForStatuses = []) {
  if (!response.ok && $.inArray(response.status, noRaiseForStatuses)) {
    throw response;
  }
  return response;
}

export function handleFetchErrors(responses, noRaiseForStatuses = []) {
  for (let i = 0; i < responses.length; ++i) {
    if (!responses[i].ok && $.inArray(responses[i].status, noRaiseForStatuses)) {
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

export function staticAsset(asset, origin) {
  let url = `${__STATIC__}${asset}`;
  if (url.startsWith('/') && origin) {
    url = origin + url;
  }
  return url;
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
  return re.test(url.pathname.slice(pathPrefix.length)) || url.pathname === '/';
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

export function textToHTML(text) {
  const textArea = document.createElement('textarea');
  textArea.innerText = text;
  return textArea.innerHTML;
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
    let url = `${Urls.api_1_origin_visit_latest(originPath.replace('?', '%3F'))}?require_snapshot=true`;
    if (visitType && visitType !== 'any') {
      url += `&visit_type=${visitType}`;
    }
    const response = await fetch(url);
    return response.ok;
  }
}

async function getCanonicalGithubOriginURL(ownerRepo) {
  try {
    const ghApiResponse = await fetch(`https://api.github.com/repos/${ownerRepo}`);
    if (ghApiResponse.ok && ghApiResponse.status === 200) {
      const ghApiResponseData = await ghApiResponse.json();
      return ghApiResponseData.html_url;
    }
  } catch (_) {
    return null;
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

export function dtUpdateSettings(init) {
  const params = new URLSearchParams(window.location.search);

  if (init.urlParamPrefix) init.urlParamPrefix += '_';
  else init.urlParamPrefix = '';

  const getParam = (param) => params.get(`${init.urlParamPrefix}${param}`) ?? undefined;

  init.search = {search: getParam('search') ?? ''};

  const page = getParam('page');
  init.page = /^[1-9]\d*$/.test(page) ? page - 1 : 0;

  let length = Number(getParam('length'));
  length = init.lengthMenu.find((e) => e === length);
  if (length === undefined) length = init.lengthMenu[0];
  init.pageLength = length;

  init.displayStart = init.page * init.pageLength;

  const getOrderParams = (order, sortParam, dirParam) => {
    const sort = getParam(sortParam);
    if (sort !== undefined) {
      const column = init.columns.findIndex((c) => {
        return (c.urlParam ?? c.name) === sort && (c.orderable ?? true);
      });
      if (column >= 0) {
        let dir = getParam(dirParam);
        dir = ['asc', 'desc'].includes(dir) ? dir : 'asc';
        order.push([column, dir]);
        return true;
      }
    }
  };

  const order = [];
  const sort = getParam('sort');
  if (sort !== undefined) {
    getOrderParams(order, 'sort', 'dir');
  } else {
    let i = 1;
    while (true) {
      if (!getOrderParams(order, `sort_${i}`, `dir_${i}`)) {
        break;
      }
      i++;
    };
  }
  if (init.defaultOrder === undefined) {
    init.defaultOrder = init.order;
  }
  init.order = order.length ? order : init.defaultOrder;

  init.realInitComplete = init.initComplete ?? init.fnInitComplete;
  init.initComplete = function(settings, json) {
    init.realInitComplete?.(settings, json);
    dtAddEvents(this);
  };

  return init;
}

function dtAddEvents(dt) {
  dt.on('search.dt', dtSaveSearchParam);
  dt.on('page.dt', dtSavePageParam);
  dt.on('length.dt', dtSaveLengthParam);
  dt.on('order.dt', dtSaveSortingParams);
  $(window).on('popstate', dtLoadParams);
}

function dtRemoveEvents(dt) {
  dt.off('search.dt', dtSaveSearchParam);
  dt.off('page.dt', dtSavePageParam);
  dt.off('length.dt', dtSaveLengthParam);
  dt.off('order.dt', dtSaveSortingParams);
  $(window).off('popstate', dtLoadParams);
}

function dtSaveSearchParam(e, settings) {
  const url = new URL(window.location.href);
  dtUpdateParam(url, e, 'search', e.dt.search());
  dtUpdateParam(url, e, 'page', undefined);
  dtSaveParams(url);
}

function dtSavePageParam(e, settings) {
  const url = new URL(window.location.href);
  dtUpdateParam(url, e, 'page', e.dt.page() + 1);
  dtSaveParams(url);
}

function dtSaveLengthParam(e, settings, length) {
  const url = new URL(window.location.href);
  dtUpdateParam(url, e, 'length', length);
  dtUpdateParam(url, e, 'page', e.dt.page() + 1);
  dtSaveParams(url);
}

function dtUpdateParam(url, e, param, value) {
  const prefix = e.dt.init().urlParamPrefix;
  const par = `${prefix}${param}`;
  if (value === undefined) {
    url.searchParams.delete(par);
  } else {
    url.searchParams.set(par, value);
  }
}

function dtSaveParams(url) {
  if (window.location.href !== url.href) {
    history.pushState(undefined, '', url.href);
  }
}

function dtSaveSortingParams(e, settings, ordersObj) {
  const orders = e.dt.order();
  const columns = e.dt.init().columns;
  const prefix = e.dt.init().urlParamPrefix;
  const sortPrefix = `${prefix}sort`;
  const dirPrefix = `${prefix}dir`;
  const sortPrefix_ = `${sortPrefix}_`;
  const dirPrefix_ = `${dirPrefix}_`;
  const url = new URL(window.location.href);

  // Remove existing order parameters
  url.searchParams.delete(sortPrefix);
  url.searchParams.delete(dirPrefix);
  Array.from(url.searchParams.keys())
  .filter((k) => k.startsWith(sortPrefix_) || k.startsWith(dirPrefix_))
  .forEach((k) => url.searchParams.delete(k));

  // Add new order parameters
  const short = orders.length === 1;
  orders.forEach(([col, dir], i) => {
    const column = columns[col];
    if (column !== undefined) {
      const sort = column.urlParam ?? column.name;
      if (sort !== undefined) {
        const sortParam = short ? sortPrefix : `${sortPrefix_}${i + 1}`;
        const dirParam = short ? dirPrefix : `${dirPrefix_}${i + 1}`;
        url.searchParams.set(sortParam, sort);
        url.searchParams.set(dirParam, dir);
      }
    }
  });

  // Reordering resets the current page
  dtUpdateParam(url, e, 'page', undefined);

  // Save the new URL with updated parameters
  dtSaveParams(url);
}

function dtLoadParams(e) {
  $(':focus').blur(); // Otherwise old values are retained
  $.fn.dataTable.tables({api: true}).iterator('table', function(table, i) {
    dtRemoveEvents(this);
    const init = dtUpdateSettings({...this.init()});
    this.search(init.search.search);
    this.page(init.page);
    this.page.len(init.pageLength);
    this.draw('full-hold');
    dtAddEvents(this);
  });
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
