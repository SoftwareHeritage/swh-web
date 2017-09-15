# Copyright (C) 2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.http import HttpResponseBadRequest
from django.shortcuts import render

from swh.web.common import service
from swh.web.browse.utils import gen_path_info


def directory_browse(request, sha1_git, path=None):
    """Django view for browsing the content of a swh directory identified
    by its sha1_git value.

    The url scheme that points to that view is the following:

        * /browse/directory/<sha1_git>/

        * /browse/directory/<sha1_git>/<path>/

    The content of the directory is first sorted in lexicographical order
    and the sub-directories are displayed before the regular files.

    The view enables to navigate from the provided root directory to
    directories reachable from it in a recursive way.
    A breadcrumb located in the top part of the view allows
    to keep track of the paths navigated so far.

    Args:
        request: input django http request
        sha1_git: swh sha1_git identifer of the directory to browse
        path: optionnal path parameter used to navigate in directories
              reachable from the provided root one

    """
    root_sha1_git = sha1_git
    try:
        if path:
            dir_info = service.lookup_directory_with_path(sha1_git, path)
            sha1_git = dir_info['target']

        entries = list(service.lookup_directory(sha1_git))
    except Exception as exc:
        return HttpResponseBadRequest(str(exc))

    entries = sorted(entries, key=lambda e: e['name'])
    dirs = [e for e in entries if e['type'] == 'dir']
    files = [e for e in entries if e['type'] == 'file']

    path_info = gen_path_info(path)

    return render(request, 'directory.html',
                  {'root_dir': root_sha1_git,
                   'dirs': dirs,
                   'files': files,
                   'path': '' if path is None else (path + '/'),
                   'path_info': path_info})
