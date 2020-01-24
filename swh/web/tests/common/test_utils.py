# Copyright (C) 2017-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import datetime

import pytest

from swh.web.common import utils
from swh.web.common.exc import BadInputExc


def test_shorten_path_noop():
    noops = [
        '/api/',
        '/browse/',
        '/content/symbol/foobar/'
    ]

    for noop in noops:
        assert utils.shorten_path(noop) == noop


def test_shorten_path_sha1():
    sha1 = 'aafb16d69fd30ff58afdd69036a26047f3aebdc6'
    short_sha1 = sha1[:8] + '...'

    templates = [
        '/api/1/content/sha1:%s/',
        '/api/1/content/sha1_git:%s/',
        '/api/1/directory/%s/',
        '/api/1/content/sha1:%s/ctags/',
    ]

    for template in templates:
        assert utils.shorten_path(template % sha1) == template % short_sha1


def test_shorten_path_sha256():
    sha256 = ('aafb16d69fd30ff58afdd69036a26047'
              '213add102934013a014dfca031c41aef')
    short_sha256 = sha256[:8] + '...'

    templates = [
        '/api/1/content/sha256:%s/',
        '/api/1/directory/%s/',
        '/api/1/content/sha256:%s/filetype/',
    ]

    for template in templates:
        assert utils.shorten_path(template % sha256) == template % short_sha256


def test_parse_timestamp():
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
        assert utils.parse_timestamp(ts) == exp_date


def test_format_utc_iso_date():
    assert (utils.format_utc_iso_date('2017-05-04T13:27:13+02:00') ==
            '04 May 2017, 11:27 UTC')


def test_gen_path_info():
    input_path = '/home/user/swh-environment/swh-web/'
    expected_result = [
        {'name': 'home', 'path': 'home'},
        {'name': 'user', 'path': 'home/user'},
        {'name': 'swh-environment', 'path': 'home/user/swh-environment'},
        {'name': 'swh-web', 'path': 'home/user/swh-environment/swh-web'}
    ]
    path_info = utils.gen_path_info(input_path)
    assert path_info == expected_result

    input_path = 'home/user/swh-environment/swh-web'
    path_info = utils.gen_path_info(input_path)
    assert path_info == expected_result


def test_get_swh_persistent_id():
    swh_object_type = 'content'
    sha1_git = 'aafb16d69fd30ff58afdd69036a26047f3aebdc6'

    expected_swh_id = 'swh:1:cnt:' + sha1_git

    assert (utils.get_swh_persistent_id(swh_object_type, sha1_git) ==
            expected_swh_id)

    with pytest.raises(BadInputExc) as e:
        utils.get_swh_persistent_id('foo', sha1_git)
    assert e.match('Invalid object')

    with pytest.raises(BadInputExc) as e:
        utils.get_swh_persistent_id(swh_object_type, 'not a valid id')
    assert e.match('Invalid object')
