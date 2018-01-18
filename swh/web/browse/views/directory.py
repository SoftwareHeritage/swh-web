# Copyright (C) 2017-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information


from django.shortcuts import render
from django.template.defaultfilters import filesizeformat

from swh.web.common import service
from swh.web.common.utils import reverse, gen_path_info
from swh.web.common.exc import handle_view_exception
from swh.web.browse.utils import get_directory_entries

from swh.web.browse.browseurls import browse_route


@browse_route(r'directory/(?P<sha1_git>[0-9a-f]+)/',
              r'directory/(?P<sha1_git>[0-9a-f]+)/(?P<path>.+)/',
              view_name='browse-directory')
def directory_browse(request, sha1_git, path=None):
    """Django view for browsing the content of a SWH directory identified
    by its sha1_git value.

    The url that points to it is :http:get:`/browse/directory/(sha1_git)/[(path)/]`

    Args:
        request: input django http request
        sha1_git: swh sha1_git identifer of the directory to browse
        path: optionnal path parameter used to navigate in directories
              reachable from the provided root one

    Returns:
        The HTML rendering for the content of the provided directory.
    """ # noqa
    root_sha1_git = sha1_git
    try:
        if path:
            dir_info = service.lookup_directory_with_path(sha1_git, path)
            sha1_git = dir_info['target']

        dirs, files = get_directory_entries(sha1_git)
    except Exception as exc:
        return handle_view_exception(request, exc)

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

    sum_file_sizes = 0

    readme_name = None
    readme_url = None

    for f in files:
        query_string = 'sha1_git:' + f['target']
        f['url'] = reverse('browse-content',
                           kwargs={'query_string': query_string},
                           query_params={'path': root_sha1_git + '/' +
                                         path + f['name']})
        sum_file_sizes += f['length']
        f['length'] = filesizeformat(f['length'])
        if f['name'].lower().startswith('readme'):
            readme_name = f['name']
            readme_sha1 = f['checksums']['sha1']
            readme_url = reverse('browse-content-raw',
                                 kwargs={'query_string': readme_sha1})

    sum_file_sizes = filesizeformat(sum_file_sizes)

    dir_metadata = {'id': sha1_git,
                    'number of regular files': len(files),
                    'number of subdirectories': len(dirs),
                    'sum of regular file sizes': sum_file_sizes}

    return render(request, 'directory.html',
                  {'empty_browse': False,
                   'heading': 'Directory information',
                   'top_panel_visible': True,
                   'top_panel_collapsible': True,
                   'top_panel_text_left': 'SWH object: Directory',
                   'top_panel_text_right': 'Sha1 git: ' + sha1_git,
                   'swh_object_metadata': dir_metadata,
                   'main_panel_visible': True,
                   'dirs': dirs,
                   'files': files,
                   'breadcrumbs': breadcrumbs,
                   'branches': None,
                   'branch': None,
                   'top_right_link': None,
                   'top_right_link_text': None,
                   'readme_name': readme_name,
                   'readme_url': readme_url})
