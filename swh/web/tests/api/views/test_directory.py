# Copyright (C) 2015-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import random

from hypothesis import given

from swh.web.common.utils import reverse
from swh.web.tests.data import random_sha1
from swh.web.tests.strategies import directory


@given(directory())
def test_api_directory(api_client, archive_data, directory):

    url = reverse('api-1-directory', url_args={'sha1_git': directory})
    rv = api_client.get(url)

    assert rv.status_code == 200, rv.data
    assert rv['Content-Type'] == 'application/json'

    expected_data = list(map(_enrich_dir_data,
                             archive_data.directory_ls(directory)))

    assert rv.data == expected_data


def test_api_directory_not_found(api_client):
    unknown_directory_ = random_sha1()

    url = reverse('api-1-directory',
                  url_args={'sha1_git': unknown_directory_})
    rv = api_client.get(url)

    assert rv.status_code == 404, rv.data
    assert rv['Content-Type'] == 'application/json'
    assert rv.data == {
        'exception': 'NotFoundExc',
        'reason': 'Directory with sha1_git %s not found' % unknown_directory_
    }


@given(directory())
def test_api_directory_with_path_found(api_client, archive_data, directory):

    directory_content = archive_data.directory_ls(directory)
    path = random.choice(directory_content)

    url = reverse('api-1-directory',
                  url_args={'sha1_git': directory, 'path': path['name']})
    rv = api_client.get(url)

    assert rv.status_code == 200, rv.data
    assert rv['Content-Type'] == 'application/json'
    assert rv.data == _enrich_dir_data(path)


@given(directory())
def test_api_directory_with_path_not_found(api_client, directory):

    path = 'some/path/to/nonexistent/dir/'
    url = reverse('api-1-directory',
                  url_args={'sha1_git': directory, 'path': path})
    rv = api_client.get(url)

    assert rv.status_code == 404, rv.data
    assert rv['Content-Type'] == 'application/json'
    assert rv.data == {
        'exception': 'NotFoundExc',
        'reason': ('Directory entry with path %s from %s not found' %
                   (path, directory))
    }


@given(directory())
def test_api_directory_uppercase(api_client, directory):
    url = reverse('api-1-directory-uppercase-checksum',
                  url_args={'sha1_git': directory.upper()})

    resp = api_client.get(url)
    assert resp.status_code == 302

    redirect_url = reverse('api-1-directory', url_args={'sha1_git': directory})

    assert resp['location'] == redirect_url


def _enrich_dir_data(dir_data):
    if dir_data['type'] == 'file':
        dir_data['target_url'] = reverse(
            'api-1-content',
            url_args={'q': 'sha1_git:%s' % dir_data['target']})
    elif dir_data['type'] == 'dir':
        dir_data['target_url'] = reverse(
            'api-1-directory',
            url_args={'sha1_git': dir_data['target']})
    elif dir_data['type'] == 'rev':
        dir_data['target_url'] = reverse(
            'api-1-revision',
            url_args={'sha1_git': dir_data['target']})
    return dir_data
