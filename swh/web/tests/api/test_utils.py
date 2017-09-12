# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import unittest

from unittest.mock import patch, call
from nose.tools import istest, nottest

from swh.web.api import utils


class UtilsTestCase(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
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
    def prepare_data_for_view_ko_cannot_decode(self):
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
    def filter_field_keys_map(self):
        # when
        actual_res = utils.filter_field_keys(
            map(lambda x: {'i': x['i']+1, 'j': x['j']},
                [{'i': 1, 'j': None},
                 {'i': 2, 'j': None},
                 {'i': 3, 'j': None}]),
            {'i'})

        # then
        self.assertEqual(list(actual_res), [{'i': 2}, {'i': 3}, {'i': 4}])

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
        self.assertEquals([2, 3, None, 4],
                          utils.fmap(lambda x: x+1, [1, 2, None, 3]))
        self.assertEquals([11, 12, 13],
                          list(utils.fmap(lambda x: x+10,
                                          map(lambda x: x, [1, 2, 3]))))
        self.assertEquals({'a': 2, 'b': 4},
                          utils.fmap(lambda x: x*2, {'a': 1, 'b': 2}))
        self.assertEquals(100,
                          utils.fmap(lambda x: x*10, 10))
        self.assertEquals({'a': [2, 6], 'b': 4},
                          utils.fmap(lambda x: x*2, {'a': [1, 3], 'b': 2}))

        self.assertIsNone(utils.fmap(lambda x: x, None))

    @istest
    def person_to_string(self):
        self.assertEqual(utils.person_to_string(dict(name='raboof',
                                                     email='foo@bar')),
                         'raboof <foo@bar>')

    @istest
    def enrich_release_0(self):
        # when
        actual_release = utils.enrich_release({})

        # then
        self.assertEqual(actual_release, {})

    @patch('swh.web.api.utils.reverse')
    @istest
    def enrich_release_1(self, mock_django_reverse):
        # given

        def reverse_test_context(view_name, kwargs):
            if view_name == 'content':
                id = kwargs['q']
                return '/api/1/content/%s/' % id
            elif view_name == 'person':
                id = kwargs['person_id']
                return '/api/1/person/%s/' % id
            else:
                raise ValueError(
                    'This should not happened so fail if it does.')

        mock_django_reverse.side_effect = reverse_test_context

        # when
        actual_release = utils.enrich_release({
            'target': '123',
            'target_type': 'content',
            'author': {
                'id': 100,
                'name': 'author release name',
                'email': 'author@email',
            },
        })

        # then
        self.assertEqual(actual_release, {
            'target': '123',
            'target_type': 'content',
            'target_url': '/api/1/content/sha1_git:123/',
            'author_url': '/api/1/person/100/',
            'author': {
                'id': 100,
                'name': 'author release name',
                'email': 'author@email',
            },
        })

        mock_django_reverse.assert_has_calls([
                call('content', kwargs={'q': 'sha1_git:123'}),
                call('person', kwargs={'person_id': 100})
        ])

    @patch('swh.web.api.utils.reverse')
    @istest
    def enrich_release_2(self, mock_django_reverse):
        # given
        mock_django_reverse.return_value = '/api/1/dir/23/'

        # when
        actual_release = utils.enrich_release({'target': '23',
                                               'target_type': 'directory'})

        # then
        self.assertEqual(actual_release, {
            'target': '23',
            'target_type': 'directory',
            'target_url': '/api/1/dir/23/'
        })

        mock_django_reverse.assert_called_once_with('directory',
                                                    kwargs={'sha1_git': '23'})

    @patch('swh.web.api.utils.reverse')
    @istest
    def enrich_release_3(self, mock_django_reverse):
        # given
        mock_django_reverse.return_value = '/api/1/rev/3/'

        # when
        actual_release = utils.enrich_release({'target': '3',
                                               'target_type': 'revision'})

        # then
        self.assertEqual(actual_release, {
            'target': '3',
            'target_type': 'revision',
            'target_url': '/api/1/rev/3/'
        })

        mock_django_reverse.assert_called_once_with('revision',
                                                    kwargs={'sha1_git': '3'})

    @patch('swh.web.api.utils.reverse')
    @istest
    def enrich_release_4(self, mock_django_reverse):
        # given
        mock_django_reverse.return_value = '/api/1/rev/4/'

        # when
        actual_release = utils.enrich_release({'target': '4',
                                               'target_type': 'release'})

        # then
        self.assertEqual(actual_release, {
            'target': '4',
            'target_type': 'release',
            'target_url': '/api/1/rev/4/'
        })

        mock_django_reverse.assert_called_once_with('release',
                                                    kwargs={'sha1_git': '4'})

    @patch('swh.web.api.utils.reverse')
    @istest
    def enrich_directory_no_type(self, mock_django_reverse):
        # when/then
        self.assertEqual(utils.enrich_directory({'id': 'dir-id'}),
                         {'id': 'dir-id'})

        # given
        mock_django_reverse.return_value = '/api/content/sha1_git:123/'

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

        mock_django_reverse.assert_called_once_with(
            'content', kwargs={'q': 'sha1_git:123'})

    @patch('swh.web.api.utils.reverse')
    @istest
    def enrich_directory_with_context_and_type_file(self, mock_django_reverse):
        # given
        mock_django_reverse.return_value = '/api/content/sha1_git:123/'

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

        mock_django_reverse.assert_called_once_with(
            'content', kwargs={'q': 'sha1_git:789'})

    @patch('swh.web.api.utils.reverse')
    @istest
    def enrich_directory_with_context_and_type_dir(self, mock_django_reverse):
        # given
        mock_django_reverse.return_value = '/api/directory/456/'

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

        mock_django_reverse.assert_called_once_with('directory',
                                                    kwargs={'sha1_git': '456'})

    @istest
    def enrich_content_without_hashes(self):
        # when/then
        self.assertEqual(utils.enrich_content({'id': '123'}),
                         {'id': '123'})

    @patch('swh.web.api.utils.reverse')
    @istest
    def enrich_content_with_hashes(self, mock_django_reverse):
        for h in ['sha1', 'sha256', 'sha1_git']:
            # given
            mock_django_reverse.side_effect = [
                '/api/content/%s:123/raw/' % h,
                '/api/filetype/%s:123/' % h,
                '/api/language/%s:123/' % h,
                '/api/license/%s:123/' % h,
                ]

            # when
            enriched_content = utils.enrich_content(
                {
                    'id': '123',
                    h: 'blahblah'
                }
            )

            # then
            self.assertEqual(
                enriched_content,
                {
                    'id': '123',
                    h: 'blahblah',
                    'data_url': '/api/content/%s:123/raw/' % h,
                    'filetype_url': '/api/filetype/%s:123/' % h,
                    'language_url': '/api/language/%s:123/' % h,
                    'license_url': '/api/license/%s:123/' % h,
                }
            )

            mock_django_reverse.assert_has_calls([
                call('content-raw', kwargs={'q': '%s:blahblah' % h}),
                call('content-filetype', kwargs={'q': '%s:blahblah' % h}),
                call('content-language', kwargs={'q': '%s:blahblah' % h}),
                call('content-license', kwargs={'q': '%s:blahblah' % h}),
            ])

            mock_django_reverse.reset()

    @patch('swh.web.api.utils.reverse')
    @istest
    def enrich_content_with_hashes_and_top_level_url(self,
                                                     mock_django_reverse):
        for h in ['sha1', 'sha256', 'sha1_git']:
            # given
            mock_django_reverse.side_effect = [
                '/api/content/%s:123/' % h,
                '/api/content/%s:123/raw/' % h,
                '/api/filetype/%s:123/' % h,
                '/api/language/%s:123/' % h,
                '/api/license/%s:123/' % h,
                ]

            # when
            enriched_content = utils.enrich_content(
                {
                    'id': '123',
                    h: 'blahblah'
                },
                top_url=True
            )

            # then
            self.assertEqual(
                enriched_content,
                {
                    'id': '123',
                    h: 'blahblah',
                    'content_url': '/api/content/%s:123/' % h,
                    'data_url': '/api/content/%s:123/raw/' % h,
                    'filetype_url': '/api/filetype/%s:123/' % h,
                    'language_url': '/api/language/%s:123/' % h,
                    'license_url': '/api/license/%s:123/' % h,
                }
            )

            mock_django_reverse.assert_has_calls([
                call('content', kwargs={'q': '%s:blahblah' % h}),
                call('content-raw', kwargs={'q': '%s:blahblah' % h}),
                call('content-filetype', kwargs={'q': '%s:blahblah' % h}),
                call('content-language', kwargs={'q': '%s:blahblah' % h}),
                call('content-license', kwargs={'q': '%s:blahblah' % h}),
            ])

            mock_django_reverse.reset()

    @istest
    def enrich_entity_identity(self):
        # when/then
        self.assertEqual(utils.enrich_content({'id': '123'}),
                         {'id': '123'})

    @patch('swh.web.api.utils.reverse')
    @istest
    def enrich_entity_with_sha1(self, mock_django_reverse):
        # given
        def reverse_test(view_name, kwargs):
            return '/api/entity/' + kwargs['uuid'] + '/'

        mock_django_reverse.side_effect = reverse_test

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

        mock_django_reverse.assert_has_calls(
            [call('entity', kwargs={'uuid': 'uuid-1'}),
             call('entity', kwargs={'uuid': 'uuid-parent'})])

    @nottest
    def _reverse_context_test(self, view_name, kwargs):
        if view_name == 'revision':
            return '/api/revision/%s/' % kwargs['sha1_git']
        elif view_name == 'revision-context':
            return '/api/revision/%s/prev/%s/' % (kwargs['sha1_git'], kwargs['context'])  # noqa
        elif view_name == 'revision-log':
            if 'prev_sha1s' in kwargs:
                return '/api/revision/%s/prev/%s/log/' % (kwargs['sha1_git'], kwargs['prev_sha1s'])  # noqa
            else:
                return '/api/revision/%s/log/' % kwargs['sha1_git']

    @patch('swh.web.api.utils.reverse')
    @istest
    def enrich_revision_without_children_or_parent(self, mock_django_reverse):
        # given
        def reverse_test(view_name, kwargs):
            if view_name == 'revision':
                return '/api/revision/' + kwargs['sha1_git'] + '/'
            elif view_name == 'revision-log':
                return '/api/revision/' + kwargs['sha1_git'] + '/log/'
            elif view_name == 'directory':
                return '/api/directory/' + kwargs['sha1_git'] + '/'
            elif view_name == 'person':
                return '/api/person/' + kwargs['person_id'] + '/'

        mock_django_reverse.side_effect = reverse_test

        # when
        actual_revision = utils.enrich_revision({
            'id': 'rev-id',
            'directory': '123',
            'author': {'id': '1'},
            'committer': {'id': '2'},
        })

        expected_revision = {
            'id': 'rev-id',
            'directory': '123',
            'url': '/api/revision/rev-id/',
            'history_url': '/api/revision/rev-id/log/',
            'directory_url': '/api/directory/123/',
            'author': {'id': '1'},
            'author_url': '/api/person/1/',
            'committer': {'id': '2'},
            'committer_url': '/api/person/2/'
        }

        # then
        self.assertEqual(actual_revision, expected_revision)

        mock_django_reverse.assert_has_calls(
            [call('revision', kwargs={'sha1_git': 'rev-id'}),
             call('revision-log', kwargs={'sha1_git': 'rev-id'}),
             call('person', kwargs={'person_id': '1'}),
             call('person', kwargs={'person_id': '2'}),
             call('directory', kwargs={'sha1_git': '123'})])

    @patch('swh.web.api.utils.reverse')
    @istest
    def enrich_revision_with_children_and_parent_no_dir(self,
                                                        mock_django_reverse):
        # given
        mock_django_reverse.side_effect = self._reverse_context_test

        # when
        actual_revision = utils.enrich_revision({
            'id': 'rev-id',
            'parents': ['123'],
            'children': ['456'],
        }, context='prev-rev')

        expected_revision = {
            'id': 'rev-id',
            'url': '/api/revision/rev-id/',
            'history_url': '/api/revision/rev-id/log/',
            'history_context_url': '/api/revision/rev-id/prev/prev-rev/log/',
            'parents': [{'id': '123', 'url': '/api/revision/123/'}],
            'children': ['456'],
            'children_urls': ['/api/revision/456/',
                              '/api/revision/prev-rev/'],
        }

        # then
        self.assertEqual(actual_revision, expected_revision)

        mock_django_reverse.assert_has_calls(
            [call('revision', kwargs={'sha1_git': 'prev-rev'}),
             call('revision', kwargs={'sha1_git': 'rev-id'}),
             call('revision-log', kwargs={'sha1_git': 'rev-id'}),
             call('revision-log', kwargs={'sha1_git': 'rev-id',
                                          'prev_sha1s': 'prev-rev'}),
             call('revision', kwargs={'sha1_git': '123'}),
             call('revision', kwargs={'sha1_git': '456'})])

    @patch('swh.web.api.utils.reverse')
    @istest
    def enrich_revision_no_context(self, mock_django_reverse):
        # given
        mock_django_reverse.side_effect = self._reverse_context_test

        # when
        actual_revision = utils.enrich_revision({
            'id': 'rev-id',
            'parents': ['123'],
            'children': ['456'],
        })

        expected_revision = {
            'id': 'rev-id',
            'url': '/api/revision/rev-id/',
            'history_url': '/api/revision/rev-id/log/',
            'parents': [{'id': '123', 'url': '/api/revision/123/'}],
            'children': ['456'],
            'children_urls': ['/api/revision/456/']
        }

        # then
        self.assertEqual(actual_revision, expected_revision)

        mock_django_reverse.assert_has_calls(
            [call('revision', kwargs={'sha1_git': 'rev-id'}),
             call('revision-log', kwargs={'sha1_git': 'rev-id'}),
             call('revision', kwargs={'sha1_git': '123'}),
             call('revision', kwargs={'sha1_git': '456'})])

    @patch('swh.web.api.utils.reverse')
    @istest
    def enrich_revision_context_empty_prev_list(self, mock_django_reverse):
        # given
        mock_django_reverse.side_effect = self._reverse_context_test

        # when
        expected_revision = {
            'id': 'rev-id',
            'url': '/api/revision/rev-id/',
            'history_url': '/api/revision/rev-id/log/',
            'history_context_url': ('/api/revision/rev-id/'
                                    'prev/prev-rev/log/'),
            'parents': [{'id': '123', 'url': '/api/revision/123/'}],
            'children': ['456'],
            'children_urls': ['/api/revision/456/',
                              '/api/revision/prev-rev/'],
        }

        actual_revision = utils.enrich_revision({
            'id': 'rev-id',
            'url': '/api/revision/rev-id/',
            'parents': ['123'],
            'children': ['456']}, context='prev-rev')

        # then
        self.assertEqual(actual_revision, expected_revision)
        mock_django_reverse.assert_has_calls(
            [call('revision', kwargs={'sha1_git': 'prev-rev'}),
             call('revision', kwargs={'sha1_git': 'rev-id'}),
             call('revision-log', kwargs={'sha1_git': 'rev-id'}),
             call('revision-log', kwargs={'sha1_git': 'rev-id',
                                          'prev_sha1s': 'prev-rev'}),
             call('revision', kwargs={'sha1_git': '123'}),
             call('revision', kwargs={'sha1_git': '456'})])

    @patch('swh.web.api.utils.reverse')
    @istest
    def enrich_revision_context_some_prev_list(self, mock_django_reverse):
        # given
        mock_django_reverse.side_effect = self._reverse_context_test

        # when
        expected_revision = {
            'id': 'rev-id',
            'url': '/api/revision/rev-id/',
            'history_url': '/api/revision/rev-id/log/',
            'history_context_url': ('/api/revision/rev-id/'
                                    'prev/prev1-rev/prev0-rev/log/'),
            'parents': [{'id': '123', 'url': '/api/revision/123/'}],
            'children': ['456'],
            'children_urls': ['/api/revision/456/',
                              '/api/revision/prev0-rev/prev/prev1-rev/'],
        }

        actual_revision = utils.enrich_revision({
            'id': 'rev-id',
            'parents': ['123'],
            'children': ['456']}, context='prev1-rev/prev0-rev')

        # then
        self.assertEqual(actual_revision, expected_revision)
        mock_django_reverse.assert_has_calls(
            [call('revision-context', kwargs={'context': 'prev1-rev',
                                              'sha1_git': 'prev0-rev'}),
             call('revision', kwargs={'sha1_git': 'rev-id'}),
             call('revision-log', kwargs={'sha1_git': 'rev-id'}),
             call('revision-log', kwargs={'prev_sha1s': 'prev1-rev/prev0-rev',
                                          'sha1_git': 'rev-id'}),
             call('revision', kwargs={'sha1_git': '123'}),
             call('revision', kwargs={'sha1_git': '456'})])

    @nottest
    def _reverse_rev_message_test(self, view_name, kwargs):
        if view_name == 'revision':
            return '/api/revision/%s/' % kwargs['sha1_git']
        elif view_name == 'revision-log':
            if 'prev_sha1s' in kwargs and kwargs['prev_sha1s'] is not None:
                return '/api/revision/%s/prev/%s/log/' % (kwargs['sha1_git'], kwargs['prev_sha1s'])  # noqa
            else:
                return '/api/revision/%s/log/' % kwargs['sha1_git']
        elif view_name == 'revision-raw-message':
            return '/api/revision/' + kwargs['sha1_git'] + '/raw/'
        else:
            return '/api/revision/%s/prev/%s/' % (kwargs['sha1_git'], kwargs['context'])  # noqa

    @patch('swh.web.api.utils.reverse')
    @istest
    def enrich_revision_with_no_message(self, mock_django_reverse):
        # given
        mock_django_reverse.side_effect = self._reverse_rev_message_test

        # when
        expected_revision = {
            'id': 'rev-id',
            'url': '/api/revision/rev-id/',
            'history_url': '/api/revision/rev-id/log/',
            'history_context_url': ('/api/revision/rev-id/'
                                    'prev/prev-rev/log/'),
            'message': None,
            'parents': [{'id': '123', 'url': '/api/revision/123/'}],
            'children': ['456'],
            'children_urls': ['/api/revision/456/',
                              '/api/revision/prev-rev/'],
        }

        actual_revision = utils.enrich_revision({
            'id': 'rev-id',
            'message': None,
            'parents': ['123'],
            'children': ['456'],
        }, context='prev-rev')

        # then
        self.assertEqual(actual_revision, expected_revision)

        mock_django_reverse.assert_has_calls(
            [call('revision', kwargs={'sha1_git': 'prev-rev'}),
             call('revision', kwargs={'sha1_git': 'rev-id'}),
             call('revision-log', kwargs={'sha1_git': 'rev-id'}),
             call('revision-log', kwargs={'sha1_git': 'rev-id',
                                          'prev_sha1s': 'prev-rev'}),
             call('revision', kwargs={'sha1_git': '123'}),
             call('revision', kwargs={'sha1_git': '456'})]
        )

    @patch('swh.web.api.utils.reverse')
    @istest
    def enrich_revision_with_invalid_message(self, mock_django_reverse):
        # given
        mock_django_reverse.side_effect = self._reverse_rev_message_test

        # when
        actual_revision = utils.enrich_revision({
            'id': 'rev-id',
            'message': None,
            'message_decoding_failed': True,
            'parents': ['123'],
            'children': ['456'],
        }, context='prev-rev')

        expected_revision = {
            'id': 'rev-id',
            'url': '/api/revision/rev-id/',
            'history_url': '/api/revision/rev-id/log/',
            'history_context_url': ('/api/revision/rev-id/'
                                    'prev/prev-rev/log/'),
            'message': None,
            'message_decoding_failed': True,
            'message_url': '/api/revision/rev-id/raw/',
            'parents': [{'id': '123', 'url': '/api/revision/123/'}],
            'children': ['456'],
            'children_urls': ['/api/revision/456/',
                              '/api/revision/prev-rev/'],
        }

        # then
        self.assertEqual(actual_revision, expected_revision)

        mock_django_reverse.assert_has_calls(
            [call('revision', kwargs={'sha1_git': 'prev-rev'}),
             call('revision', kwargs={'sha1_git': 'rev-id'}),
             call('revision-log', kwargs={'sha1_git': 'rev-id'}),
             call('revision-log', kwargs={'sha1_git': 'rev-id',
                                          'prev_sha1s': 'prev-rev'}),
             call('revision', kwargs={'sha1_git': '123'}),
             call('revision', kwargs={'sha1_git': '456'}),
             call('revision-raw-message', kwargs={'sha1_git': 'rev-id'})])
