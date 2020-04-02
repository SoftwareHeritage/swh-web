# Copyright (C) 2017-2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.utils.html import escape
from hypothesis import given

from swh.web.common.identifiers import get_swh_persistent_id
from swh.web.common.utils import (
    reverse, format_utc_iso_date, parse_timestamp
)
from swh.web.tests.django_asserts import assert_contains, assert_template_used
from swh.web.tests.strategies import (
    origin, revision, unknown_revision, new_origin
)


@given(revision())
def test_revision_browse(client, archive_data, revision):
    url = reverse('browse-revision',
                  url_args={'sha1_git': revision})

    revision_data = archive_data.revision_get(revision)

    author_name = revision_data['author']['name']
    committer_name = revision_data['committer']['name']
    dir_id = revision_data['directory']

    directory_url = reverse('browse-directory',
                            url_args={'sha1_git': dir_id})

    history_url = reverse('browse-revision-log',
                          url_args={'sha1_git': revision})

    resp = client.get(url)

    assert resp.status_code == 200
    assert_template_used(resp, 'browse/revision.html')
    assert_contains(resp, author_name)
    assert_contains(resp, committer_name)
    assert_contains(resp, directory_url)
    assert_contains(resp, history_url)

    for parent in revision_data['parents']:
        parent_url = reverse('browse-revision',
                             url_args={'sha1_git': parent})
        assert_contains(resp, '<a href="%s">%s</a>' %
                        (parent_url, parent))

    author_date = revision_data['date']
    committer_date = revision_data['committer_date']

    message_lines = revision_data['message'].split('\n')

    assert_contains(resp, format_utc_iso_date(author_date))
    assert_contains(resp, format_utc_iso_date(committer_date))
    assert_contains(resp, escape(message_lines[0]))
    assert_contains(resp, escape('\n'.join(message_lines[1:])))


@given(origin())
def test_revision_origin_browse(client, archive_data, origin):
    snapshot = archive_data.snapshot_get_latest(origin['url'])
    revision = archive_data.snapshot_get_head(snapshot)
    revision_data = archive_data.revision_get(revision)
    dir_id = revision_data['directory']

    origin_revision_log_url = reverse('browse-origin-log',
                                        url_args={'origin_url': origin['url']},  # noqa
                                        query_params={'revision': revision})

    url = reverse('browse-revision',
                  url_args={'sha1_git': revision},
                  query_params={'origin': origin['url']})

    resp = client.get(url)

    assert_contains(resp, origin_revision_log_url)

    for parent in revision_data['parents']:
        parent_url = reverse('browse-revision',
                             url_args={'sha1_git': parent},
                             query_params={'origin': origin['url']})
        assert_contains(resp, '<a href="%s">%s</a>' %
                        (parent_url, parent))

    assert_contains(resp, 'vault-cook-directory')
    assert_contains(resp, 'vault-cook-revision')

    swh_rev_id = get_swh_persistent_id('revision', revision)
    swh_rev_id_url = reverse('browse-swh-id',
                             url_args={'swh_id': swh_rev_id})
    assert_contains(resp, swh_rev_id)
    assert_contains(resp, swh_rev_id_url)

    swh_dir_id = get_swh_persistent_id('directory', dir_id)
    swh_dir_id_url = reverse('browse-swh-id',
                             url_args={'swh_id': swh_dir_id})
    assert_contains(resp, swh_dir_id)
    assert_contains(resp, swh_dir_id_url)

    assert_contains(resp, 'swh-take-new-snapshot')


