/**
 * Copyright (C) 2019-2021  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import DOMPurify from 'dompurify';

// we register a hook when performing XSS filtering in order to
// possibly replace a relative image url with the one for getting
// the image bytes from the archive content
DOMPurify.addHook('uponSanitizeAttribute', function(node, data) {
  if (node.nodeName === 'IMG' && data.attrName === 'src') {

    // image url does not need any processing here
    if (data.attrValue.startsWith('data:image') ||
        data.attrValue.startsWith('http:') ||
        data.attrValue.startsWith('https:')) {
      return;
    }

    // get currently browsed swh object metadata
    const swhObjectMetadata = swh.webapp.getBrowsedSwhObjectMetadata();

    // the swh object is provided without any useful context
    // to get the image checksums from the web api
    if (!swhObjectMetadata.hasOwnProperty('directory')) {
      return;
    }

    let directory;
    // get directory from which to check path existence
    if (swhObjectMetadata.object_type === 'directory') {
      // case when a README is rendered in a directory view
      directory = swhObjectMetadata.object_id;
    } else {
      // otherwise we browse a content, get its directory
      directory = swhObjectMetadata.directory;
    }

    // used internal endpoint as image url to possibly get the image data
    // from the archive content
    let directoryUrl = Urls.browse_directory_resolve_content_path(directory);
    let path = data.attrValue;
    // strip any query parameters appended to path
    let processedPath = path;
    if (!processedPath.startsWith('/')) {
      processedPath = '/' + processedPath;
    }
    const url = new URL(window.location.origin + processedPath);
    if (url.search) {
      path = path.replace(url.search, '');
    }
    // update img src attribute with archive URL
    directoryUrl += `?path=${encodeURIComponent(path)}`;
    data.attrValue = directoryUrl;
  }
});

export function filterXSS(html) {
  return DOMPurify.sanitize(html);
}
