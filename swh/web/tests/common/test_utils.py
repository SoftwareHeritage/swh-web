# Copyright (C) 2017-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import datetime

from unittest.mock import patch

from swh.web.common import utils
from swh.web.common.exc import BadInputExc
from swh.web.tests.testcase import SWHWebTestCase


class UtilsTestCase(SWHWebTestCase):
    def test_shorten_path_noop(self):
        noops = [
            '/api/',
            '/browse/',
            '/content/symbol/foobar/'
        ]

        for noop in noops:
            self.assertEqual(
                utils.shorten_path(noop),
                noop
            )

    def test_shorten_path_sha1(self):
        sha1 = 'aafb16d69fd30ff58afdd69036a26047f3aebdc6'
        short_sha1 = sha1[:8] + '...'

        templates = [
            '/api/1/content/sha1:%s/',
            '/api/1/content/sha1_git:%s/',
            '/api/1/directory/%s/',
            '/api/1/content/sha1:%s/ctags/',
        ]

        for template in templates:
            self.assertEqual(
                utils.shorten_path(template % sha1),
                template % short_sha1
            )

    def test_shorten_path_sha256(self):
        sha256 = ('aafb16d69fd30ff58afdd69036a26047'
                  '213add102934013a014dfca031c41aef')
        short_sha256 = sha256[:8] + '...'

        templates = [
            '/api/1/content/sha256:%s/',
            '/api/1/directory/%s/',
            '/api/1/content/sha256:%s/filetype/',
        ]

        for template in templates:
            self.assertEqual(
                utils.shorten_path(template % sha256),
                template % short_sha256
            )

    def test_parse_timestamp(self):
        input_timestamps = [
            None,
            '2016-01-12',
            '2016-01-12T09:19:12+0100',
            'Today is January 1, 2047 at 8:21:00AM',
            '1452591542',
        ]

        output_dates = [
            None,
            datetime.datetime(2016, 1, 12, 0, 0),
            datetime.datetime(2016, 1, 12, 8, 19, 12,
                              tzinfo=datetime.timezone.utc),
            datetime.datetime(2047, 1, 1, 8, 21),
            datetime.datetime(2016, 1, 12, 9, 39, 2,
                              tzinfo=datetime.timezone.utc),
        ]

        for ts, exp_date in zip(input_timestamps, output_dates):
            self.assertEqual(utils.parse_timestamp(ts), exp_date)

    def test_format_utc_iso_date(self):
        self.assertEqual(utils.format_utc_iso_date('2017-05-04T13:27:13+02:00'), # noqa
                         '04 May 2017, 11:27 UTC')

    def test_gen_path_info(self):
        input_path = '/home/user/swh-environment/swh-web/'
        expected_result = [
            {'name': 'home', 'path': 'home'},
            {'name': 'user', 'path': 'home/user'},
            {'name': 'swh-environment', 'path': 'home/user/swh-environment'},
            {'name': 'swh-web', 'path': 'home/user/swh-environment/swh-web'}
        ]
        path_info = utils.gen_path_info(input_path)
        self.assertEqual(path_info, expected_result)

        input_path = 'home/user/swh-environment/swh-web'
        path_info = utils.gen_path_info(input_path)
        self.assertEqual(path_info, expected_result)

    @patch('swh.web.common.utils.service')
    def test_get_origin_visits(self, mock_service):
        mock_service.MAX_LIMIT = 2

        def _lookup_origin_visits(*args, **kwargs):
            if kwargs['last_visit'] is None:
                return [{'visit': 1,
                         'date': '2017-05-06T00:59:10+00:00',
                         'metadata': {}},
                        {'visit': 2,
                         'date': '2017-08-06T00:59:10+00:00',
                         'metadata': {}}
                        ]
            else:
                return [{'visit': 3,
                         'date': '2017-09-06T00:59:10+00:00',
                         'metadata': {}}
                        ]

        mock_service.lookup_origin_visits.side_effect = _lookup_origin_visits

        origin_info = {
            'id': 1,
            'type': 'git',
            'url': 'https://github.com/foo/bar',
        }

        origin_visits = utils.get_origin_visits(origin_info)

        self.assertEqual(len(origin_visits), 3)

    def test_get_swh_persisent_id(self):
        swh_object_type = 'content'
        sha1_git = 'aafb16d69fd30ff58afdd69036a26047f3aebdc6'

        expected_swh_id = 'swh:1:cnt:' + sha1_git

        self.assertEqual(utils.get_swh_persistent_id(swh_object_type, sha1_git), # noqa
                         expected_swh_id)

        with self.assertRaises(BadInputExc) as cm:
            utils.get_swh_persistent_id('foo', sha1_git)
        self.assertIn('Invalid object', cm.exception.args[0])

        with self.assertRaises(BadInputExc) as cm:
            utils.get_swh_persistent_id(swh_object_type, 'not a valid id')
        self.assertIn('Invalid object', cm.exception.args[0])
