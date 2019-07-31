# Copyright (C) 2018-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from hypothesis import given
from rest_framework.test import APITestCase

from swh.model.identifiers import (
    CONTENT, DIRECTORY, RELEASE, REVISION, SNAPSHOT
)

from swh.web.common.utils import reverse
from swh.web.tests.strategies import (
    content, directory, origin, release, revision, snapshot,
    unknown_content, unknown_directory, unknown_release,
    unknown_revision, unknown_snapshot
)
from swh.web.tests.testcase import WebTestCase


class SwhIdsApiTestCase(WebTestCase, APITestCase):

    @given(origin(), content(), directory(), release(), revision(), snapshot())
    def test_swh_id_resolve_success(self, origin, content, directory,
                                    release, revision, snapshot):

        for obj_type_short, obj_type, obj_id in (
                ('cnt', CONTENT, content['sha1_git']),
                ('dir', DIRECTORY, directory),
                ('rel', RELEASE, release),
                ('rev', REVISION, revision),
                ('snp', SNAPSHOT, snapshot)):

            swh_id = 'swh:1:%s:%s;origin=%s' % (obj_type_short, obj_id,
                                                origin['url'])
            url = reverse('api-1-resolve-swh-pid', url_args={'swh_id': swh_id})

            resp = self.client.get(url)

            if obj_type == CONTENT:
                url_args = {'query_string': 'sha1_git:%s' % obj_id}
            elif obj_type == SNAPSHOT:
                url_args = {'snapshot_id': obj_id}
            else:
                url_args = {'sha1_git': obj_id}

            browse_rev_url = reverse('browse-%s' % obj_type,
                                     url_args=url_args,
                                     query_params={'origin': origin['url']})

            expected_result = {
                'browse_url': browse_rev_url,
                'metadata': {'origin': origin['url']},
                'namespace': 'swh',
                'object_id': obj_id,
                'object_type': obj_type,
                'scheme_version': 1
            }

            self.assertEqual(resp.status_code, 200, resp.data)
            self.assertEqual(resp.data, expected_result)

    def test_swh_id_resolve_invalid(self):
        rev_id_invalid = '96db9023b8_foo_50d6c108e9a3'
        swh_id = 'swh:1:rev:%s' % rev_id_invalid
        url = reverse('api-1-resolve-swh-pid', url_args={'swh_id': swh_id})

        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 400, resp.data)

    @given(unknown_content(), unknown_directory(), unknown_release(),
           unknown_revision(), unknown_snapshot())
    def test_swh_id_resolve_not_found(self, unknown_content, unknown_directory,
                                      unknown_release, unknown_revision,
                                      unknown_snapshot):

        for obj_type_short, obj_id in (('cnt', unknown_content['sha1_git']),
                                       ('dir', unknown_directory),
                                       ('rel', unknown_release),
                                       ('rev', unknown_revision),
                                       ('snp', unknown_snapshot)):

            swh_id = 'swh:1:%s:%s' % (obj_type_short, obj_id)

            url = reverse('api-1-resolve-swh-pid', url_args={'swh_id': swh_id})

            resp = self.client.get(url)

            self.assertEqual(resp.status_code, 404, resp.data)
