# Copyright (C) 2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import textwrap

from django.shortcuts import render
from django.utils.safestring import mark_safe
from swh.web.common import service
from swh.web.common.utils import reverse, format_utc_iso_date
from swh.web.common.exc import handle_view_exception
from swh.web.browse.browseurls import browse_route


def _gen_person_link(person_id, person_name):
    person_url = reverse('browse-person', kwargs={'person_id': person_id})
    person_link = '<a href="%s">%s</a>' % (person_url, person_name)
    return mark_safe(person_link)


def _gen_directory_link(sha1_git, link_text):
    directory_url = reverse('browse-directory',
                            kwargs={'sha1_git': sha1_git})
    directory_link = '<a href="%s">%s</a>' % \
        (directory_url, link_text)
    return mark_safe(directory_link)


def _gen_revision_link(revision_id, shorten_id=False):
    revision_url = reverse('browse-revision',
                           kwargs={'sha1_git': revision_id})
    if shorten_id:
        revision_link = '<a href="%s">%s</a>' % (revision_url, revision_id[:7])
    else:
        revision_link = '<a href="%s">%s</a>' % (revision_url, revision_id)
    return mark_safe(revision_link)


def _gen_revision_log_link(revision_id):
    revision_log_url = reverse('browse-revision-log',
                               kwargs={'sha1_git': revision_id})
    revision_log_link = '<a href="%s">%s</a>' % (revision_log_url,
                                                 revision_log_url)
    return mark_safe(revision_log_link)


@browse_route(r'revision/(?P<sha1_git>[0-9a-f]+)/',
              view_name='browse-revision')
def revision_browse(request, sha1_git):
    """
    Django view that produces an HTML display of a SWH revision
    identified by its id.

    The url that points to it is :http:get:`/browse/revision/(revision_id)/`.

    Args:
        request: input django http request
        sha1_git: a SWH revision id

    Returns:
        The HMTL rendering for the metadata of the provided revision.
    """
    try:
        revision = service.lookup_revision(sha1_git)
    except Exception as exc:
        return handle_view_exception(exc)

    revision_data = {}

    revision_data['author'] = _gen_person_link(
        revision['author']['id'], revision['author']['name'])
    revision_data['committer'] = _gen_person_link(
        revision['committer']['id'], revision['committer']['name'])
    revision_data['committer date'] = format_utc_iso_date(
        revision['committer_date'])
    revision_data['date'] = format_utc_iso_date(revision['date'])
    revision_data['directory'] = _gen_directory_link(revision['directory'],
                                                     revision['directory'])
    revision_data['history log'] = _gen_revision_log_link(sha1_git)
    revision_data['merge'] = revision['merge']
    revision_data['message'] = revision['message']

    parents = ''
    for p in revision['parents']:
        parent_link = _gen_revision_link(p)
        parents += parent_link + '<br/>'

    revision_data['parents'] = mark_safe(parents)
    revision_data['synthetic'] = revision['synthetic']
    revision_data['type'] = revision['type']

    return render(request, 'revision.html', {'revision': revision_data})


NB_LOG_ENTRIES = 20


@browse_route(r'revision/(?P<sha1_git>[0-9a-f]+)/log/',
              view_name='browse-revision-log')
def revision_log_browse(request, sha1_git):
    """
    Django view that produces an HTML display of the history
    log for a SWH revision identified by its id.

    The url that points to it is :http:get:`/browse/revision/(revision_id)/log/`.

    Args:
        request: input django http request
        sha1_git: a SWH revision id

    Returns:
        The HMTL rendering of the revision history log.
    """ # noqa
    try:
        per_page = int(request.GET.get('per_page', NB_LOG_ENTRIES))
        revision_log = service.lookup_revision_log(sha1_git,
                                                   limit=per_page+1)
        revision_log = list(revision_log)
    except Exception as exc:
        return handle_view_exception(exc)

    revision_log_data = []

    next_rev = None
    prev_rev = None
    next_revs_breadcrumb = None
    prev_revs_breadcrumb = None
    if len(revision_log) == per_page + 1:
        prev_rev = revision_log[-1]['id']

    revs_breadcrumb = request.GET.get('revs_breadcrumb', None)
    if revs_breadcrumb:
        revs = revs_breadcrumb.split('/')
        next_rev = revs[-1]
        if len(revs) > 1:
            next_revs_breadcrumb = '/'.join(revs[:-1])
        prev_revs_breadcrumb = revs_breadcrumb + '/' + sha1_git
    else:
        prev_revs_breadcrumb = sha1_git

    prev_rev_url = None
    if prev_rev:
        prev_rev_url = \
            reverse('browse-revision-log',
                    kwargs={'sha1_git': prev_rev},
                    query_params={'revs_breadcrumb': prev_revs_breadcrumb,
                                  'per_page': per_page})

    next_rev_url = None
    if next_rev:
        next_rev_url = \
            reverse('browse-revision-log',
                    kwargs={'sha1_git': next_rev},
                    query_params={'revs_breadcrumb': next_revs_breadcrumb,
                                  'per_page': per_page})

    for i, log in enumerate(revision_log):
        if i == per_page:
            break
        revision_log_data.append({
            'author': _gen_person_link(log['author']['id'],
                                       log['author']['name']),
            'revision': _gen_revision_link(log['id'], True),
            'message': log['message'],
            'message_shorten': textwrap.shorten(log['message'],
                                                width=80,
                                                placeholder='...'),
            'date': format_utc_iso_date(log['date']),
            'directory': _gen_directory_link(log['directory'], 'Tree')
        })

    return render(request, 'revision-log.html',
                  {'revision_log': revision_log_data,
                   'next_rev_url': next_rev_url,
                   'prev_rev_url': prev_rev_url})
