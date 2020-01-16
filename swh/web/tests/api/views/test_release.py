# Copyright (C) 2015-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from datetime import datetime
from hypothesis import given

from swh.model.hashutil import hash_to_bytes
from swh.web.common.utils import reverse
from swh.web.tests.data import random_sha1
from swh.web.tests.strategies import (
    release, sha1, content, directory
)


@given(release())
def test_api_release(api_client, archive_data, release):
    url = reverse('api-1-release', url_args={'sha1_git': release})

    rv = api_client.get(url)

    expected_release = archive_data.release_get(release)
    target_revision = expected_release['target']
    target_url = reverse('api-1-revision',
                         url_args={'sha1_git': target_revision},
                         request=rv.wsgi_request)
    expected_release['target_url'] = target_url

    assert rv.status_code == 200, rv.data
    assert rv['Content-Type'] == 'application/json'
    assert rv.data == expected_release


@given(sha1(), sha1(), sha1(), content(), directory(), release())
def test_api_release_target_type_not_a_revision(api_client, archive_data,
                                                new_rel1, new_rel2,
                                                new_rel3, content,
                                                directory, release):
    for new_rel_id, target_type, target in (
            (new_rel1, 'content', content),
            (new_rel2, 'directory', directory),
            (new_rel3, 'release', release)):

        if target_type == 'content':
            target = target['sha1_git']

        sample_release = {
            'author': {
                'email': b'author@company.org',
                'fullname': b'author <author@company.org>',
                'name': b'author'
            },
            'date': {
                'timestamp': int(datetime.now().timestamp()),
                'offset': 0,
                'negative_utc': False,
            },
            'id': hash_to_bytes(new_rel_id),
            'message': b'sample release message',
            'name': b'sample release',
            'synthetic': False,
            'target': hash_to_bytes(target),
            'target_type': target_type
        }

        archive_data.release_add([sample_release])

        url = reverse('api-1-release', url_args={'sha1_git': new_rel_id})

        rv = api_client.get(url)

        expected_release = archive_data.release_get(new_rel_id)

        if target_type == 'content':
            url_args = {'q': 'sha1_git:%s' % target}
        else:
            url_args = {'sha1_git': target}

        target_url = reverse('api-1-%s' % target_type,
                             url_args=url_args,
                             request=rv.wsgi_request)
        expected_release['target_url'] = target_url

        assert rv.status_code == 200, rv.data
        assert rv['Content-Type'] == 'application/json'
        assert rv.data == expected_release


def test_api_release_not_found(api_client):
    unknown_release_ = random_sha1()

    url = reverse('api-1-release', url_args={'sha1_git': unknown_release_})

    rv = api_client.get(url)

    assert rv.status_code == 404, rv.data
    assert rv['Content-Type'] == 'application/json'
    assert rv.data == {
        'exception': 'NotFoundExc',
        'reason': 'Release with sha1_git %s not found.' % unknown_release_
    }


@given(release())
def test_api_release_uppercase(api_client, release):
    url = reverse('api-1-release-uppercase-checksum',
                  url_args={'sha1_git': release.upper()})

    resp = api_client.get(url)
    assert resp.status_code == 302

    redirect_url = reverse('api-1-release-uppercase-checksum',
                           url_args={'sha1_git': release})

    assert resp['location'] == redirect_url
