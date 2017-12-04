# Copyright (C) 2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import datetime
import dateutil
import unittest

from nose.tools import istest

from swh.web.common import utils


class UtilsTestCase(unittest.TestCase):
    @istest
    def shorten_path_noop(self):
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

    @istest
    def shorten_path_sha1(self):
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

    @istest
    def shorten_path_sha256(self):
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

    @istest
    def parse_timestamp(self):
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
            datetime.datetime(2016, 1, 12, 9, 19, 12,
                              tzinfo=dateutil.tz.tzoffset(None, 3600)),
            datetime.datetime(2047, 1, 1, 8, 21),
            datetime.datetime(2016, 1, 12, 9, 39, 2,
                              tzinfo=datetime.timezone.utc),
        ]

        for ts, exp_date in zip(input_timestamps, output_dates):
            self.assertEquals(utils.parse_timestamp(ts), exp_date)

    @istest
    def format_utc_iso_date(self):
        self.assertEqual(utils.format_utc_iso_date('2017-05-04T13:27:13+02:00'), # noqa
                         '04 May 2017, 13:27 UTC')

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
