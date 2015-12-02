# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import unittest

from unittest.mock import patch
from nose.tools import istest

from swh.web.ui import utils


class Rule(object):
    rule = ""
    endpoint = None
    methods = []

    def __init__(self, rule, methods, endpoint):
        self.rule = rule
        self.endpoint = endpoint
        self.methods = methods


class Map(object):
    _rules = []

    def __init__(self, rules):
        self._rules = rules


class UtilsTestCase(unittest.TestCase):
    def setUp(self):
        self.url_map = Map([Rule('/other/<slug>',
                                 methods=set(['GET', 'POST', 'HEAD']),
                                 endpoint='foo'),
                            Rule('/some/old/url/<slug>',
                                 methods=set(['GET', 'POST']),
                                 endpoint='blablafn'),
                            Rule('/other/old/url/<int:id>',
                                 methods=set(['GET', 'HEAD']),
                                 endpoint='bar'),
                            Rule('/other',
                                 methods=set([]),
                                 endpoint=None),
                            Rule('/other2',
                                 methods=set([]),
                                 endpoint=None)])

    @istest
    def filter_endpoints_1(self):
        # when
        actual_data = utils.filter_endpoints(self.url_map, '/some')

        # then
        self.assertEquals(actual_data, {
            '/some/old/url/<slug>': {
                'methods': ['GET', 'POST'],
                'endpoint': 'blablafn'
            }
        })

    @istest
    def filter_endpoints_2(self):
        # when
        actual_data = utils.filter_endpoints(self.url_map, '/other',
                                             blacklist=['/other2'])

        # then
        # rules /other is skipped because its' exactly the prefix url
        # rules /other2 is skipped because it's blacklisted
        self.assertEquals(actual_data, {
            '/other/<slug>': {
                'methods': ['GET', 'HEAD', 'POST'],
                'endpoint': 'foo'
            },
            '/other/old/url/<int:id>': {
                'methods': ['GET', 'HEAD'],
                'endpoint': 'bar'
            }
        })

    @patch('swh.web.ui.utils.flask')
    @istest
    def prepare_directory_listing(self, mock_flask):
        # given
        def mock_url_for(url_key, **kwds):
            if url_key == 'browse_directory':
                sha1_git = kwds['sha1_git']
                return '/path/to/url/dir' + '/' + sha1_git
            else:
                sha1_git = kwds['q']
                return '/path/to/url/file' + '/' + sha1_git

        mock_flask.url_for.side_effect = mock_url_for

        inputs = [{'type': 'dir',
                   'target': '123',
                   'name': 'some-dir-name'},
                  {'type': 'file',
                   'sha1': '654',
                   'name': 'some-filename'},
                  {'type': 'dir',
                   'target': '987',
                   'name': 'some-other-dirname'}]

        expected_output = [{'link': '/path/to/url/dir/123',
                            'name': 'some-dir-name',
                            'type': 'dir'},
                           {'link': '/path/to/url/file/654',
                            'name': 'some-filename',
                            'type': 'file'},
                           {'link': '/path/to/url/dir/987',
                            'name': 'some-other-dirname',
                            'type': 'dir'}]

        # when
        actual_outputs = utils.prepare_directory_listing(inputs)

        # then
        self.assertEquals(actual_outputs, expected_output)
