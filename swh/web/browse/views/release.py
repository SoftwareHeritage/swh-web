# Copyright (C) 2017-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.shortcuts import render
from django.utils.safestring import mark_safe

from swh.web.common import service
from swh.web.common.utils import reverse, format_utc_iso_date
from swh.web.common.exc import handle_view_exception
from swh.web.browse.browseurls import browse_route
from swh.web.browse.utils import (
    gen_person_link, gen_revision_link,
    get_snapshot_context, gen_link
)


@browse_route(r'release/(?P<sha1_git>[0-9a-f]+)/',
              view_name='browse-release')
def release_browse(request, sha1_git):
    """
    Django view that produces an HTML display of a SWH release
    identified by its id.

    The url that points to it is :http:get:`/browse/release/(sha1_git)/`.
    """
    try:
        release = service.lookup_release(sha1_git)
        snapshot_context = None
        snapshot_id = request.GET.get('snapshot_id', None)
        origin_type = request.GET.get('origin_type', None)
        origin_url = request.GET.get('origin_url', None)
        timestamp = request.GET.get('timestamp', None)
        visit_id = request.GET.get('visit_id', None)
        if origin_type and origin_url:
            snapshot_context = get_snapshot_context(snapshot_id, origin_type,
                                                    origin_url, timestamp,
                                                    visit_id)
    except Exception as exc:
        return handle_view_exception(request, exc)

    release_data = {}

    release_data['author'] = gen_person_link(
        release['author']['id'], release['author']['name'])
    release_data['date'] = format_utc_iso_date(release['date'])
    release_data['id'] = sha1_git
    release_data['name'] = release['name']
    release_data['synthetic'] = release['synthetic']
    release_data['target type'] = release['target_type']

    if release['target_type'] == 'revision':
        release_data['target'] = \
            gen_revision_link(release['target'],
                              snapshot_context=snapshot_context)
    elif release['target_type'] == 'content':
        content_url = \
            reverse('browse-content',
                    kwargs={'query_string': 'sha1_git:' + release['target']})
        release_data['target'] = gen_link(content_url, release['target'])
    elif release['target_type'] == 'directory':
        directory_url = \
            reverse('browse-directory',
                    kwargs={'sha1_git': release['target']})
        release_data['target'] = gen_link(directory_url, release['target'])
    elif release['target_type'] == 'release':
        release_url = \
            reverse('browse-release',
                    kwargs={'sha1_git': release['target']})
        release_data['target'] = gen_link(release_url, release['target'])

    release_note_lines = release['message'].split('\n')

    release_target_link = '<b>Target:</b> '
    if release['target_type'] == 'revision':
        release_target_link += '<i class="octicon octicon-git-commit fa-fw"></i>' # noqa
    else:
        release_target_link += release['target_type']
    release_target_link += ' ' + release_data['target']

    return render(request, 'release.html',
                  {'empty_browse': False,
                   'heading': 'Release information',
                   'top_panel_visible': True,
                   'top_panel_collapsible': True,
                   'top_panel_text': 'Release metadata',
                   'swh_object_metadata': release_data,
                   'main_panel_visible': True,
                   'release_name': release['name'],
                   'release_note_header': release_note_lines[0],
                   'release_note_body': '\n'.join(release_note_lines[1:]),
                   'release_target_link': mark_safe(release_target_link),
                   'snapshot_context': snapshot_context})
