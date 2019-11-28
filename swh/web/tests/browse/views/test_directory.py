# Copyright (C) 2017-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import random

from hypothesis import given

from swh.web.common.utils import reverse, get_swh_persistent_id
from swh.web.common.utils import gen_path_info
from swh.web.tests.django_asserts import assert_contains, assert_template_used
from swh.web.tests.strategies import (
    directory, directory_with_subdirs, invalid_sha1,
    unknown_directory
)


@given(directory())
def test_root_directory_view(client, archive_data, directory):
    _directory_view(client, directory, archive_data.directory_ls(directory))


@given(directory_with_subdirs())
def test_sub_directory_view(client, archive_data, directory):
    dir_content = archive_data.directory_ls(directory)
    subdir = random.choice([e for e in dir_content if e['type'] == 'dir'])
    subdir_content = archive_data.directory_ls(subdir['target'])
    _directory_view(client, directory, subdir_content, subdir['name'])


@given(invalid_sha1(), unknown_directory())
def test_directory_request_errors(client, invalid_sha1, unknown_directory):
    dir_url = reverse('browse-directory',
                      url_args={'sha1_git': invalid_sha1})

    resp = client.get(dir_url)
    assert resp.status_code == 400
    assert_template_used(resp, 'error.html')

    dir_url = reverse('browse-directory',
                      url_args={'sha1_git': unknown_directory})

    resp = client.get(dir_url)
    assert resp.status_code == 404
    assert_template_used(resp, 'error.html')


@given(directory())
def test_directory_uppercase(client, directory):
    url = reverse('browse-directory-uppercase-checksum',
                  url_args={'sha1_git': directory.upper()})

    resp = client.get(url)
    assert resp.status_code == 302

    redirect_url = reverse('browse-directory',
                           url_args={'sha1_git': directory})

    assert resp['location'] == redirect_url


def _directory_view(client, root_directory_sha1, directory_entries,
                    path=None):
    dirs = [e for e in directory_entries if e['type'] in ('dir', 'rev')]
    files = [e for e in directory_entries if e['type'] == 'file']

    url_args = {'sha1_git': root_directory_sha1}
    if path:
        url_args['path'] = path

    url = reverse('browse-directory',
                  url_args=url_args)

    root_dir_url = reverse('browse-directory',
                           url_args={'sha1_git': root_directory_sha1})

    resp = client.get(url)

    assert resp.status_code == 200
    assert_template_used(resp, 'browse/directory.html')
    assert_contains(resp, '<a href="' + root_dir_url + '">' +
                    root_directory_sha1[:7] + '</a>')
    assert_contains(resp, '<td class="swh-directory">',
                    count=len(dirs))
    assert_contains(resp, '<td class="swh-content">',
                    count=len(files))

    for d in dirs:
        if d['type'] == 'rev':
            dir_url = reverse('browse-revision',
                              url_args={'sha1_git': d['target']})
        else:
            dir_path = d['name']
            if path:
                dir_path = "%s/%s" % (path, d['name'])
            dir_url = reverse('browse-directory',
                              url_args={'sha1_git': root_directory_sha1,
                                        'path': dir_path})
        assert_contains(resp, dir_url)

    for f in files:
        file_path = "%s/%s" % (root_directory_sha1, f['name'])
        if path:
            file_path = "%s/%s/%s" % (root_directory_sha1, path, f['name'])
        query_string = 'sha1_git:' + f['target']
        file_url = reverse('browse-content',
                           url_args={'query_string': query_string},
                           query_params={'path': file_path})
        assert_contains(resp, file_url)

    path_info = gen_path_info(path)

    assert_contains(resp, '<li class="swh-path">',
                    count=len(path_info)+1)
    assert_contains(resp, '<a href="%s">%s</a>' %
                    (root_dir_url, root_directory_sha1[:7]))

    for p in path_info:
        dir_url = reverse('browse-directory',
                          url_args={'sha1_git': root_directory_sha1,
                                    'path': p['path']})
        assert_contains(resp, '<a href="%s">%s</a>' %
                        (dir_url, p['name']))

    assert_contains(resp, 'vault-cook-directory')

    swh_dir_id = get_swh_persistent_id(
        'directory', directory_entries[0]['dir_id'])
    swh_dir_id_url = reverse('browse-swh-id',
                             url_args={'swh_id': swh_dir_id})
    assert_contains(resp, swh_dir_id)
    assert_contains(resp, swh_dir_id_url)
