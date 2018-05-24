# Copyright (C) 2017-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


from django.shortcuts import render, redirect
from django.template.defaultfilters import filesizeformat

from swh.web.common import service
from swh.web.common.utils import reverse, gen_path_info
from swh.web.common.exc import handle_view_exception
from swh.web.browse.utils import (
    get_directory_entries, get_snapshot_context,
    get_readme_to_display
)

from swh.web.browse.browseurls import browse_route


@browse_route(r'directory/(?P<sha1_git>[0-9a-f]+)/',
              r'directory/(?P<sha1_git>[0-9a-f]+)/(?P<path>.+)/',
              view_name='browse-directory')
def directory_browse(request, sha1_git, path=None):
    """Django view for browsing the content of a SWH directory identified
    by its sha1_git value.

    The url that points to it is :http:get:`/browse/directory/(sha1_git)/[(path)/]`
    """ # noqa
    root_sha1_git = sha1_git
    try:
        if path:
            dir_info = service.lookup_directory_with_path(sha1_git, path)
            # some readme files can reference assets reachable from the
            # browsed directory, handle that special case in order to
            # correctly displayed them
            if dir_info and dir_info['type'] == 'file':
                file_raw_url = reverse(
                    'browse-content-raw',
                    kwargs={'query_string': dir_info['checksums']['sha1']})
                return redirect(file_raw_url)
            sha1_git = dir_info['target']

        dirs, files = get_directory_entries(sha1_git)
        origin_type = request.GET.get('origin_type', None)
        origin_url = request.GET.get('origin_url', None)
        if not origin_url:
            origin_url = request.GET.get('origin', None)
        snapshot_context = None
        if origin_url:
            snapshot_context = get_snapshot_context(None, origin_type,
                                                    origin_url)
        if snapshot_context:
            snapshot_context['visit_info'] = None
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

    readmes = {}

    for f in files:
        query_string = 'sha1_git:' + f['target']
        f['url'] = reverse('browse-content',
                           kwargs={'query_string': query_string},
                           query_params={'path': root_sha1_git + '/' +
                                         path + f['name']})
        sum_file_sizes += f['length']
        f['length'] = filesizeformat(f['length'])
        if f['name'].lower().startswith('readme'):
            readmes[f['name']] = f['checksums']['sha1']

    readme_name, readme_url, readme_html = get_readme_to_display(readmes)

    sum_file_sizes = filesizeformat(sum_file_sizes)

    dir_metadata = {'id': sha1_git,
                    'number of regular files': len(files),
                    'number of subdirectories': len(dirs),
                    'sum of regular file sizes': sum_file_sizes}

    vault_cooking = {
        'directory_context': True,
        'directory_id': sha1_git,
        'revision_context': False,
        'revision_id': None
    }

    return render(request, 'directory.html',
                  {'empty_browse': False,
                   'heading': 'Directory',
                   'swh_object_name': 'Directory',
                   'swh_object_metadata': dir_metadata,
                   'dirs': dirs,
                   'files': files,
                   'breadcrumbs': breadcrumbs,
                   'top_right_link': None,
                   'top_right_link_text': None,
                   'readme_name': readme_name,
                   'readme_url': readme_url,
                   'readme_html': readme_html,
                   'snapshot_context': snapshot_context,
                   'vault_cooking': vault_cooking,
                   'show_actions_menu': True})
