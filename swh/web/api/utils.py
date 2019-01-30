# Copyright (C) 2015-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


from swh.web.common.utils import reverse
from swh.web.common.query import parse_hash


def filter_field_keys(data, field_keys):
    """Given an object instance (directory or list), and a csv field keys
    to filter on.

    Return the object instance with filtered keys.

    Note: Returns obj as is if it's an instance of types not in (dictionary,
    list)

    Args:
        - data: one object (dictionary, list...) to filter.
        - field_keys: csv or set of keys to filter the object on

    Returns:
        obj filtered on field_keys

    """
    if isinstance(data, map):
        return map(lambda x: filter_field_keys(x, field_keys), data)
    if isinstance(data, list):
        return [filter_field_keys(x, field_keys) for x in data]
    if isinstance(data, dict):
        return {k: v for (k, v) in data.items() if k in field_keys}
    return data


def person_to_string(person):
    """Map a person (person, committer, tagger, etc...) to a string.

    """
    return ''.join([person['name'], ' <', person['email'], '>'])


def enrich_object(object):
    """Enrich an object (revision, release) with link to the 'target' of
    type 'target_type'.

    Args:
        object: An object with target and target_type keys
        (e.g. release, revision)

    Returns:
        Object enriched with target_url pointing to the right
        swh.web.ui.api urls for the pointing object (revision,
        release, content, directory)

    """
    obj = object.copy()
    if 'target' in obj and 'target_type' in obj:
        if obj['target_type'] == 'revision':
            obj['target_url'] = reverse('api-revision',
                                        url_args={'sha1_git': obj['target']})
        elif obj['target_type'] == 'release':
            obj['target_url'] = reverse('api-release',
                                        url_args={'sha1_git': obj['target']})
        elif obj['target_type'] == 'content':
            obj['target_url'] = \
                reverse('api-content',
                        url_args={'q': 'sha1_git:' + obj['target']})

        elif obj['target_type'] == 'directory':
            obj['target_url'] = reverse('api-directory',
                                        url_args={'sha1_git': obj['target']})

    if 'author' in obj:
        author = obj['author']
        obj['author_url'] = reverse('api-person',
                                    url_args={'person_id': author['id']})

    return obj


enrich_release = enrich_object


def enrich_directory(directory, context_url=None):
    """Enrich directory with url to content or directory.

    """
    if 'type' in directory:
        target_type = directory['type']
        target = directory['target']
        if target_type == 'file':
            directory['target_url'] = \
                reverse('api-content', url_args={'q': 'sha1_git:%s' % target})
            if context_url:
                directory['file_url'] = context_url + directory['name'] + '/'
        elif target_type == 'dir':
            directory['target_url'] = reverse('api-directory',
                                              url_args={'sha1_git': target})
            if context_url:
                directory['dir_url'] = context_url + directory['name'] + '/'
        else:
            directory['target_url'] = reverse('api-revision',
                                              url_args={'sha1_git': target})
            if context_url:
                directory['rev_url'] = context_url + directory['name'] + '/'

    return directory


def enrich_metadata_endpoint(content):
    """Enrich metadata endpoint with link to the upper metadata endpoint.

    """
    c = content.copy()
    c['content_url'] = reverse('api-content',
                               url_args={'q': 'sha1:%s' % c['id']})
    return c


def enrich_content(content, top_url=False, query_string=None):
    """Enrich content with links to:
        - data_url: its raw data
        - filetype_url: its filetype information
        - language_url: its programming language information
        - license_url: its licensing information

    Args:
        content: dict of data associated to a swh content object
        top_url: whether or not to include the content url in
            the enriched data
        query_string: optional query string of type '<algo>:<hash>'
            used when requesting the content, it acts as a hint
            for picking the same hash method when computing
            the url listed above

    Returns:
        An enriched content dict filled with additional urls

    """
    checksums = content
    if 'checksums' in content:
        checksums = content['checksums']
    hash_algo = 'sha1'
    if query_string:
        hash_algo = parse_hash(query_string)[0]
    if hash_algo in checksums:
        q = '%s:%s' % (hash_algo, checksums[hash_algo])
        if top_url:
            content['content_url'] = reverse('api-content', url_args={'q': q})
        content['data_url'] = reverse('api-content-raw', url_args={'q': q})
        content['filetype_url'] = reverse('api-content-filetype',
                                          url_args={'q': q})
        content['language_url'] = reverse('api-content-language',
                                          url_args={'q': q})
        content['license_url'] = reverse('api-content-license',
                                         url_args={'q': q})

    return content


def enrich_revision(revision):
    """Enrich revision with links where it makes sense (directory, parents).
    Keep track of the navigation breadcrumbs if they are specified.

    Args:
        revision: the revision as a dict
    """

    revision['url'] = reverse('api-revision',
                              url_args={'sha1_git': revision['id']})
    revision['history_url'] = reverse('api-revision-log',
                                      url_args={'sha1_git': revision['id']})

    if 'author' in revision:
        author = revision['author']
        revision['author_url'] = reverse('api-person',
                                         url_args={'person_id': author['id']})

    if 'committer' in revision:
        committer = revision['committer']
        revision['committer_url'] = \
            reverse('api-person', url_args={'person_id': committer['id']})

    if 'directory' in revision:
        revision['directory_url'] = \
            reverse('api-directory',
                    url_args={'sha1_git': revision['directory']})

    if 'parents' in revision:
        parents = []
        for parent in revision['parents']:
            parents.append({
                'id': parent,
                'url': reverse('api-revision', url_args={'sha1_git': parent})
            })

        revision['parents'] = parents

    if 'children' in revision:
        children = []
        for child in revision['children']:
            children.append(reverse('api-revision',
                                    url_args={'sha1_git': child}))
        revision['children_urls'] = children

    if 'message_decoding_failed' in revision:
        revision['message_url'] = \
            reverse('api-revision-raw-message',
                    url_args={'sha1_git': revision['id']})

    return revision
