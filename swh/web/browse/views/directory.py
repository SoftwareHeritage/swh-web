# Copyright (C) 2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information


from django.shortcuts import render

from swh.web.common import service
from swh.web.common.utils import reverse
from swh.web.common.exc import handle_view_exception
from swh.web.browse.utils import (
    gen_path_info, get_directory_entries
)


def directory_browse(request, sha1_git, path=None):
    """Django view for browsing the content of a SWH directory identified
    by its sha1_git value.

    The url scheme that points to it is the following:

        * :http:get:`/browse/directory/(sha1_git)/`
        * :http:get:`/browse/directory/(sha1_git)/(path)/`

    Args:
        request: input django http request
        sha1_git: swh sha1_git identifer of the directory to browse
        path: optionnal path parameter used to navigate in directories
              reachable from the provided root one

    Returns:
        The HTML rendering for the content of the provided directory.
    """
    root_sha1_git = sha1_git
    try:
        if path:
            dir_info = service.lookup_directory_with_path(sha1_git, path)
            sha1_git = dir_info['target']

        dirs, files = get_directory_entries(sha1_git)
    except Exception as exc:
        return handle_view_exception(exc)

    path_info = gen_path_info(path)

    breadcrumbs = []
    breadcrumbs.append({'name': root_sha1_git[:7],
                        'url': reverse('browse-directory',
                                       kwargs={'sha1_git': root_sha1_git})})
    for pi in path_info:
        breadcrumbs.append({'name': pi['name'],
                            'url': reverse('browse-directory',
                                           kwargs={'sha1_git': root_sha1_git,
                                                   'path': pi['path']})})

    path = '' if path is None else (path + '/')

    for d in dirs:
        d['url'] = reverse('browse-directory',
                           kwargs={'sha1_git': root_sha1_git,
                                   'path': path + d['name']})

    for f in files:
        query_string = 'sha1_git:' + f['target']
        f['url'] = reverse('browse-content',
                           kwargs={'query_string': query_string},
                           query_params={'path': root_sha1_git + '/' +
                                         path + f['name']})

    return render(request, 'directory.html',
                  {'dir_sha1_git': sha1_git,
                   'dirs': dirs,
                   'files': files,
                   'breadcrumbs': breadcrumbs,
                   'branches': None,
                   'branch': None})
