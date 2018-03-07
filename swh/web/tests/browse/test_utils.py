# Copyright (C) 2017-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

# flake8: noqa

import unittest

from unittest.mock import patch
from nose.tools import istest


from swh.web.browse import utils
from swh.web.common.exc import NotFoundExc
from swh.web.common.utils import reverse
from swh.web.tests.testbase import SWHWebTestBase

from .views.data.revision_test_data import revision_history_log_test


class SwhBrowseUtilsTestCase(SWHWebTestBase, unittest.TestCase):

    @istest
    def get_mimetype_and_encoding_for_content(self):
        text = b'Hello world!'
        self.assertEqual(utils.get_mimetype_and_encoding_for_content(text),
                         ('text/plain', 'us-ascii'))

    @patch('swh.web.browse.utils.service')
    @istest
    def get_origin_visits(self, mock_service):
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

    @patch('swh.web.browse.utils.get_origin_visits')
    @istest
    def get_origin_visit(self, mock_origin_visits):
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

        with self.assertRaises(NotFoundExc) as cm:
            visit_id = 12
            visit = utils.get_origin_visit(origin_info,
                                           visit_id=visit_id)
            self.assertIn('Visit with id %s for origin with id %s not found' %
                          (origin_info['id'], visit_id),
                          cm.exception.args[0])

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
    @istest
    def get_origin_visit_snapshot(self, mock_get_origin_visit,
                                  mock_service):

        mock_get_origin_visit.return_value = \
            {'status': 'full',
             'date': '2015-08-04T22:26:14.804009+00:00',
             'visit': 1,
             'origin': 1,
             'snapshot': '584b2fe3ce6218a96892e73bd76c2966bbc2a797'}

        mock_service.lookup_snapshot.return_value = \
            {'branches': {
                 'refs/heads/master': {
                     'target': '9fbd21adbac36be869514e82e2e98505dc47219c',
                     'target_type': 'revision',
                     'target_url': '/api/1/revision/9fbd21adbac36be869514e82e2e98505dc47219c/'
                 },
                 'refs/tags/0.10.0': {
                     'target': '6072557b6c10cd9a21145781e26ad1f978ed14b9',
                     'target_type': 'release',
                     'target_url': '/api/1/release/6072557b6c10cd9a21145781e26ad1f978ed14b9/'
                 },
                 'refs/tags/0.10.1': {
                     'target': 'ecc003b43433e5b46511157598e4857a761007bf',
                     'target_type': 'release',
                     'target_url': '/api/1/release/ecc003b43433e5b46511157598e4857a761007bf/'
                 }
             },
             'id': '584b2fe3ce6218a96892e73bd76c2966bbc2a797'}

        mock_service.lookup_release_multiple.return_value = \
            [{'name': '0.10.0',
              'message': 'release 0.10.0',
              'id': '6072557b6c10cd9a21145781e26ad1f978ed14b9',
              'date': '2015-08-04T13:16:54+03:00',
              'target_type': 'revision',
              'target': 'e9c6243371087d04848b7686888f6dd29dfaef0e'},
             {'name': '0.10.1',
              'message': 'release 0.10.1',
              'id': 'ecc003b43433e5b46511157598e4857a761007bf',
              'date': '2017-08-04T13:16:54+03:00',
              'target_type': 'revision',
              'target': '6072557b6c10cd9a21145781e26ad1f978ed14b9'}]

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
            [{'name': 'refs/heads/master',
              'message': 'Merge pull request #678 from algernon',
              'date': '04 August 2015, 10:16 UTC',
              'revision': '9fbd21adbac36be869514e82e2e98505dc47219c',
              'directory': '828da2b80e41aa958b2c98526f4a1d2cc7d298b7'}],
            [{'name': '0.10.0',
              'id': '6072557b6c10cd9a21145781e26ad1f978ed14b9',
              'message': 'release 0.10.0',
              'date': '04 August 2015, 10:16 UTC',
              'target_type': 'revision',
              'target': 'e9c6243371087d04848b7686888f6dd29dfaef0e',
              'directory': '2df4cd84ecc65b50b1d5318d3727e02a39b8a4cf'},
             {'name': '0.10.1',
              'id': 'ecc003b43433e5b46511157598e4857a761007bf',
              'message': 'release 0.10.1',
              'date': '04 August 2017, 10:16 UTC',
              'target_type': 'revision',
              'target': '6072557b6c10cd9a21145781e26ad1f978ed14b9',
              'directory': '28ba64f97ef709e54838ae482c2da2619a74a0bd'}]
        )

        origin_info = {
            'id': 1,
            'type': 'git',
            'url': 'https://github.com/hylang/hy'
        }

        origin_visit_branches = \
            utils.get_origin_visit_snapshot(origin_info, visit_id=1)

        self.assertEqual(origin_visit_branches, expected_result)

    @istest
    def gen_link(self):
        self.assertEqual(utils.gen_link('https://www.softwareheritage.org/', 'SWH'),
                         '<a href="https://www.softwareheritage.org/">SWH</a>')

    @istest
    def gen_person_link(self):
        person_id = 8221896
        person_name = 'Antoine Lambert'
        person_url = reverse('browse-person', kwargs={'person_id': person_id})

        self.assertEqual(utils.gen_person_link(person_id, person_name),
                         '<a href="%s">%s</a>' % (person_url, person_name))

    @istest
    def gen_revision_link(self):
        revision_id = '28a0bc4120d38a394499382ba21d6965a67a3703'
        revision_url = reverse('browse-revision',
                               kwargs={'sha1_git': revision_id})

        self.assertEqual(utils.gen_revision_link(revision_id),
                         '<a href="%s">%s</a>' % (revision_url, revision_id))
        self.assertEqual(utils.gen_revision_link(revision_id, shorten_id=True),
                         '<a href="%s">%s</a>' % (revision_url, revision_id[:7]))

    @istest
    def prepare_revision_log_for_display_no_contex(self):
        per_page = 10
        first_page_logs_data = revision_history_log_test[:per_page+1]
        second_page_logs_data = revision_history_log_test[per_page:2*per_page+1]
        third_page_logs_data = revision_history_log_test[2*per_page:3*per_page+1]
        last_page_logs_data = revision_history_log_test[3*per_page:3*per_page+5]

        revision_log_display_data = utils.prepare_revision_log_for_display(
            first_page_logs_data, per_page, None)

        self.assertEqual(revision_log_display_data['revision_log_data'],
                         utils._format_log_entries(first_page_logs_data,
                                                   per_page))

        self.assertEqual(revision_log_display_data['prev_rev'],
                         first_page_logs_data[-1]['id'])

        self.assertEqual(revision_log_display_data['prev_revs_breadcrumb'],
                         first_page_logs_data[0]['id'])

        self.assertEqual(revision_log_display_data['next_rev'], None)
        self.assertEqual(revision_log_display_data['next_revs_breadcrumb'],
                         None)

        old_prev_revs_bc = str(revision_log_display_data['prev_revs_breadcrumb'])

        revision_log_display_data = utils.prepare_revision_log_for_display(
            second_page_logs_data, per_page, old_prev_revs_bc)

        self.assertEqual(revision_log_display_data['revision_log_data'],
                         utils._format_log_entries(second_page_logs_data,
                                                   per_page))

        self.assertEqual(revision_log_display_data['prev_rev'],
                         second_page_logs_data[-1]['id'])

        self.assertEqual(revision_log_display_data['prev_revs_breadcrumb'],
                         old_prev_revs_bc + '/' + second_page_logs_data[0]['id'])

        self.assertEqual(revision_log_display_data['next_rev'],
                         old_prev_revs_bc)
        self.assertEqual(revision_log_display_data['next_revs_breadcrumb'],
                         None)

        old_prev_revs_bc = str(revision_log_display_data['prev_revs_breadcrumb'])

        revision_log_display_data = utils.prepare_revision_log_for_display(
            third_page_logs_data, per_page, old_prev_revs_bc)

        self.assertEqual(revision_log_display_data['revision_log_data'],
                         utils._format_log_entries(third_page_logs_data, per_page))

        self.assertEqual(revision_log_display_data['prev_rev'],
                         third_page_logs_data[-1]['id'])

        self.assertEqual(revision_log_display_data['prev_revs_breadcrumb'],
                         old_prev_revs_bc + '/' + third_page_logs_data[0]['id'])

        self.assertEqual(revision_log_display_data['next_rev'],
                         old_prev_revs_bc.split('/')[-1])

        self.assertEqual(revision_log_display_data['next_revs_breadcrumb'],
                         '/'.join(old_prev_revs_bc.split('/')[:-1]))

        old_prev_revs_bc = str(revision_log_display_data['prev_revs_breadcrumb'])

        revision_log_display_data = utils.prepare_revision_log_for_display(
            last_page_logs_data, per_page, old_prev_revs_bc)

        self.assertEqual(revision_log_display_data['revision_log_data'],
                         utils._format_log_entries(last_page_logs_data, per_page))

        self.assertEqual(revision_log_display_data['prev_rev'],
                         None)

        self.assertEqual(revision_log_display_data['prev_revs_breadcrumb'],
                         None)

        self.assertEqual(revision_log_display_data['next_rev'], old_prev_revs_bc.split('/')[-1])
        self.assertEqual(revision_log_display_data['next_revs_breadcrumb'],
                         '/'.join(old_prev_revs_bc.split('/')[:-1]))

    @istest
    def prepare_revision_log_for_display_snapshot_context(self):
        per_page = 10
        first_page_logs_data = revision_history_log_test[:per_page+1]
        second_page_logs_data = revision_history_log_test[per_page:2*per_page+1]
        third_page_logs_data = revision_history_log_test[2*per_page:3*per_page+1]
        last_page_logs_data = revision_history_log_test[3*per_page:3*per_page+5]

        snapshot_context = {
            'origin_info': {'type': 'git',
                            'url': 'https://github.com/git/git'},
            'url_args': {},
            'query_params': {}
        }

        revision_log_display_data = utils.prepare_revision_log_for_display(
            first_page_logs_data, per_page, None, snapshot_context=snapshot_context)

        self.assertEqual(revision_log_display_data['revision_log_data'],
                         utils._format_log_entries(first_page_logs_data,
                                                   per_page, snapshot_context=snapshot_context))

        self.assertEqual(revision_log_display_data['prev_rev'],
                         first_page_logs_data[-1]['id'])

        self.assertEqual(revision_log_display_data['prev_revs_breadcrumb'],
                         first_page_logs_data[-1]['id'])

        self.assertEqual(revision_log_display_data['next_rev'], None)
        self.assertEqual(revision_log_display_data['next_revs_breadcrumb'],
                         None)

        old_prev_revs_bc = str(revision_log_display_data['prev_revs_breadcrumb'])

        revision_log_display_data = utils.prepare_revision_log_for_display(
            second_page_logs_data, per_page, old_prev_revs_bc, snapshot_context=snapshot_context)

        self.assertEqual(revision_log_display_data['revision_log_data'],
                         utils._format_log_entries(second_page_logs_data,
                                                   per_page, snapshot_context=snapshot_context))

        self.assertEqual(revision_log_display_data['prev_rev'],
                         second_page_logs_data[-1]['id'])

        self.assertEqual(revision_log_display_data['prev_revs_breadcrumb'],
                         old_prev_revs_bc + '/' + second_page_logs_data[-1]['id'])

        self.assertEqual(revision_log_display_data['next_rev'],
                         old_prev_revs_bc)
        self.assertEqual(revision_log_display_data['next_revs_breadcrumb'],
                         None)

        old_prev_revs_bc = str(revision_log_display_data['prev_revs_breadcrumb'])

        revision_log_display_data = utils.prepare_revision_log_for_display(
            third_page_logs_data, per_page, old_prev_revs_bc, snapshot_context=snapshot_context)

        self.assertEqual(revision_log_display_data['revision_log_data'],
                         utils._format_log_entries(third_page_logs_data, per_page,
                                                   snapshot_context=snapshot_context))

        self.assertEqual(revision_log_display_data['prev_rev'],
                         third_page_logs_data[-1]['id'])

        self.assertEqual(revision_log_display_data['prev_revs_breadcrumb'],
                         old_prev_revs_bc + '/' + third_page_logs_data[-1]['id'])

        self.assertEqual(revision_log_display_data['next_rev'],
                         old_prev_revs_bc.split('/')[-1])

        self.assertEqual(revision_log_display_data['next_revs_breadcrumb'],
                         '/'.join(old_prev_revs_bc.split('/')[:-1]))

        old_prev_revs_bc = str(revision_log_display_data['prev_revs_breadcrumb'])

        revision_log_display_data = utils.prepare_revision_log_for_display(
            last_page_logs_data, per_page, old_prev_revs_bc, snapshot_context=snapshot_context)

        self.assertEqual(revision_log_display_data['revision_log_data'],
                         utils._format_log_entries(last_page_logs_data, per_page,
                                                   snapshot_context=snapshot_context))

        self.assertEqual(revision_log_display_data['prev_rev'],
                         None)

        self.assertEqual(revision_log_display_data['prev_revs_breadcrumb'],
                         None)

        self.assertEqual(revision_log_display_data['next_rev'], old_prev_revs_bc.split('/')[-1])
        self.assertEqual(revision_log_display_data['next_revs_breadcrumb'],
                         '/'.join(old_prev_revs_bc.split('/')[:-1]))
