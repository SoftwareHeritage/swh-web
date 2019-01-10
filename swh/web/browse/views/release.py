# Copyright (C) 2017-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.shortcuts import render

from swh.web.common import service
from swh.web.common.utils import (
    reverse, format_utc_iso_date
)
from swh.web.common.exc import NotFoundExc, handle_view_exception
from swh.web.browse.browseurls import browse_route
from swh.web.browse.utils import (
    gen_person_link, gen_revision_link,
    get_snapshot_context, gen_link,
    gen_snapshot_link, get_swh_persistent_ids
)


@browse_route(r'release/(?P<sha1_git>[0-9a-f]+)/',
              view_name='browse-release')
def release_browse(request, sha1_git):
    """
    Django view that produces an HTML display of a release
    identified by its id.

    The url that points to it is :http:get:`/browse/release/(sha1_git)/`.
    """
    try:
        release = service.lookup_release(sha1_git)
        snapshot_context = None
        origin_info = None
        snapshot_id = request.GET.get('snapshot_id', None)
        origin_type = request.GET.get('origin_type', None)
        origin_url = request.GET.get('origin_url', None)
        if not origin_url:
            origin_url = request.GET.get('origin', None)
        timestamp = request.GET.get('timestamp', None)
        visit_id = request.GET.get('visit_id', None)
        if origin_url:
            try:
                snapshot_context = \
                    get_snapshot_context(snapshot_id, origin_type,
                                         origin_url, timestamp,
                                         visit_id)
            except Exception:
                raw_rel_url = reverse('browse-release',
                                      url_args={'sha1_git': sha1_git})
                error_message = \
                    ('The Software Heritage archive has a release '
                     'with the hash you provided but the origin '
                     'mentioned in your request appears broken: %s. '
                     'Please check the URL and try again.\n\n'
                     'Nevertheless, you can still browse the release '
                     'without origin information: %s'
                        % (gen_link(origin_url), gen_link(raw_rel_url)))

                raise NotFoundExc(error_message)
            origin_info = snapshot_context['origin_info']
        elif snapshot_id:
            snapshot_context = get_snapshot_context(snapshot_id)
    except Exception as exc:
        return handle_view_exception(request, exc)

    release_data = {}

    author_name = 'None'
    release_data['author'] = 'None'
    if release['author']:
        author_name = release['author']['name'] or \
                      release['author']['fullname']
        release_data['author'] = \
            gen_person_link(release['author']['id'], author_name,
                            snapshot_context)
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
                    url_args={'query_string': 'sha1_git:' + release['target']})
        release_data['target'] = gen_link(content_url, release['target'])
    elif release['target_type'] == 'directory':
        directory_url = \
            reverse('browse-directory',
                    url_args={'sha1_git': release['target']})
        release_data['target'] = gen_link(directory_url, release['target'])
    elif release['target_type'] == 'release':
        release_url = \
            reverse('browse-release',
                    url_args={'sha1_git': release['target']})
        release_data['target'] = gen_link(release_url, release['target'])

    release_note_lines = []
    if release['message']:
        release_note_lines = release['message'].split('\n')

    vault_cooking = None

    query_params = {}
    if snapshot_id:
        query_params = {'snapshot_id': snapshot_id}
    elif origin_info:
        query_params = {'origin': origin_info['url']}

    target_url = ''
    if release['target_type'] == 'revision':
        target_url = reverse('browse-revision',
                             url_args={'sha1_git': release['target']},
                             query_params=query_params)
        try:
            revision = service.lookup_revision(release['target'])
            vault_cooking = {
                'directory_context': True,
                'directory_id': revision['directory'],
                'revision_context': True,
                'revision_id': release['target']
            }
        except Exception:
            pass
    elif release['target_type'] == 'directory':
        target_url = reverse('browse-directory',
                             url_args={'sha1_git': release['target']},
                             query_params=query_params)
        try:
            revision = service.lookup_directory(release['target'])
            vault_cooking = {
                'directory_context': True,
                'directory_id': revision['directory'],
                'revision_context': False,
                'revision_id': None
            }
        except Exception:
            pass
    elif release['target_type'] == 'content':
        target_url = reverse('browse-content',
                             url_args={'query_string': release['target']},
                             query_params=query_params)
    elif release['target_type'] == 'release':
        target_url = reverse('browse-release',
                             url_args={'sha1_git': release['target']},
                             query_params=query_params)

    release['target_url'] = target_url

    if snapshot_context:
        release_data['snapshot id'] = snapshot_context['snapshot_id']

    if origin_info:
        release_url = reverse('browse-release',
                              url_args={'sha1_git': release['id']})
        release_data['context-independent release'] = \
            gen_link(release_url, link_text='Browse',
                     link_attrs={'class': 'btn btn-default btn-sm',
                                 'role': 'button'})
        release_data['origin id'] = origin_info['id']
        release_data['origin type'] = origin_info['type']
        release_data['origin url'] = gen_link(origin_info['url'],
                                              origin_info['url'])
        browse_snapshot_link = \
            gen_snapshot_link(snapshot_context['snapshot_id'],
                              link_text='Browse',
                              link_attrs={'class': 'btn btn-default btn-sm',
                                          'role': 'button'})
        release_data['snapshot'] = browse_snapshot_link

    swh_objects = [{'type': 'release',
                    'id': sha1_git}]

    if snapshot_context:
        snapshot_id = snapshot_context['snapshot_id']

    if snapshot_id:
        swh_objects.append({'type': 'snapshot',
                            'id': snapshot_id})

    swh_ids = get_swh_persistent_ids(swh_objects, snapshot_context)

    note_header = 'None'
    if len(release_note_lines) > 0:
        note_header = release_note_lines[0]

    release['note_header'] = note_header
    release['note_body'] = '\n'.join(release_note_lines[1:])

    heading = 'Release - %s' % release['name']
    if snapshot_context:
        context_found = 'snapshot: %s' % snapshot_context['snapshot_id']
        if origin_info:
            context_found = 'origin: %s' % origin_info['url']
        heading += ' - %s' % context_found

    return render(request, 'browse/release.html',
                  {'heading': heading,
                   'swh_object_id': swh_ids[0]['swh_id'],
                   'swh_object_name': 'Release',
                   'swh_object_metadata': release_data,
                   'release': release,
                   'snapshot_context': snapshot_context,
                   'show_actions_menu': True,
                   'breadcrumbs': None,
                   'vault_cooking': vault_cooking,
                   'top_right_link': None,
                   'swh_ids': swh_ids})
