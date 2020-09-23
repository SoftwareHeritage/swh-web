/**
 * Copyright (C) 2019-2020  The Software Heritage developers
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
    let swhObjectMetadata = swh.webapp.getBrowsedSwhObjectMetadata();

    // the swh object is provided without any useful context
    // to get the image checksums from the web api
    if (!swhObjectMetadata.hasOwnProperty('directory')) {
      return;
    }

    // used internal endpoint as image url to possibly get the image data
    // from the archive content
    let url = Urls.browse_directory_resolve_content_path(swhObjectMetadata.directory);
    url += `?path=${data.attrValue}`;
    data.attrValue = url;
  }
});

export function filterXSS(html) {
  return DOMPurify.sanitize(html);
}
