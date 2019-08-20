# Copyright (C) 2015-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from unittest.mock import patch, call

from swh.web.api import utils
from swh.web.tests.testcase import WebTestCase


class UtilsTestCase(WebTestCase):
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
        self.sample_content_hashes = {
            'blake2s256': ('791e07fcea240ade6dccd0a9309141673'
                           'c31242cae9c237cf3855e151abc78e9'),
            'sha1': 'dc2830a9e72f23c1dfebef4413003221baa5fb62',
            'sha1_git': 'fe95a46679d128ff167b7c55df5d02356c5a1ae1',
            'sha256': ('b5c7fe0536f44ef60c8780b6065d30bca74a5cd06'
                       'd78a4a71ba1ad064770f0c9')
        }

    def test_filter_field_keys_dict_unknown_keys(self):
        # when
        actual_res = utils.filter_field_keys(
            {'directory': 1, 'file': 2, 'link': 3},
            {'directory1', 'file2'})

        # then
        self.assertEqual(actual_res, {})

    def test_filter_field_keys_dict(self):
        # when
        actual_res = utils.filter_field_keys(
            {'directory': 1, 'file': 2, 'link': 3},
            {'directory', 'link'})

        # then
        self.assertEqual(actual_res, {'directory': 1, 'link': 3})

    def test_filter_field_keys_list_unknown_keys(self):
        # when
        actual_res = utils.filter_field_keys(
            [{'directory': 1, 'file': 2, 'link': 3},
             {'1': 1, '2': 2, 'link': 3}],
            {'d'})

        # then
        self.assertEqual(actual_res, [{}, {}])

    def test_filter_field_keys_map(self):
        # when
        actual_res = utils.filter_field_keys(
            map(lambda x: {'i': x['i']+1, 'j': x['j']},
                [{'i': 1, 'j': None},
                 {'i': 2, 'j': None},
                 {'i': 3, 'j': None}]),
            {'i'})

        # then
        self.assertEqual(list(actual_res), [{'i': 2}, {'i': 3}, {'i': 4}])

    def test_filter_field_keys_list(self):
        # when
        actual_res = utils.filter_field_keys(
            [{'directory': 1, 'file': 2, 'link': 3},
             {'dir': 1, 'fil': 2, 'lin': 3}],
            {'directory', 'dir'})

        # then
        self.assertEqual(actual_res, [{'directory': 1}, {'dir': 1}])

    def test_filter_field_keys_other(self):
        # given
        input_set = {1, 2}

        # when
        actual_res = utils.filter_field_keys(input_set, {'a', '1'})

        # then
        self.assertEqual(actual_res, input_set)

    def test_person_to_string(self):
        self.assertEqual(utils.person_to_string(dict(name='raboof',
                                                     email='foo@bar')),
                         'raboof <foo@bar>')

    def test_enrich_release_0(self):
        # when
        actual_release = utils.enrich_release({})

        # then
        self.assertEqual(actual_release, {})

    @patch('swh.web.api.utils.reverse')
    def test_enrich_release_1(self, mock_django_reverse):
        # given

        def reverse_test_context(view_name, url_args):
            if view_name == 'api-1-content':
                id = url_args['q']
                return '/api/1/content/%s/' % id
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
            'author': {
                'id': 100,
                'name': 'author release name',
                'email': 'author@email',
            },
        })

        mock_django_reverse.assert_has_calls([
                call('api-1-content', url_args={'q': 'sha1_git:123'}),
        ])

    @patch('swh.web.api.utils.reverse')
    def test_enrich_release_2(self, mock_django_reverse):
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

        mock_django_reverse.assert_called_once_with('api-1-directory',
                                                    url_args={'sha1_git': '23'}) # noqa

    @patch('swh.web.api.utils.reverse')
    def test_enrich_release_3(self, mock_django_reverse):
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

        mock_django_reverse.assert_called_once_with('api-1-revision',
                                                    url_args={'sha1_git': '3'})

    @patch('swh.web.api.utils.reverse')
    def test_enrich_release_4(self, mock_django_reverse):
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

        mock_django_reverse.assert_called_once_with('api-1-release',
                                                    url_args={'sha1_git': '4'})

    @patch('swh.web.api.utils.reverse')
    def test_enrich_directory_no_type(self, mock_django_reverse):
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
            'api-1-content', url_args={'q': 'sha1_git:123'})

    @patch('swh.web.api.utils.reverse')
    def test_enrich_directory_with_context_and_type_file(
        self, mock_django_reverse,
    ):
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
            'api-1-content', url_args={'q': 'sha1_git:789'})

    @patch('swh.web.api.utils.reverse')
    def test_enrich_directory_with_context_and_type_dir(
        self, mock_django_reverse,
    ):
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

        mock_django_reverse.assert_called_once_with('api-1-directory',
                                                    url_args={'sha1_git': '456'}) # noqa

    def test_enrich_content_without_hashes(self):
        # when/then
        self.assertEqual(utils.enrich_content({'id': '123'}),
                         {'id': '123'})

    @patch('swh.web.api.utils.reverse')
    def test_enrich_content_with_hashes(self, mock_django_reverse):

        for algo, hash in self.sample_content_hashes.items():

            query_string = '%s:%s' % (algo, hash)

            # given
            mock_django_reverse.side_effect = [
                '/api/content/%s/raw/' % query_string,
                '/api/filetype/%s/' % query_string,
                '/api/language/%s/' % query_string,
                '/api/license/%s/' % query_string
                ]

            # when
            enriched_content = utils.enrich_content(
                {
                    algo: hash,
                },
                query_string=query_string
            )

            # then
            self.assertEqual(
                enriched_content,
                {
                    algo: hash,
                    'data_url': '/api/content/%s/raw/' % query_string,
                    'filetype_url': '/api/filetype/%s/' % query_string,
                    'language_url': '/api/language/%s/' % query_string,
                    'license_url': '/api/license/%s/' % query_string,
                }
            )

            mock_django_reverse.assert_has_calls([
                call('api-1-content-raw', url_args={'q': query_string}),
                call('api-1-content-filetype', url_args={'q': query_string}),
                call('api-1-content-language', url_args={'q': query_string}),
                call('api-1-content-license', url_args={'q': query_string}),
            ])

            mock_django_reverse.reset()

    @patch('swh.web.api.utils.reverse')
    def test_enrich_content_with_hashes_and_top_level_url(self,
                                                          mock_django_reverse):

        for algo, hash in self.sample_content_hashes.items():

            query_string = '%s:%s' % (algo, hash)

            # given
            mock_django_reverse.side_effect = [
                '/api/content/%s/' % query_string,
                '/api/content/%s/raw/' % query_string,
                '/api/filetype/%s/' % query_string,
                '/api/language/%s/' % query_string,
                '/api/license/%s/' % query_string,
                ]

            # when
            enriched_content = utils.enrich_content(
                {
                    algo: hash
                },
                top_url=True,
                query_string=query_string
            )

            # then
            self.assertEqual(
                enriched_content,
                {
                    algo: hash,
                    'content_url': '/api/content/%s/' % query_string,
                    'data_url': '/api/content/%s/raw/' % query_string,
                    'filetype_url': '/api/filetype/%s/' % query_string,
                    'language_url': '/api/language/%s/' % query_string,
                    'license_url': '/api/license/%s/' % query_string,
                }
            )

            mock_django_reverse.assert_has_calls([
                call('api-1-content', url_args={'q': query_string}),
                call('api-1-content-raw', url_args={'q': query_string}),
                call('api-1-content-filetype', url_args={'q': query_string}),
                call('api-1-content-language', url_args={'q': query_string}),
                call('api-1-content-license', url_args={'q': query_string}),
            ])

            mock_django_reverse.reset()

    def _reverse_context_test(self, view_name, url_args):
        if view_name == 'api-1-revision':
            return '/api/revision/%s/' % url_args['sha1_git']
        elif view_name == 'api-1-revision-context':
            return '/api/revision/%s/prev/%s/' % (url_args['sha1_git'], url_args['context'])  # noqa
        elif view_name == 'api-1-revision-log':
            if 'prev_sha1s' in url_args:
                return '/api/revision/%s/prev/%s/log/' % (url_args['sha1_git'], url_args['prev_sha1s'])  # noqa
            else:
                return '/api/revision/%s/log/' % url_args['sha1_git']

    @patch('swh.web.api.utils.reverse')
    def test_enrich_revision_without_children_or_parent(
        self, mock_django_reverse,
    ):
        # given
        def reverse_test(view_name, url_args):
            if view_name == 'api-1-revision':
                return '/api/revision/' + url_args['sha1_git'] + '/'
            elif view_name == 'api-1-revision-log':
                return '/api/revision/' + url_args['sha1_git'] + '/log/'
            elif view_name == 'api-1-directory':
                return '/api/directory/' + url_args['sha1_git'] + '/'

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
            'committer': {'id': '2'},
        }

        # then
        self.assertEqual(actual_revision, expected_revision)

        mock_django_reverse.assert_has_calls(
            [call('api-1-revision', url_args={'sha1_git': 'rev-id'}),
             call('api-1-revision-log', url_args={'sha1_git': 'rev-id'}),
             call('api-1-directory', url_args={'sha1_git': '123'})])

    @patch('swh.web.api.utils.reverse')
    def test_enrich_revision_with_children_and_parent_no_dir(
        self, mock_django_reverse,
    ):
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
            'children_urls': ['/api/revision/456/'],
        }

        # then
        self.assertEqual(actual_revision, expected_revision)

        mock_django_reverse.assert_has_calls(
            [call('api-1-revision', url_args={'sha1_git': 'rev-id'}),
             call('api-1-revision-log', url_args={'sha1_git': 'rev-id'}),
             call('api-1-revision', url_args={'sha1_git': '123'}),
             call('api-1-revision', url_args={'sha1_git': '456'})])

    @patch('swh.web.api.utils.reverse')
    def test_enrich_revision_no_context(self, mock_django_reverse):
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
            [call('api-1-revision', url_args={'sha1_git': 'rev-id'}),
             call('api-1-revision-log', url_args={'sha1_git': 'rev-id'}),
             call('api-1-revision', url_args={'sha1_git': '123'}),
             call('api-1-revision', url_args={'sha1_git': '456'})])

    def _reverse_rev_message_test(self, view_name, url_args):
        if view_name == 'api-1-revision':
            return '/api/revision/%s/' % url_args['sha1_git']
        elif view_name == 'api-1-revision-log':
            if 'prev_sha1s' in url_args and url_args['prev_sha1s'] is not None:
                return '/api/revision/%s/prev/%s/log/' % (url_args['sha1_git'], url_args['prev_sha1s'])  # noqa
            else:
                return '/api/revision/%s/log/' % url_args['sha1_git']
        elif view_name == 'api-1-revision-raw-message':
            return '/api/revision/' + url_args['sha1_git'] + '/raw/'
        else:
            return '/api/revision/%s/prev/%s/' % (url_args['sha1_git'], url_args['context'])  # noqa

    @patch('swh.web.api.utils.reverse')
    def test_enrich_revision_with_no_message(self, mock_django_reverse):
        # given
        mock_django_reverse.side_effect = self._reverse_rev_message_test

        # when
        expected_revision = {
            'id': 'rev-id',
            'url': '/api/revision/rev-id/',
            'history_url': '/api/revision/rev-id/log/',
            'message': None,
            'parents': [{'id': '123', 'url': '/api/revision/123/'}],
            'children': ['456'],
            'children_urls': ['/api/revision/456/'],
        }

        actual_revision = utils.enrich_revision({
            'id': 'rev-id',
            'message': None,
            'parents': ['123'],
            'children': ['456'],
        })

        # then
        self.assertEqual(actual_revision, expected_revision)

        mock_django_reverse.assert_has_calls(
            [call('api-1-revision', url_args={'sha1_git': 'rev-id'}),
             call('api-1-revision-log', url_args={'sha1_git': 'rev-id'}),
             call('api-1-revision', url_args={'sha1_git': '123'}),
             call('api-1-revision', url_args={'sha1_git': '456'})]
        )

    @patch('swh.web.api.utils.reverse')
    def test_enrich_revision_with_invalid_message(self, mock_django_reverse):
        # given
        mock_django_reverse.side_effect = self._reverse_rev_message_test

        # when
        actual_revision = utils.enrich_revision({
            'id': 'rev-id',
            'message': None,
            'message_decoding_failed': True,
            'parents': ['123'],
            'children': ['456'],
        })

        expected_revision = {
            'id': 'rev-id',
            'url': '/api/revision/rev-id/',
            'history_url': '/api/revision/rev-id/log/',
            'message': None,
            'message_decoding_failed': True,
            'message_url': '/api/revision/rev-id/raw/',
            'parents': [{'id': '123', 'url': '/api/revision/123/'}],
            'children': ['456'],
            'children_urls': ['/api/revision/456/'],
        }

        # then
        self.assertEqual(actual_revision, expected_revision)

        mock_django_reverse.assert_has_calls(
            [call('api-1-revision', url_args={'sha1_git': 'rev-id'}),
             call('api-1-revision-log', url_args={'sha1_git': 'rev-id'}),
             call('api-1-revision', url_args={'sha1_git': '123'}),
             call('api-1-revision', url_args={'sha1_git': '456'}),
             call('api-1-revision-raw-message', url_args={'sha1_git': 'rev-id'})]) # noqa
