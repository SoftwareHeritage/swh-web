# Copyright (C) 2017-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import json

from django.shortcuts import render
from django.utils.safestring import mark_safe

from swh.web.common import service
from swh.web.common.utils import reverse, format_utc_iso_date, gen_path_info
from swh.web.common.exc import handle_view_exception
from swh.web.browse.browseurls import browse_route
from swh.web.browse.utils import (
    gen_link, gen_person_link, gen_revision_link,
    prepare_revision_log_for_display,
    get_origin_context, gen_origin_directory_link,
    gen_revision_log_link, get_directory_entries,
    gen_directory_link, request_content, prepare_content_for_display
)


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
        origin_info = None
        origin_context = None
        origin_type = request.GET.get('origin_type', None)
        origin_url = request.GET.get('origin_url', None)
        timestamp = request.GET.get('timestamp', None)
        visit_id = request.GET.get('visit_id', None)
        path = request.GET.get('path', None)
        dir_id = None
        dirs, files = None, None
        content_data = None
        if origin_type and origin_url:
            origin_context = get_origin_context(origin_type, origin_url,
                                                timestamp, visit_id)
        if path:
            path_info = \
                service.lookup_directory_with_path(revision['directory'], path)
            if path_info['type'] == 'dir':
                dir_id = path_info['target']
            else:
                query_string = 'sha1_git:' + path_info['target']
                content_data = request_content(query_string)
        else:
            dir_id = revision['directory']

        if dir_id:
            path = '' if path is None else (path + '/')
            dirs, files = get_directory_entries(dir_id)
    except Exception as exc:
        return handle_view_exception(request, exc)

    revision_data = {}

    revision_data['author'] = gen_person_link(
        revision['author']['id'], revision['author']['name'])
    revision_data['committer'] = gen_person_link(
        revision['committer']['id'], revision['committer']['name'])
    revision_data['committer date'] = format_utc_iso_date(
        revision['committer_date'])
    revision_data['date'] = format_utc_iso_date(revision['date'])
    if origin_context:
        revision_data['directory'] = \
            gen_origin_directory_link(origin_context, sha1_git,
                                      link_text='Browse')
        revision_data['history log'] = \
            gen_revision_log_link(sha1_git, origin_context,
                                  link_text='Browse')
    else:
        revision_data['directory'] = \
            gen_directory_link(revision['directory'], link_text='Browse')
        revision_data['history log'] = \
            gen_revision_log_link(sha1_git, link_text='Browse')
    revision_data['id'] = sha1_git
    revision_data['merge'] = revision['merge']
    revision_data['metadata'] = json.dumps(revision['metadata'],
                                           sort_keys=True,
                                           indent=4, separators=(',', ': '))

    if origin_info:
        browse_revision_url = reverse('browse-revision',
                                      kwargs={'sha1_git': sha1_git})
        revision_data['browse revision url'] = gen_link(browse_revision_url,
                                                        browse_revision_url)
        revision_data['origin id'] = origin_info['id']
        revision_data['origin type'] = origin_info['type']
        revision_data['origin url'] = gen_link(origin_info['url'],
                                               origin_info['url'])

    parents = ''
    for p in revision['parents']:
        parent_link = gen_revision_link(p, origin_context=origin_context)
        parents += parent_link + '<br/>'

    revision_data['parents'] = mark_safe(parents)
    revision_data['synthetic'] = revision['synthetic']
    revision_data['type'] = revision['type']

    message_lines = revision['message'].split('\n')

    parents_links = '<b>%s parent%s</b> ' %  \
        (len(revision['parents']),
         '' if len(revision['parents']) == 1 else 's')
    parents_links += '<i class="octicon octicon-git-commit fa-fw"></i> '
    for p in revision['parents']:
        parent_link = gen_revision_link(p, shorten_id=True,
                                        origin_context=origin_context)
        parents_links += parent_link
        if p != revision['parents'][-1]:
            parents_links += ' + '

    path_info = gen_path_info(path)

    query_params = {'origin_type': origin_type,
                    'origin_url': origin_url,
                    'timestamp': timestamp,
                    'visit_id': visit_id}

    breadcrumbs = []
    breadcrumbs.append({'name': revision['directory'][:7],
                        'url': reverse('browse-revision',
                                       kwargs={'sha1_git': sha1_git},
                                       query_params=query_params)})
    for pi in path_info:
        query_params['path'] = pi['path']
        breadcrumbs.append({'name': pi['name'],
                            'url': reverse('browse-revision',
                                           kwargs={'sha1_git': sha1_git},
                                           query_params=query_params)})

    content = None
    mimetype = None
    language = None
    if content_data:
        breadcrumbs[-1]['url'] = None
        content_display_data = prepare_content_for_display(
            content_data['raw_data'], content_data['mimetype'], path)
        content = content_display_data['content_data']
        mimetype = content_data['mimetype']
        language = content_display_data['language']
    else:
        for d in dirs:
            query_params['path'] = path + d['name']
            d['url'] = reverse('browse-revision',
                               kwargs={'sha1_git': sha1_git},
                               query_params=query_params)
        for f in files:
            query_params['path'] = path + f['name']
            f['url'] = reverse('browse-revision',
                               kwargs={'sha1_git': sha1_git},
                               query_params=query_params)

    return render(request, 'revision.html',
                  {'empty_browse': False,
                   'heading': 'Revision information',
                   'top_panel_visible': True,
                   'top_panel_collapsible': True,
                   'top_panel_text': 'SWH object: Revision',
                   'swh_object_metadata': revision_data,
                   'message_header': message_lines[0],
                   'message_body': '\n'.join(message_lines[1:]),
                   'parents_links': mark_safe(parents_links),
                   'main_panel_visible': True,
                   'origin_context': origin_context,
                   'dirs': dirs,
                   'files': files,
                   'content': content,
                   'mimetype': mimetype,
                   'language': language,
                   'breadcrumbs': breadcrumbs})


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
        return handle_view_exception(request, exc)

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
        log['directory'] = gen_directory_link(log['directory'], 'Tree')

    return render(request, 'revision-log.html',
                  {'empty_browse': False,
                   'heading': 'Revision history information',
                   'top_panel_visible': False,
                   'top_panel_collapsible': False,
                   'top_panel_text': 'SWH object: Revision history',
                   'swh_object_metadata': None,
                   'main_panel_visible': True,
                   'revision_log': revision_log_data,
                   'next_log_url': next_log_url,
                   'prev_log_url': prev_log_url,
                   'breadcrumbs': None,
                   'top_right_link': None,
                   'top_right_link_text': None,
                   'include_top_navigation': False,
                   'origin_context': None})