@given(revision())
def test_revision_log_browse(client, archive_data, revision):
    per_page = 10

    revision_log = archive_data.revision_log(revision)

    revision_log_sorted = \
        sorted(revision_log,
               key=lambda rev: -parse_timestamp(
                   rev['committer_date']).timestamp())

    url = reverse('browse-revision-log',
                  url_args={'sha1_git': revision},
                  query_params={'per_page': per_page})

    resp = client.get(url)

    next_page_url = reverse('browse-revision-log',
                            url_args={'sha1_git': revision},
                            query_params={'offset': per_page,
                                          'per_page': per_page})

    nb_log_entries = per_page
    if len(revision_log_sorted) < per_page:
        nb_log_entries = len(revision_log_sorted)

    assert resp.status_code == 200
    assert_template_used(resp, 'browse/revision-log.html')
    assert_contains(resp, '<tr class="swh-revision-log-entry',
                    count=nb_log_entries)
    assert_contains(resp, '<a class="page-link">Newer</a>')

    if len(revision_log_sorted) > per_page:
        assert_contains(resp, '<a class="page-link" href="%s">Older</a>' %  # noqa
                            escape(next_page_url))

    for log in revision_log_sorted[:per_page]:
        revision_url = reverse('browse-revision',
                               url_args={'sha1_git': log['id']})
        assert_contains(resp, log['id'][:7])
        assert_contains(resp, log['author']['name'])
        assert_contains(resp, format_utc_iso_date(log['date']))
        assert_contains(resp, escape(log['message']))
        assert_contains(resp, format_utc_iso_date(log['committer_date']))  # noqa
        assert_contains(resp, revision_url)

    if len(revision_log_sorted) <= per_page:
        return

    resp = client.get(next_page_url)

    prev_page_url = reverse('browse-revision-log',
                            url_args={'sha1_git': revision},
                            query_params={'per_page': per_page})
    next_page_url = reverse('browse-revision-log',
                            url_args={'sha1_git': revision},
                            query_params={'offset': 2 * per_page,
                                          'per_page': per_page})

    nb_log_entries = len(revision_log_sorted) - per_page
    if nb_log_entries > per_page:
        nb_log_entries = per_page

    assert resp.status_code == 200
    assert_template_used(resp, 'browse/revision-log.html')
    assert_contains(resp, '<tr class="swh-revision-log-entry',
                    count=nb_log_entries)

    assert_contains(resp, '<a class="page-link" href="%s">Newer</a>' %
                    escape(prev_page_url))

    if len(revision_log_sorted) > 2 * per_page:
        assert_contains(resp, '<a class="page-link" href="%s">Older</a>' %  # noqa
                            escape(next_page_url))

    if len(revision_log_sorted) <= 2 * per_page:
        return

    resp = client.get(next_page_url)

    prev_page_url = reverse('browse-revision-log',
                            url_args={'sha1_git': revision},
                            query_params={'offset': per_page,
                                          'per_page': per_page})
    next_page_url = reverse('browse-revision-log',
                            url_args={'sha1_git': revision},
                            query_params={'offset': 3 * per_page,
                                          'per_page': per_page})

    nb_log_entries = len(revision_log_sorted) - 2 * per_page
    if nb_log_entries > per_page:
        nb_log_entries = per_page

    assert resp.status_code == 200
    assert_template_used(resp, 'browse/revision-log.html')
    assert_contains(resp, '<tr class="swh-revision-log-entry',
                    count=nb_log_entries)
    assert_contains(resp, '<a class="page-link" href="%s">Newer</a>' %
                    escape(prev_page_url))

    if len(revision_log_sorted) > 3 * per_page:
        assert_contains(resp, '<a class="page-link" href="%s">Older</a>' %  # noqa
                            escape(next_page_url))


@given(revision(), unknown_revision(), new_origin())
def test_revision_request_errors(client, revision, unknown_revision,
                                 new_origin):
    url = reverse('browse-revision',
                  url_args={'sha1_git': unknown_revision})
    resp = client.get(url)
    assert resp.status_code == 404
    assert_template_used(resp, 'error.html')
    assert_contains(resp,
                    'Revision with sha1_git %s not found' %
                    unknown_revision, status_code=404)

    url = reverse('browse-revision',
                  url_args={'sha1_git': revision},
                  query_params={'origin': new_origin.url})

    resp = client.get(url)
    assert resp.status_code == 404
    assert_template_used(resp, 'error.html')
    assert_contains(resp, 'the origin mentioned in your request'
                    ' appears broken', status_code=404)


@given(revision())
def test_revision_uppercase(client, revision):
    url = reverse('browse-revision-uppercase-checksum',
                  url_args={'sha1_git': revision.upper()})

    resp = client.get(url)
    assert resp.status_code == 302

    redirect_url = reverse('browse-revision',
                           url_args={'sha1_git': revision})

    assert resp['location'] == redirect_url
