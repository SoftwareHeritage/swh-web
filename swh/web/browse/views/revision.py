# Copyright (C) 2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.shortcuts import render
from django.utils.safestring import mark_safe
from swh.web.common import service
from swh.web.common.utils import reverse, format_utc_iso_date
from swh.web.common.exc import handle_view_exception
from swh.web.browse.browseurls import browse_route
from swh.web.browse.utils import (
    gen_link, gen_person_link, gen_revision_link,
    prepare_revision_log_for_display
)


def _gen_directory_link(sha1_git, link_text):
    directory_url = reverse('browse-directory',
                            kwargs={'sha1_git': sha1_git})
    return gen_link(directory_url, link_text)


def _gen_revision_log_link(revision_id):
    revision_log_url = reverse('browse-revision-log',
                               kwargs={'sha1_git': revision_id})
    return gen_link(revision_log_url, revision_log_url)


@browse_route(r'revision/(?P<sha1_git>[0-9a-f]+)/',
              view_name='browse-revision')
def revision_browse(request, sha1_git):
    """
    Django view that produces an HTML display of a SWH revision
    identified by its id.

    The url that points to it is :http:get:`/browse/revision/(sha1_git)/`.

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

    revision_data['author'] = gen_person_link(
        revision['author']['id'], revision['author']['name'])
    revision_data['committer'] = gen_person_link(
        revision['committer']['id'], revision['committer']['name'])
    revision_data['committer date'] = format_utc_iso_date(
        revision['committer_date'])
    revision_data['date'] = format_utc_iso_date(revision['date'])
    revision_data['directory'] = _gen_directory_link(revision['directory'],
                                                     revision['directory'])
    revision_data['history log'] = _gen_revision_log_link(sha1_git)
    revision_data['id'] = sha1_git
    revision_data['merge'] = revision['merge']
    revision_data['message'] = revision['message']

    parents = ''
    for p in revision['parents']:
        parent_link = gen_revision_link(p)
        parents += parent_link + '<br/>'

    revision_data['parents'] = mark_safe(parents)
    revision_data['synthetic'] = revision['synthetic']
    revision_data['type'] = revision['type']

    return render(request, 'revision.html',
                  {'top_panel_visible': False,
                   'top_panel_collapsible': False,
                   'top_panel_text_left': 'SWH object: Revision',
                   'top_panel_text_right': 'Sha1 git: ' + sha1_git,
                   'swh_object_metadata': None,
                   'main_panel_visible': True,
                   'revision': revision_data})


NB_LOG_ENTRIES = 20


@browse_route(r'revision/(?P<sha1_git>[0-9a-f]+)/log/',
              view_name='browse-revision-log')
def revision_log_browse(request, sha1_git):
    """
    Django view that produces an HTML display of the history
    log for a SWH revision identified by its id.

    The url that points to it is :http:get:`/browse/revision/(sha1_git)/log/`.

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

    revs_breadcrumb = request.GET.get('revs_breadcrumb', None)

    revision_log_display_data = prepare_revision_log_for_display(
        revision_log, per_page, revs_breadcrumb)

    prev_rev = revision_log_display_data['prev_rev']
    prev_revs_breadcrumb = revision_log_display_data['prev_revs_breadcrumb']
    prev_log_url = None
    if prev_rev:
        prev_log_url = \
            reverse('browse-revision-log',
                    kwargs={'sha1_git': prev_rev},
                    query_params={'revs_breadcrumb': prev_revs_breadcrumb,
                                  'per_page': per_page})

    next_rev = revision_log_display_data['next_rev']
    next_revs_breadcrumb = revision_log_display_data['next_revs_breadcrumb']
    next_log_url = None
    if next_rev:
        next_log_url = \
            reverse('browse-revision-log',
                    kwargs={'sha1_git': next_rev},
                    query_params={'revs_breadcrumb': next_revs_breadcrumb,
                                  'per_page': per_page})

    revision_log_data = revision_log_display_data['revision_log_data']

    for log in revision_log_data:
        log['directory'] = _gen_directory_link(log['directory'], 'Tree')

    return render(request, 'revision-log.html',
                  {'top_panel_visible': False,
                   'top_panel_collapsible': False,
                   'top_panel_text_left': 'SWH object: Revision history',
                   'top_panel_text_right': 'Sha1 git: ' + sha1_git,
                   'swh_object_metadata': None,
                   'main_panel_visible': True,
                   'revision_log': revision_log_data,
                   'next_log_url': next_log_url,
                   'prev_log_url': prev_log_url,
                   'breadcrumbs': None,
                   'branches': None,
                   'branch': None,
                   'top_right_link': None,
                   'top_right_link_text': None,
                   'include_top_navigation': False})
