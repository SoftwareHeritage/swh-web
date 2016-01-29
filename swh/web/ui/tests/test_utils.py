# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import datetime
import dateutil
import unittest

from unittest.mock import patch, call
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

    @istest
    def prepare_data_for_view_default_encoding(self):
        self.maxDiff = None
        # given
        inputs = [
            {
                'data': b'some blah data'
            },
            {
                'data': 1,
                'data_url': '/api/1/some/api/call',
            },
            {
                'blah': 'foobar',
                'blah_url': '/some/non/changed/api/call'
            }]

        # when
        actual_result = utils.prepare_data_for_view(inputs)

        # then
        self.assertEquals(actual_result, [
            {
                'data': 'some blah data',
            },
            {
                'data': 1,
                'data_url': '/browse/some/api/call',
            },
            {
                'blah': 'foobar',
                'blah_url': '/some/non/changed/api/call'
            }
        ])

    @istest
    def prepare_data_for_view(self):
        self.maxDiff = None
        # given
        inputs = [
            {
                'data': b'some blah data'
            },
            {
                'data': 1,
                'data_url': '/api/1/some/api/call',
            },
            {
                'blah': 'foobar',
                'blah_url': '/some/non/changed/api/call'
            }]

        # when
        actual_result = utils.prepare_data_for_view(inputs, encoding='ascii')

        # then
        self.assertEquals(actual_result, [
            {
                'data': 'some blah data',
            },
            {
                'data': 1,
                'data_url': '/browse/some/api/call',
            },
            {
                'blah': 'foobar',
                'blah_url': '/some/non/changed/api/call'
            }
        ])

    @istest
    def prepare_data_for_view_KO_cannot_decode(self):
        self.maxDiff = None
        # given
        inputs = {
            'data': 'hé dude!'.encode('utf8'),
        }

        actual_result = utils.prepare_data_for_view(inputs, encoding='ascii')

        # then
        self.assertEquals(actual_result, {
                'data': "Cannot decode the data bytes, try and set another "
                        "encoding in the url (e.g. ?encoding=utf8) or "
                        "download directly the "
                        "content's raw data.",
            })

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
        input_set = {1, 2}

        # when
        actual_res = utils.filter_field_keys(input_set, {'a', '1'})

        # then
        self.assertEqual(actual_res, input_set)

    @istest
    def fmap(self):
        self.assertEquals([2, 3, 4],
                          utils.fmap(lambda x: x+1, [1, 2, 3]))
        self.assertEquals([11, 12, 13],
                          list(utils.fmap(lambda x: x+10,
                                          map(lambda x: x, [1, 2, 3]))))
        self.assertEquals({'a': 2, 'b': 4},
                          utils.fmap(lambda x: x*2, {'a': 1, 'b': 2}))
        self.assertEquals(100,
                          utils.fmap(lambda x: x*10, 10))
        self.assertEquals({'a': [2, 6], 'b': 4},
                          utils.fmap(lambda x: x*2, {'a': [1, 3], 'b': 2}))

    @istest
    def person_to_string(self):
        self.assertEqual(utils.person_to_string(dict(name='raboof',
                                                     email='foo@bar')),
                         'raboof <foo@bar>')

    @istest
    def parse_timestamp(self):
        input_timestamps = [
            '2016-01-12',
            '2016-01-12T09:19:12+0100',
            'Today is January 1, 2047 at 8:21:00AM',
            '1452591542',
        ]

        output_dates = [
            datetime.datetime(2016, 1, 12, 0, 0),
            datetime.datetime(2016, 1, 12, 9, 19, 12,
                              tzinfo=dateutil.tz.tzoffset(None, 3600)),
            datetime.datetime(2047, 1, 1, 8, 21),
            datetime.datetime(2016, 1, 12, 10, 39, 2),
        ]

        for ts, exp_date in zip(input_timestamps, output_dates):
            self.assertEquals(utils.parse_timestamp(ts), exp_date)

    @istest
    def enrich_release_0(self):
        # when
        actual_release = utils.enrich_release({})

        # then
        self.assertEqual(actual_release, {})

    @patch('swh.web.ui.utils.flask')
    @istest
    def enrich_release_1(self, mock_flask):
        # given
        mock_flask.url_for.return_value = '/api/1/content/sha1_git:123/'

        # when
        actual_release = utils.enrich_release({'target': '123',
                                               'target_type': 'content'})

        # then
        self.assertEqual(actual_release, {
            'target': '123',
            'target_type': 'content',
            'target_url': '/api/1/content/sha1_git:123/'
        })

        mock_flask.url_for.assert_called_once_with('api_content_metadata',
                                                   q='sha1_git:123')

    @patch('swh.web.ui.utils.flask')
    @istest
    def enrich_release_2(self, mock_flask):
        # given
        mock_flask.url_for.return_value = '/api/1/dir/23/'

        # when
        actual_release = utils.enrich_release({'target': '23',
                                               'target_type': 'directory'})

        # then
        self.assertEqual(actual_release, {
            'target': '23',
            'target_type': 'directory',
            'target_url': '/api/1/dir/23/'
        })

        mock_flask.url_for.assert_called_once_with('api_directory',
                                                   q='23')

    @patch('swh.web.ui.utils.flask')
    @istest
    def enrich_release_3(self, mock_flask):
        # given
        mock_flask.url_for.return_value = '/api/1/rev/3/'

        # when
        actual_release = utils.enrich_release({'target': '3',
                                               'target_type': 'revision'})

        # then
        self.assertEqual(actual_release, {
            'target': '3',
            'target_type': 'revision',
            'target_url': '/api/1/rev/3/'
        })

        mock_flask.url_for.assert_called_once_with('api_revision',
                                                   sha1_git='3')

    @patch('swh.web.ui.utils.flask')
    @istest
    def enrich_release_4(self, mock_flask):
        # given
        mock_flask.url_for.return_value = '/api/1/rev/4/'

        # when
        actual_release = utils.enrich_release({'target': '4',
                                               'target_type': 'release'})

        # then
        self.assertEqual(actual_release, {
            'target': '4',
            'target_type': 'release',
            'target_url': '/api/1/rev/4/'
        })

        mock_flask.url_for.assert_called_once_with('api_release',
                                                   sha1_git='4')

    @patch('swh.web.ui.utils.flask')
    @istest
    def enrich_directory_no_type(self, mock_flask):
        # when/then
        self.assertEqual(utils.enrich_directory({'id': 'dir-id'}),
                         {'id': 'dir-id'})

        # given
        mock_flask.url_for.return_value = '/api/content/sha1_git:123/'

        # when
        actual_directory = utils.enrich_directory({
            'id': 'dir-id',
            'type': 'file',
            'target': '123',
        })

        # then
        self.assertEqual(actual_directory, {
            'id': 'dir-id',
            'type': 'file',
            'target': '123',
            'target_url': '/api/content/sha1_git:123/',
        })

        mock_flask.url_for.assert_called_once_with('api_content_metadata',
                                                   q='sha1_git:123')

    @patch('swh.web.ui.utils.flask')
    @istest
    def enrich_directory_with_context_and_type_file(self, mock_flask):
        # given
        mock_flask.url_for.return_value = '/api/content/sha1_git:123/'

        # when
        actual_directory = utils.enrich_directory({
            'id': 'dir-id',
            'type': 'file',
            'name': 'hy',
            'target': '789',
        }, context_url='/api/revision/revsha1/directory/prefix/path/')

        # then
        self.assertEqual(actual_directory, {
            'id': 'dir-id',
            'type': 'file',
            'name': 'hy',
            'target': '789',
            'target_url': '/api/content/sha1_git:123/',
            'file_url': '/api/revision/revsha1/directory'
                        '/prefix/path/hy/'
        })

        mock_flask.url_for.assert_called_once_with('api_content_metadata',
                                                   q='sha1_git:789')

    @patch('swh.web.ui.utils.flask')
    @istest
    def enrich_directory_with_context_and_type_dir(self, mock_flask):
        # given
        mock_flask.url_for.return_value = '/api/directory/456/'

        # when
        actual_directory = utils.enrich_directory({
            'id': 'dir-id',
            'type': 'dir',
            'name': 'emacs-42',
            'target_type': 'file',
            'target': '456',
        }, context_url='/api/revision/origin/2/directory/some/prefix/path/')

        # then
        self.assertEqual(actual_directory, {
            'id': 'dir-id',
            'type': 'dir',
            'target_type': 'file',
            'name': 'emacs-42',
            'target': '456',
            'target_url': '/api/directory/456/',
            'dir_url': '/api/revision/origin/2/directory'
            '/some/prefix/path/emacs-42/'
        })

        mock_flask.url_for.assert_called_once_with('api_directory',
                                                   sha1_git='456')

    @istest
    def enrich_content_without_sha1(self):
        # when/then
        self.assertEqual(utils.enrich_content({'id': '123'}),
                         {'id': '123'})

    @patch('swh.web.ui.utils.flask')
    @istest
    def enrich_content_with_sha1(self, mock_flask):
        # given
        mock_flask.url_for.return_value = '/api/content/sha1:123/raw/'

        # when/then
        self.assertEqual(utils.enrich_content(
            {'id': '123', 'sha1': 'blahblah'}),
                         {'id': '123', 'sha1': 'blahblah',
                          'data_url': '/api/content/sha1:123/raw/'})

        mock_flask.url_for.assert_called_once_with('api_content_raw',
                                                   q='blahblah')

    @istest
    def enrich_entity_identity(self):
        # when/then
        self.assertEqual(utils.enrich_content({'id': '123'}),
                         {'id': '123'})

    @patch('swh.web.ui.utils.flask')
    @istest
    def enrich_entity_with_sha1(self, mock_flask):
        # given
        def url_for_test(fn, **entity):
            return '/api/entity/' + entity['uuid'] + '/'

        mock_flask.url_for.side_effect = url_for_test

        # when
        actual_entity = utils.enrich_entity({
            'uuid': 'uuid-1',
            'parent': 'uuid-parent',
            'name': 'something'
        })

        # then
        self.assertEqual(actual_entity, {
            'uuid': 'uuid-1',
            'uuid_url': '/api/entity/uuid-1/',
            'parent': 'uuid-parent',
            'parent_url': '/api/entity/uuid-parent/',
            'name': 'something',
            })

        mock_flask.url_for.assert_has_calls([call('api_entity_by_uuid',
                                                  uuid='uuid-1'),
                                             call('api_entity_by_uuid',
                                                  uuid='uuid-parent')])

    @patch('swh.web.ui.utils.flask')
    @istest
    def enrich_revision_without_children_or_parent(self, mock_flask):
        # given
        def url_for_test(fn, **data):
            print(fn, data)
            if fn == 'api_revision':
                return '/api/revision/' + data['sha1_git'] + '/'
            elif fn == 'api_revision_log':
                return '/api/revision/' + data['sha1_git'] + '/log/'
            elif fn == 'api_directory':
                return '/api/directory/' + data['sha1_git'] + '/'

        mock_flask.url_for.side_effect = url_for_test

        # when
        actual_revision = utils.enrich_revision({
            'id': 'rev-id',
            'directory': '123'
        })

        # then
        self.assertEqual(actual_revision, {
            'id': 'rev-id',
            'directory': '123',
            'url': '/api/revision/rev-id/',
            'history_url': '/api/revision/rev-id/log/',
            'directory_url': '/api/directory/123/'
        })

        mock_flask.url_for.assert_has_calls([call('api_revision',
                                                  sha1_git='rev-id'),
                                             call('api_revision_log',
                                                  sha1_git='rev-id'),
                                             call('api_directory',
                                                  sha1_git='123')])

    @patch('swh.web.ui.utils.flask')
    @istest
    def enrich_revision_with_children_and_parent_no_dir(self,
                                                        mock_flask):
        # given
        def url_for_test(fn, **data):
            print(fn, data)
            if fn == 'api_revision':
                return '/api/revision/' + data['sha1_git'] + '/'
            elif fn == 'api_revision_log':
                return '/api/revision/' + data['sha1_git'] + '/log/'
            else:
                return '/api/revision/' + data['sha1_git_root'] + '/history/' + data['sha1_git'] + '/'  # noqa

        mock_flask.url_for.side_effect = url_for_test

        # when
        actual_revision = utils.enrich_revision({
            'id': 'rev-id',
            'parents': ['123'],
            'children': ['456'],
        }, context='sha1_git_root')

        # then
        self.assertEqual(actual_revision, {
            'id': 'rev-id',
            'url': '/api/revision/rev-id/',
            'history_url': '/api/revision/rev-id/log/',
            'parents': ['123'],
            'parent_urls': ['/api/revision/sha1_git_root/history/123/'],
            'children': ['456'],
            'children_urls': ['/api/revision/sha1_git_root/history/456/'],
        })

        mock_flask.url_for.assert_has_calls(
            [call('api_revision',
                  sha1_git='rev-id'),
             call('api_revision_log',
                  sha1_git='rev-id'),
             call('api_revision_history',
                  sha1_git_root='sha1_git_root',
                  sha1_git='123'),
             call('api_revision_history',
                  sha1_git_root='sha1_git_root',
                  sha1_git='456')])
