# Copyright (C) 2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import unittest

from unittest.mock import patch
from nose.tools import istest


from swh.web.browse import utils
from swh.web.common.utils import reverse
from swh.web.tests.testbase import SWHWebTestBase

from .views.data.revision_test_data import revision_history_log_test


class SwhBrowseUtilsTestCase(SWHWebTestBase, unittest.TestCase):

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
                return [{'visit': 1}, {'visit': 2}]
            else:
                return [{'visit': 3}]

        mock_service.lookup_origin_visits.side_effect = _lookup_origin_visits

        origin_visits = utils.get_origin_visits(1)

        self.assertEqual(len(origin_visits), 3)

    @patch('swh.web.browse.utils.service')
    @istest
    def test_get_origin_visit_branches(self, mock_service):

        mock_service.lookup_origin_visit.return_value = \
            {'date': '2015-08-04T22:26:14.804009+00:00',
             'metadata': {},
             'occurrences': {
                 'refs/heads/master': {
                     'target': '9fbd21adbac36be869514e82e2e98505dc47219c',
                     'target_type': 'revision',
                     'target_url': '/api/1/revision/9fbd21adbac36be869514e82e2e98505dc47219c/' # noqa
                 },
                 'refs/tags/0.10.0': {
                     'target': '6072557b6c10cd9a21145781e26ad1f978ed14b9',
                     'target_type': 'revision',
                     'target_url': '/api/1/revision/6072557b6c10cd9a21145781e26ad1f978ed14b9/' # noqa
                 },
                 'refs/tags/0.10.1': {
                     'target': 'ecc003b43433e5b46511157598e4857a761007bf',
                     'target_type': 'revision',
                     'target_url': '/api/1/revision/ecc003b43433e5b46511157598e4857a761007bf/' # noqa
                 }
             },
             'origin': 1,
             'origin_url': '/api/1/origin/1/',
             'status': 'full',
             'visit': 1}

        mock_service.lookup_revision_multiple.return_value = \
            [{'directory': '828da2b80e41aa958b2c98526f4a1d2cc7d298b7'},
             {'directory': '2df4cd84ecc65b50b1d5318d3727e02a39b8a4cf'},
             {'directory': '28ba64f97ef709e54838ae482c2da2619a74a0bd'}]

        expected_result = [
            {'name': 'refs/heads/master',
             'revision': '9fbd21adbac36be869514e82e2e98505dc47219c',
             'directory': '828da2b80e41aa958b2c98526f4a1d2cc7d298b7'},
            {'name': 'refs/tags/0.10.0',
             'revision': '6072557b6c10cd9a21145781e26ad1f978ed14b9',
             'directory': '2df4cd84ecc65b50b1d5318d3727e02a39b8a4cf'},
            {'name': 'refs/tags/0.10.1',
             'revision': 'ecc003b43433e5b46511157598e4857a761007bf',
             'directory': '28ba64f97ef709e54838ae482c2da2619a74a0bd'}
        ]

        origin_visit_branches = utils.get_origin_visit_branches(1, 1)

        self.assertEqual(origin_visit_branches, expected_result)

    @istest
    def gen_link(self):
        self.assertEqual(utils.gen_link('https://www.softwareheritage.org/', 'SWH'), # noqa
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
                         '<a href="%s">%s</a>' % (revision_url, revision_id[:7])) # noqa

    @istest
    def test_prepare_revision_log_for_display_no_contex(self):
        per_page = 10
        first_page_logs_data = revision_history_log_test[:per_page+1]
        second_page_logs_data = revision_history_log_test[per_page:2*per_page+1] # noqa
        third_page_logs_data = revision_history_log_test[2*per_page:3*per_page+1] # noqa
        last_page_logs_data = revision_history_log_test[3*per_page:3*per_page+5] # noqa

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

        old_prev_revs_bc = str(revision_log_display_data['prev_revs_breadcrumb']) # noqa

        revision_log_display_data = utils.prepare_revision_log_for_display(
            second_page_logs_data, per_page, old_prev_revs_bc)

        self.assertEqual(revision_log_display_data['revision_log_data'],
                         utils._format_log_entries(second_page_logs_data,
                                                   per_page))

        self.assertEqual(revision_log_display_data['prev_rev'],
                         second_page_logs_data[-1]['id'])

        self.assertEqual(revision_log_display_data['prev_revs_breadcrumb'],
                         old_prev_revs_bc + '/' + second_page_logs_data[0]['id']) # noqa

        self.assertEqual(revision_log_display_data['next_rev'],
                         old_prev_revs_bc)
        self.assertEqual(revision_log_display_data['next_revs_breadcrumb'],
                         None)

        old_prev_revs_bc = str(revision_log_display_data['prev_revs_breadcrumb']) # noqa

        revision_log_display_data = utils.prepare_revision_log_for_display(
            third_page_logs_data, per_page, old_prev_revs_bc)

        self.assertEqual(revision_log_display_data['revision_log_data'],
                         utils._format_log_entries(third_page_logs_data, per_page)) # noqa

        self.assertEqual(revision_log_display_data['prev_rev'],
                         third_page_logs_data[-1]['id'])

        self.assertEqual(revision_log_display_data['prev_revs_breadcrumb'],
                         old_prev_revs_bc + '/' + third_page_logs_data[0]['id']) # noqa

        self.assertEqual(revision_log_display_data['next_rev'],
                         old_prev_revs_bc.split('/')[-1])

        self.assertEqual(revision_log_display_data['next_revs_breadcrumb'],
                         '/'.join(old_prev_revs_bc.split('/')[:-1]))

        old_prev_revs_bc = str(revision_log_display_data['prev_revs_breadcrumb']) # noqa

        revision_log_display_data = utils.prepare_revision_log_for_display(
            last_page_logs_data, per_page, old_prev_revs_bc)

        self.assertEqual(revision_log_display_data['revision_log_data'],
                         utils._format_log_entries(last_page_logs_data, per_page)) # noqa

        self.assertEqual(revision_log_display_data['prev_rev'],
                         None)

        self.assertEqual(revision_log_display_data['prev_revs_breadcrumb'],
                         None) # noqa

        self.assertEqual(revision_log_display_data['next_rev'], old_prev_revs_bc.split('/')[-1]) # noqa
        self.assertEqual(revision_log_display_data['next_revs_breadcrumb'],
                         '/'.join(old_prev_revs_bc.split('/')[:-1]))

    @istest
    def test_prepare_revision_log_for_display_origin_contex(self):
        per_page = 10
        first_page_logs_data = revision_history_log_test[:per_page+1]
        second_page_logs_data = revision_history_log_test[per_page:2*per_page+1] # noqa
        third_page_logs_data = revision_history_log_test[2*per_page:3*per_page+1] # noqa
        last_page_logs_data = revision_history_log_test[3*per_page:3*per_page+5] # noqa

        revision_log_display_data = utils.prepare_revision_log_for_display(
            first_page_logs_data, per_page, None, origin_context=True)

        self.assertEqual(revision_log_display_data['revision_log_data'],
                         utils._format_log_entries(first_page_logs_data,
                                                   per_page))

        self.assertEqual(revision_log_display_data['prev_rev'],
                         first_page_logs_data[-1]['id'])

        self.assertEqual(revision_log_display_data['prev_revs_breadcrumb'],
                         first_page_logs_data[-1]['id'])

        self.assertEqual(revision_log_display_data['next_rev'], None)
        self.assertEqual(revision_log_display_data['next_revs_breadcrumb'],
                         None)

        old_prev_revs_bc = str(revision_log_display_data['prev_revs_breadcrumb']) # noqa

        revision_log_display_data = utils.prepare_revision_log_for_display(
            second_page_logs_data, per_page, old_prev_revs_bc, origin_context=True) # noqa

        self.assertEqual(revision_log_display_data['revision_log_data'],
                         utils._format_log_entries(second_page_logs_data,
                                                   per_page))

        self.assertEqual(revision_log_display_data['prev_rev'],
                         second_page_logs_data[-1]['id'])

        self.assertEqual(revision_log_display_data['prev_revs_breadcrumb'],
                         old_prev_revs_bc + '/' + second_page_logs_data[-1]['id']) # noqa

        self.assertEqual(revision_log_display_data['next_rev'],
                         old_prev_revs_bc)
        self.assertEqual(revision_log_display_data['next_revs_breadcrumb'],
                         None)

        old_prev_revs_bc = str(revision_log_display_data['prev_revs_breadcrumb']) # noqa

        revision_log_display_data = utils.prepare_revision_log_for_display(
            third_page_logs_data, per_page, old_prev_revs_bc, origin_context=True) # noqa

        self.assertEqual(revision_log_display_data['revision_log_data'],
                         utils._format_log_entries(third_page_logs_data, per_page)) # noqa

        self.assertEqual(revision_log_display_data['prev_rev'],
                         third_page_logs_data[-1]['id'])

        self.assertEqual(revision_log_display_data['prev_revs_breadcrumb'],
                         old_prev_revs_bc + '/' + third_page_logs_data[-1]['id']) # noqa

        self.assertEqual(revision_log_display_data['next_rev'],
                         old_prev_revs_bc.split('/')[-1])

        self.assertEqual(revision_log_display_data['next_revs_breadcrumb'],
                         '/'.join(old_prev_revs_bc.split('/')[:-1]))

        old_prev_revs_bc = str(revision_log_display_data['prev_revs_breadcrumb']) # noqa

        revision_log_display_data = utils.prepare_revision_log_for_display(
            last_page_logs_data, per_page, old_prev_revs_bc, origin_context=True) # noqa

        self.assertEqual(revision_log_display_data['revision_log_data'],
                         utils._format_log_entries(last_page_logs_data, per_page)) # noqa

        self.assertEqual(revision_log_display_data['prev_rev'],
                         None)

        self.assertEqual(revision_log_display_data['prev_revs_breadcrumb'],
                         None) # noqa

        self.assertEqual(revision_log_display_data['next_rev'], old_prev_revs_bc.split('/')[-1]) # noqa
        self.assertEqual(revision_log_display_data['next_revs_breadcrumb'],
                         '/'.join(old_prev_revs_bc.split('/')[:-1]))
