# Copyright (C) 2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from unittest.mock import patch

from swh.web.common.exc import NotFoundExc
from swh.web.common.origin_visits import (
    get_origin_visits, get_origin_visit
)
from swh.web.tests.testcase import WebTestCase


class OriginVisitsTestCase(WebTestCase):
    @patch('swh.web.common.service')
    def test_get_origin_visits(self, mock_service):
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

        origin_visits = get_origin_visits(origin_info)

        self.assertEqual(len(origin_visits), 3)

    @patch('swh.web.common.origin_visits.get_origin_visits')
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
              'origin': origin_info['id']},
             {'status': 'full',
              'date': '2016-02-23T18:05:23.312045+00:00',
              'visit': 2,
              'origin': origin_info['id']},
             {'status': 'full',
              'date': '2016-03-28T01:35:06.554111+00:00',
              'visit': 3,
              'origin': origin_info['id']},
             {'status': 'full',
              'date': '2016-06-18T01:22:24.808485+00:00',
              'visit': 4,
              'origin': origin_info['id']},
             {'status': 'full',
              'date': '2016-08-14T12:10:00.536702+00:00',
              'visit': 5,
              'origin': origin_info['id']}]
        mock_origin_visits.return_value = visits

        visit_id = 12
        with self.assertRaises(NotFoundExc) as cm:
            visit = get_origin_visit(origin_info,
                                     visit_id=visit_id)
        exception_text = cm.exception.args[0]
        self.assertIn('Visit with id %s' % visit_id, exception_text)
        self.assertIn('type %s' % origin_info['type'], exception_text)
        self.assertIn('url %s' % origin_info['url'], exception_text)

        visit = get_origin_visit(origin_info, visit_id=2)
        self.assertEqual(visit, visits[1])

        visit = get_origin_visit(
            origin_info, visit_ts='2016-02-23T18:05:23.312045+00:00')
        self.assertEqual(visit, visits[1])

        visit = get_origin_visit(
            origin_info, visit_ts='2016-02-20')
        self.assertEqual(visit, visits[1])

        visit = get_origin_visit(
            origin_info, visit_ts='2016-06-18T01:22')
        self.assertEqual(visit, visits[3])

        visit = get_origin_visit(
            origin_info, visit_ts='2016-06-18 01:22')
        self.assertEqual(visit, visits[3])

        visit = get_origin_visit(
            origin_info, visit_ts=1466208000)
        self.assertEqual(visit, visits[3])

        visit = get_origin_visit(
            origin_info, visit_ts='2014-01-01')
        self.assertEqual(visit, visits[0])

        visit = get_origin_visit(
            origin_info, visit_ts='2018-01-01')
        self.assertEqual(visit, visits[-1])
