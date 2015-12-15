# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import unittest

from unittest.mock import patch
from nose.tools import istest

from swh.web.ui import utils


class UtilsTestCase(unittest.TestCase):
    def setUp(self):
        self.url_map = [dict(rule='/other/<slug>',
                             methods=set(['GET', 'POST', 'HEAD']),
                             endpoint='foo'),
                        dict(rule='/some/old/url/<slug>',
                             methods=set(['GET', 'POST']),
                             endpoint='blablafn'),
                        dict(rule='/other/old/url/<int:id>',
                             methods=set(['GET', 'HEAD']),
                             endpoint='bar'),
                        dict(rule='/other',
                             methods=set([]),
                             endpoint=None),
                        dict(rule='/other2',
                             methods=set([]),
                             endpoint=None)]

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

    @istest
    def filter_field_keys_dict_unknown_keys(self):
        # when
        actual_res = utils.filter_field_keys(
            {'directory': 1, 'file': 2, 'link': 3},
            {'directory1', 'file2'})

        # then
        self.assertEqual(actual_res, {})

    @istest
    def filter_field_keys_dict(self):
        # when
        actual_res = utils.filter_field_keys(
            {'directory': 1, 'file': 2, 'link': 3},
            {'directory', 'link'})

        # then
        self.assertEqual(actual_res, {'directory': 1, 'link': 3})

    @istest
    def filter_field_keys_list_unknown_keys(self):
        # when
        actual_res = utils.filter_field_keys(
            [{'directory': 1, 'file': 2, 'link': 3},
             {'1': 1, '2': 2, 'link': 3}],
            {'d'})

        # then
        self.assertEqual(actual_res, [{}, {}])

    @istest
    def filter_field_keys_list(self):
        # when
        actual_res = utils.filter_field_keys(
            [{'directory': 1, 'file': 2, 'link': 3},
             {'dir': 1, 'fil': 2, 'lin': 3}],
            {'directory', 'dir'})

        # then
        self.assertEqual(actual_res, [{'directory': 1}, {'dir': 1}])

    @istest
    def filter_field_keys_other(self):
        # given
        inputSet = {1, 2}

        # when
        actual_res = utils.filter_field_keys(inputSet, {'a', '1'})

        # then
        self.assertEqual(actual_res, inputSet)

    @istest
    def fmap(self):
        self.assertEquals([2, 3, 4],
                          utils.fmap(lambda x: x+1, [1, 2, 3]))
        self.assertEquals({'a': 2, 'b': 4},
                          utils.fmap(lambda x: x*2, {'a': 1, 'b': 2}))
        self.assertEquals(100,
                          utils.fmap(lambda x: x*10, 10))

    @istest
    def person_to_string(self):
        self.assertEqual(utils.person_to_string(dict(name='raboof',
                                                     email='foo@bar')),
                         'raboof <foo@bar>')
