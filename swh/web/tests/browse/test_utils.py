# Copyright (C) 2017-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

# flake8: noqa

from unittest.mock import patch

from swh.web.browse import utils
from swh.web.common.exc import NotFoundExc
from swh.web.common.utils import reverse
from swh.web.tests.testcase import SWHWebTestCase

from .views.data.revision_test_data import revision_history_log_test


class SwhBrowseUtilsTestCase(SWHWebTestCase):

    def test_get_mimetype_and_encoding_for_content(self):
        text = b'Hello world!'
        self.assertEqual(utils.get_mimetype_and_encoding_for_content(text),
                         ('text/plain', 'us-ascii'))

    @patch('swh.web.browse.utils.get_origin_visits')
    def test_get_origin_visit(self, mock_origin_visits):
        origin_info = {
            'id': 2,
            'type': 'git',
            'url': 'https://github.com/foo/bar',
        }
        visits = \
            [{'status': 'full',
              'date': '2015-07-09T21:09:24+00:00',
              'visit': 1,
              'origin': origin_info['id']
              },
             {'status': 'full',
              'date': '2016-02-23T18:05:23.312045+00:00',
              'visit': 2,
              'origin': origin_info['id']
              },
             {'status': 'full',
              'date': '2016-03-28T01:35:06.554111+00:00',
              'visit': 3,
              'origin': origin_info['id']
              },
             {'status': 'full',
              'date': '2016-06-18T01:22:24.808485+00:00',
              'visit': 4,
              'origin': origin_info['id']
              },
             {'status': 'full',
              'date': '2016-08-14T12:10:00.536702+00:00',
              'visit': 5,
              'origin': origin_info['id']
              }]
        mock_origin_visits.return_value = visits

        visit_id = 12
        with self.assertRaises(NotFoundExc) as cm:
            visit = utils.get_origin_visit(origin_info,
                                           visit_id=visit_id)
        exception_text = cm.exception.args[0]
        self.assertIn('Visit with id %s' % visit_id, exception_text)
        self.assertIn('type %s' % origin_info['type'], exception_text)
        self.assertIn('url %s' % origin_info['url'], exception_text)

        visit = utils.get_origin_visit(origin_info, visit_id=2)
        self.assertEqual(visit, visits[1])

        visit = utils.get_origin_visit(
            origin_info, visit_ts='2016-02-23T18:05:23.312045+00:00')
        self.assertEqual(visit, visits[1])

        visit = utils.get_origin_visit(
            origin_info, visit_ts='2016-02-20')
        self.assertEqual(visit, visits[1])

        visit = utils.get_origin_visit(
            origin_info, visit_ts='2016-06-18T01:22')
        self.assertEqual(visit, visits[3])

        visit = utils.get_origin_visit(
            origin_info, visit_ts='2016-06-18 01:22')
        self.assertEqual(visit, visits[3])

        visit = utils.get_origin_visit(
            origin_info, visit_ts=1466208000)
        self.assertEqual(visit, visits[3])

        visit = utils.get_origin_visit(
            origin_info, visit_ts='2014-01-01')
        self.assertEqual(visit, visits[0])

        visit = utils.get_origin_visit(
            origin_info, visit_ts='2018-01-01')
        self.assertEqual(visit, visits[-1])

    @patch('swh.web.browse.utils.service')
    @patch('swh.web.browse.utils.get_origin_visit')
    def test_get_origin_visit_snapshot(self, mock_get_origin_visit,
                                  mock_service):

        mock_get_origin_visit.return_value = \
            {'status': 'full',
             'date': '2015-08-04T22:26:14.804009+00:00',
             'visit': 1,
             'origin': 1,
             'snapshot': '584b2fe3ce6218a96892e73bd76c2966bbc2a797'}

        mock_service.lookup_snapshot.return_value = \
            {'branches': {
                 'HEAD': {
                     'target': '9fbd21adbac36be869514e82e2e98505dc47219c',
                     'target_type': 'revision',
                     'target_url': '/api/1/revision/9fbd21adbac36be869514e82e2e98505dc47219c/'
                 },
                 'refs/heads/master': {
                     'target': '9fbd21adbac36be869514e82e2e98505dc47219c',
                     'target_type': 'revision',
                     'target_url': '/api/1/revision/9fbd21adbac36be869514e82e2e98505dc47219c/'
                 },
                 'refs/tags/0.10.0': {
                     'target': '7045404f3d1c54e6473c71bbb716529fbad4be24',
                     'target_type': 'release',
                     'target_url': '/api/1/release/7045404f3d1c54e6473c71bbb716529fbad4be24/'
                 },
                 'refs/tags/0.10.1': {
                     'target': 'c893f4549c367e68288b0eb74595050410aa0de7',
                     'target_type': 'release',
                     'target_url': '/api/1/release/c893f4549c367e68288b0eb74595050410aa0de7/'
                 }
             },
             'id': '584b2fe3ce6218a96892e73bd76c2966bbc2a797'}

        mock_service.lookup_release_multiple.return_value = \
            [{'name': '0.10.0',
              'message': '0.10: The "Oh fuck it\'s PyCon" release\n',
              'id': '7045404f3d1c54e6473c71bbb716529fbad4be24',
              'date': '2014-04-10T23:01:28-04:00',
              'target_type': 'revision',
              'target': '6072557b6c10cd9a21145781e26ad1f978ed14b9'},
             {'name': '0.10.1',
              'message': 'Tagging 0.10.1\n',
              'id': 'c893f4549c367e68288b0eb74595050410aa0de7',
              'date': '2014-10-10T09:45:52-04:00',
              'target_type': 'revision',
              'target': 'ecc003b43433e5b46511157598e4857a761007bf'}]

        mock_service.lookup_revision_multiple.return_value = \
            [{'date': '2015-08-04T13:16:54+03:00',
              'directory': '828da2b80e41aa958b2c98526f4a1d2cc7d298b7',
              'id': '9fbd21adbac36be869514e82e2e98505dc47219c',
              'message': 'Merge pull request #678 from algernon'},
             {'date': '2014-04-10T23:01:11-04:00',
              'directory': '2df4cd84ecc65b50b1d5318d3727e02a39b8a4cf',
              'id': '6072557b6c10cd9a21145781e26ad1f978ed14b9',
              'message': '0.10: The "Oh fuck it\'s PyCon" release\n'},
             {'date': '2014-10-10T09:45:23-04:00',
              'directory': '28ba64f97ef709e54838ae482c2da2619a74a0bd',
              'id': 'ecc003b43433e5b46511157598e4857a761007bf',
              'message': '0.10.1\n'}]

        expected_result = (
            [{'name': 'HEAD',
              'message': 'Merge pull request #678 from algernon',
              'date': '04 August 2015, 10:16 UTC',
              'revision': '9fbd21adbac36be869514e82e2e98505dc47219c',
              'directory': '828da2b80e41aa958b2c98526f4a1d2cc7d298b7'},
             {'name': 'refs/heads/master',
              'message': 'Merge pull request #678 from algernon',
              'date': '04 August 2015, 10:16 UTC',
              'revision': '9fbd21adbac36be869514e82e2e98505dc47219c',
              'directory': '828da2b80e41aa958b2c98526f4a1d2cc7d298b7'}],
            [{'name': '0.10.0',
              'branch_name': 'refs/tags/0.10.0',
              'id': '7045404f3d1c54e6473c71bbb716529fbad4be24',
              'message': '0.10: The "Oh fuck it\'s PyCon" release\n',
              'date': '11 April 2014, 03:01 UTC',
              'target_type': 'revision',
              'target': '6072557b6c10cd9a21145781e26ad1f978ed14b9',
              'directory': '2df4cd84ecc65b50b1d5318d3727e02a39b8a4cf'},
             {'name': '0.10.1',
              'branch_name': 'refs/tags/0.10.1',
              'id': 'c893f4549c367e68288b0eb74595050410aa0de7',
              'message': 'Tagging 0.10.1\n',
              'date': '10 October 2014, 13:45 UTC',
              'target_type': 'revision',
              'target': 'ecc003b43433e5b46511157598e4857a761007bf',
              'directory': '28ba64f97ef709e54838ae482c2da2619a74a0bd'}]
        )

        origin_info = {
            'id': 1,
            'type': 'git',
            'url': 'https://github.com/hylang/hy'
        }

        origin_visit_branches = \
            utils.get_origin_visit_snapshot(origin_info, visit_id=1)

        lookup_release_calls = mock_service.lookup_release_multiple.call_args_list
        self.assertEqual(len(lookup_release_calls), 1)

        # Check that we looked up the two expected releases
        self.assertCountEqual(set(lookup_release_calls[0][0][0]), {
            '7045404f3d1c54e6473c71bbb716529fbad4be24',
            'c893f4549c367e68288b0eb74595050410aa0de7',
        })

        lookup_revision_calls = mock_service.lookup_revision_multiple.call_args_list
        self.assertEqual(len(lookup_revision_calls), 1)

        # Check that we looked up the three expected revisions
        self.assertCountEqual(set(lookup_revision_calls[0][0][0]), {
            '9fbd21adbac36be869514e82e2e98505dc47219c',
            '6072557b6c10cd9a21145781e26ad1f978ed14b9',
            'ecc003b43433e5b46511157598e4857a761007bf',
        })

        self.assertEqual(origin_visit_branches, expected_result)

    def test_gen_link(self):
        self.assertEqual(utils.gen_link('https://www.softwareheritage.org/', 'swh'),
                         '<a href="https://www.softwareheritage.org/">swh</a>')

    def test_gen_person_link(self):
        person_id = 8221896
        person_name = 'Antoine Lambert'
        person_url = reverse('browse-person', url_args={'person_id': person_id})

        self.assertEqual(utils.gen_person_link(person_id, person_name),
                         '<a href="%s">%s</a>' % (person_url, person_name))

    def test_gen_revision_link(self):
        revision_id = '28a0bc4120d38a394499382ba21d6965a67a3703'
        revision_url = reverse('browse-revision',
                               url_args={'sha1_git': revision_id})

        self.assertEqual(utils.gen_revision_link(revision_id),
                         '<a href="%s">%s</a>' % (revision_url, revision_id))
        self.assertEqual(utils.gen_revision_link(revision_id, shorten_id=True),
                         '<a href="%s">%s</a>' % (revision_url, revision_id[:7]))
