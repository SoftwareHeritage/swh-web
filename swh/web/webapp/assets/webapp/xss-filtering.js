/**
 * Copyright (C) 2019-2025  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import * as parseCssUrls from 'css-url-parser';
import DOMPurify from 'dompurify';
import * as EmailValidator from 'email-validator';
import {resolve} from 'pathifist';

function stripQueryParameters(path) {
  let processedPath = path;
  if (!processedPath.startsWith('/')) {
    processedPath = '/' + processedPath;
  }
  const url = new URL(window.location.origin + processedPath);
  if (url.search) {
    path = path.replace(url.search, '');
  }
  return path;
}

function computeAssetUrl(relativePath, swhObjectMetadata) {
  let path = stripQueryParameters(relativePath);
  if (path.startsWith('/')) {
    path = path.slice(1);
  }
  let baseUrl;
  // used internal endpoint as file url to possibly get the raw data
  // from the archive content
  if (swhObjectMetadata.path) {
    baseUrl = Urls.browse_directory_get_content_at_path(
      swhObjectMetadata.root_directory, swhObjectMetadata.path.slice(1, -1));
  } else {
    baseUrl = Urls.browse_directory_get_content_at_path(
      swhObjectMetadata.root_directory, '').slice(0, -1);
  }
  const url = new URL(path, window.location.origin + baseUrl + '/');
  return url.toString();
}

function canSkipUrlProcessing(url) {
  return url.startsWith('data:image') ||
    url.startsWith('http:') ||
    url.startsWith('https:') ||
    url.startsWith('www') ||
    url.startsWith('#');
}

// we register a hook when performing XSS filtering in order to
// possibly replace a relative file url with the one for getting
// the file from the archive content
DOMPurify.addHook('uponSanitizeAttribute', function(node, data) {
  // get currently browsed swh object metadata
  const swhObjectMetadata = swh.webapp.getBrowsedSwhObjectMetadata();

  // process image and CSS links
  if ((node.nodeName === 'IMG' && data.attrName === 'src') ||
      (node.nodeName === 'LINK' && data.attrName === 'href')) {

    // file url does not need any processing here
    if (canSkipUrlProcessing(data.attrValue)) {
      return;
    }

    // the swh object is provided without any useful context
    // to get contents from the archive
    if (!swhObjectMetadata.hasOwnProperty('root_directory')) {
      return;
    }

    // update attribute with archive URL
    data.attrValue = computeAssetUrl(data.attrValue, swhObjectMetadata);

  } else if ((node.nodeName === 'IMG' && data.attrName === 'srcset') ||
             (node.nodeName === 'SOURCE' && data.attrName === 'srcset')) {
    // the swh object is provided without any useful context
    // to get contents from the archive
    if (!swhObjectMetadata.hasOwnProperty('root_directory')) {
      return;
    }

    const srcSetSplit = data.attrValue.split(',');
    for (const srcSet of srcSetSplit) {
      const url = srcSet.split(' ')[0];
      if (canSkipUrlProcessing(url)) {
        continue;
      }
      data.attrValue =
        data.attrValue.replace(url, computeAssetUrl(url, swhObjectMetadata));
    }

  // process document links
  } else if (node.nodeName === 'A' && data.attrName === 'href') {
    if (canSkipUrlProcessing(data.attrValue)) {
      return;
    }
    if (EmailValidator.validate(data.attrValue)) {
      data.attrValue = `mailto:${data.attrValue}`;
    } else {
      let path = stripQueryParameters(data.attrValue);
      if (path.startsWith('/')) {
        path = path.slice(1);
      }
      const dirLink = $('.swh-path a').last();
      if (dirLink.length) {
        const dirUrl = new URL(dirLink.attr('href'), window.location);
        let newPath;
        if (dirUrl.searchParams.has('path')) {
          newPath = dirUrl.searchParams.get('path') + '/' + path;
        } else {
          newPath = path;
        }
        newPath = resolve(newPath);
        if (newPath) {
          dirUrl.searchParams.set('path', newPath);
        } else {
          dirUrl.searchParams.delete('path');
        }
        data.attrValue = dirUrl.toString();
      }
    }
  }
});

let processCSS = false;

// hook to update CSS url values when they are relative to fetch assets
// from the archive
DOMPurify.addHook('uponSanitizeElement', function(node, data) {
  if (processCSS && data.tagName === 'style') {
    const swhObjectMetadata = swh.webapp.getBrowsedSwhObjectMetadata();
    // the swh object is provided without any useful context
    // to get contents from the archive
    if (!swhObjectMetadata.hasOwnProperty('root_directory')) {
      return;
    }
    const urls = parseCssUrls(node.textContent);
    for (const url of urls) {
      if (canSkipUrlProcessing(url)) {
        continue;
      }
      const assetUrl = computeAssetUrl(url, swhObjectMetadata);
      node.textContent = node.textContent.replace(`url(${url})`, `url(${assetUrl})`);
      node.textContent = node.textContent.replace(`url('${url}')`, `url('${assetUrl}')`);
      node.textContent = node.textContent.replace(`url("${url}")`, `url("${assetUrl}")`);
    }
  }
});

export function filterXSS(html, allowCSS = false) {
  processCSS = allowCSS;
  let options = {
    FORBID_TAGS: ['style']
  };
  if (allowCSS) {
    options = {
    // ensure to keep CSS links
      FORCE_BODY: true,
      ADD_TAGS: [
        'link'
      ],
      ADD_ATTR: [
        'as'
      ]};
  }
  return DOMPurify.sanitize(html, options);
}
