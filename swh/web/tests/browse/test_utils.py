# Copyright (C) 2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import unittest

from unittest.mock import patch
from nose.tools import istest


from swh.web.browse import utils


class SwhBrowseUtilsTestCase(unittest.TestCase):

    @istest
    def gen_path_info(self):
        input_path = '/home/user/swh-environment/swh-web/'
        expected_result = [
            {'name': 'home', 'path': 'home'},
            {'name': 'user', 'path': 'home/user'},
            {'name': 'swh-environment', 'path': 'home/user/swh-environment'},
            {'name': 'swh-web', 'path': 'home/user/swh-environment/swh-web'}
        ]
        path_info = utils.gen_path_info(input_path)
        self.assertEquals(path_info, expected_result)

        input_path = 'home/user/swh-environment/swh-web'
        path_info = utils.gen_path_info(input_path)
        self.assertEquals(path_info, expected_result)

    @istest
    def get_mimetype_for_content(self):
        text = b'Hello world!'
        self.assertEqual(utils.get_mimetype_for_content(text), 'text/plain')

    @patch('swh.web.browse.utils.service')
    @istest
    def get_origin_visits(self, mock_service):
        mock_service.MAX_LIMIT = 2

        def _lookup_origin_visits(*args, **kwargs):
            if kwargs['last_visit'] is None:
                return [{'visit': 1}, {'visit': 2}]
            else:
                return [{'visit': 3}]

        mock_service.lookup_origin_visits.side_effect = _lookup_origin_visits

        origin_visits = utils.get_origin_visits(1)

        self.assertEqual(len(origin_visits), 3)

    @patch('swh.web.browse.utils.service')
    @istest
    def test_get_origin_visit_branches(self, mock_service):

        mock_service.lookup_origin_visit.return_value = \
            {'date': '2015-08-04T22:26:14.804009+00:00',
             'metadata': {},
             'occurrences': {
                 'refs/heads/master': {
                     'target': '9fbd21adbac36be869514e82e2e98505dc47219c',
                     'target_type': 'revision',
                     'target_url': '/api/1/revision/9fbd21adbac36be869514e82e2e98505dc47219c/' # noqa
                 },
                 'refs/tags/0.10.0': {
                     'target': '6072557b6c10cd9a21145781e26ad1f978ed14b9',
                     'target_type': 'revision',
                     'target_url': '/api/1/revision/6072557b6c10cd9a21145781e26ad1f978ed14b9/' # noqa
                 },
                 'refs/tags/0.10.1': {
                     'target': 'ecc003b43433e5b46511157598e4857a761007bf',
                     'target_type': 'revision',
                     'target_url': '/api/1/revision/ecc003b43433e5b46511157598e4857a761007bf/' # noqa
                 }
             },
             'origin': 1,
             'origin_url': '/api/1/origin/1/',
             'status': 'full',
             'visit': 1}

        mock_service.lookup_revision_multiple.return_value = \
            [{'directory': '828da2b80e41aa958b2c98526f4a1d2cc7d298b7'},
             {'directory': '2df4cd84ecc65b50b1d5318d3727e02a39b8a4cf'},
             {'directory': '28ba64f97ef709e54838ae482c2da2619a74a0bd'}]

        expected_result = [
            {'name': 'refs/heads/master',
             'revision': '9fbd21adbac36be869514e82e2e98505dc47219c',
             'directory': '828da2b80e41aa958b2c98526f4a1d2cc7d298b7'},
            {'name': 'refs/tags/0.10.0',
             'revision': '6072557b6c10cd9a21145781e26ad1f978ed14b9',
             'directory': '2df4cd84ecc65b50b1d5318d3727e02a39b8a4cf'},
            {'name': 'refs/tags/0.10.1',
             'revision': 'ecc003b43433e5b46511157598e4857a761007bf',
             'directory': '28ba64f97ef709e54838ae482c2da2619a74a0bd'}
        ]

        origin_visit_branches = utils.get_origin_visit_branches(1, 1)

        self.assertEqual(origin_visit_branches, expected_result)
