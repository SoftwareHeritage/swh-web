# Copyright (C) 2017-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from hypothesis import given

from swh.web.browse import utils
from swh.web.common.utils import reverse, format_utc_iso_date
from swh.web.tests.strategies import origin_with_multiple_visits
from swh.web.tests.testcase import WebTestCase


class SwhBrowseUtilsTestCase(WebTestCase):

    def test_get_mimetype_and_encoding_for_content(self):
        text = b'Hello world!'
        self.assertEqual(utils.get_mimetype_and_encoding_for_content(text),
                         ('text/plain', 'us-ascii'))

    @given(origin_with_multiple_visits())
    def test_get_origin_visit_snapshot_simple(self, origin):

        visits = self.origin_visit_get(origin['url'])

        for visit in visits:

            snapshot = self.snapshot_get(visit['snapshot'])
            branches = []
            releases = []

            def _process_branch_data(branch, branch_data):
                if branch_data['target_type'] == 'revision':
                    rev_data = self.revision_get(branch_data['target'])
                    branches.append({
                        'name': branch,
                        'revision': branch_data['target'],
                        'directory': rev_data['directory'],
                        'date': format_utc_iso_date(rev_data['date']),
                        'message': rev_data['message']
                    })
                elif branch_data['target_type'] == 'release':
                    rel_data = self.release_get(branch_data['target'])
                    rev_data = self.revision_get(rel_data['target'])
                    releases.append({
                        'name': rel_data['name'],
                        'branch_name': branch,
                        'date': format_utc_iso_date(rel_data['date']),
                        'id': rel_data['id'],
                        'message': rel_data['message'],
                        'target_type': rel_data['target_type'],
                        'target': rel_data['target'],
                        'directory': rev_data['directory']
                    })

            for branch in sorted(snapshot['branches'].keys()):
                branch_data = snapshot['branches'][branch]
                if branch_data['target_type'] == 'alias':
                    target_data = snapshot['branches'][branch_data['target']]
                    _process_branch_data(branch, target_data)
                else:
                    _process_branch_data(branch, branch_data)

            assert branches and releases, 'Incomplete test data.'

            origin_visit_branches = utils.get_origin_visit_snapshot(
                origin, visit_id=visit['visit'])

            self.assertEqual(origin_visit_branches, (branches, releases))

    def test_gen_link(self):
        self.assertEqual(
            utils.gen_link('https://www.softwareheritage.org/', 'swh'),
            '<a href="https://www.softwareheritage.org/">swh</a>')

    def test_gen_revision_link(self):
        revision_id = '28a0bc4120d38a394499382ba21d6965a67a3703'
        revision_url = reverse('browse-revision',
                               url_args={'sha1_git': revision_id})

        self.assertEqual(utils.gen_revision_link(revision_id, link_text=None,
                                                 link_attrs=None),
                         '<a href="%s">%s</a>' % (revision_url, revision_id))
        self.assertEqual(
            utils.gen_revision_link(revision_id, shorten_id=True,
                                    link_attrs=None),
            '<a href="%s">%s</a>' % (revision_url, revision_id[:7]))

    def test_gen_person_mail_link(self):
        person_full = {
            'name': 'John Doe',
            'email': 'john.doe@swh.org',
            'fullname': 'John Doe <john.doe@swh.org>'
        }

        self.assertEqual(
            utils.gen_person_mail_link(person_full),
            '<a href="mailto:%s">%s</a>' % (person_full['email'],
                                            person_full['name'])
        )

        link_text = 'Mail'
        self.assertEqual(
            utils.gen_person_mail_link(person_full, link_text=link_text),
            '<a href="mailto:%s">%s</a>' % (person_full['email'],
                                            link_text)
        )

        person_partial_email = {
            'name': None,
            'email': None,
            'fullname': 'john.doe@swh.org'
        }

        self.assertEqual(
            utils.gen_person_mail_link(person_partial_email),
            '<a href="mailto:%s">%s</a>' % (person_partial_email['fullname'],
                                            person_partial_email['fullname'])
        )

        person_partial = {
            'name': None,
            'email': None,
            'fullname': 'John Doe <john.doe@swh.org>'
        }

        self.assertEqual(
            utils.gen_person_mail_link(person_partial),
            person_partial['fullname']
        )

        person_none = {
            'name': None,
            'email': None,
            'fullname': None
        }

        self.assertEqual(
            utils.gen_person_mail_link(person_none),
            'None'
        )
