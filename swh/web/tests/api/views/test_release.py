# Copyright (C) 2015-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from datetime import datetime
from hypothesis import given
from rest_framework.test import APITestCase

from swh.model.hashutil import hash_to_bytes
from swh.web.common.utils import reverse
from swh.web.tests.strategies import (
    release, unknown_release, sha1, content, directory
)
from swh.web.tests.testcase import WebTestCase


class ReleaseApiTestCase(WebTestCase, APITestCase):

    @given(release())
    def test_api_release(self, release):

        url = reverse('api-release', url_args={'sha1_git': release})

        rv = self.client.get(url)

        expected_release = self.release_get(release)
        author_id = expected_release['author']['id']
        target_revision = expected_release['target']
        author_url = reverse('api-person',
                             url_args={'person_id': author_id})
        target_url = reverse('api-revision',
                             url_args={'sha1_git': target_revision})
        expected_release['author_url'] = author_url
        expected_release['target_url'] = target_url

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, expected_release)

    @given(sha1(), sha1(), sha1(), content(), directory(), release())
    def test_api_release_target_type_not_a_revision(self, new_rel1, new_rel2,
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

            self.storage.release_add([sample_release])

            url = reverse('api-release', url_args={'sha1_git': new_rel_id})

            rv = self.client.get(url)

            expected_release = self.release_get(new_rel_id)

            author_id = expected_release['author']['id']
            author_url = reverse('api-person',
                                 url_args={'person_id': author_id})

            if target_type == 'content':
                url_args = {'q': 'sha1_git:%s' % target}
            else:
                url_args = {'sha1_git': target}

            target_url = reverse('api-%s' % target_type,
                                 url_args=url_args)
            expected_release['author_url'] = author_url
            expected_release['target_url'] = target_url

            self.assertEqual(rv.status_code, 200)
            self.assertEqual(rv['Content-Type'], 'application/json')
            self.assertEqual(rv.data, expected_release)

    @given(unknown_release())
    def test_api_release_not_found(self, unknown_release):

        url = reverse('api-release', url_args={'sha1_git': unknown_release})

        rv = self.client.get(url)

        self.assertEqual(rv.status_code, 404)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'exception': 'NotFoundExc',
            'reason': 'Release with sha1_git %s not found.' % unknown_release
        })

    @given(release())
    def test_api_release_uppercase(self, release):
        url = reverse('api-release-uppercase-checksum',
                      url_args={'sha1_git': release.upper()})

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)

        redirect_url = reverse('api-release-uppercase-checksum',
                               url_args={'sha1_git': release})

        self.assertEqual(resp['location'], redirect_url)
