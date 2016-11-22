# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import datetime
import flask
import re

from dateutil import parser


def filter_endpoints(url_map, prefix_url_rule, blacklist=[]):
    """Filter endpoints by prefix url rule.

    Args:
        - url_map: Url Werkzeug.Map of rules
        - prefix_url_rule: prefix url string
        - blacklist: blacklist of some url

    Returns:
        Dictionary of url_rule with values methods and endpoint.

        The key is the url, the associated value is a dictionary of
        'methods' (possible http methods) and 'endpoint' (python function)

    """
    out = {}
    for r in url_map:
        rule = r['rule']
        if rule == prefix_url_rule or rule in blacklist:
            continue

        if rule.startswith(prefix_url_rule):
            out[rule] = {'methods': sorted(map(str, r['methods'])),
                         'endpoint': r['endpoint']}
    return out


def fmap(f, data):
    """Map f to data at each level.

    This must keep the origin data structure type:
    - map -> map
    - dict -> dict
    - list -> list
    - None -> None

    Args:
        f: function that expects one argument.
        data: data to traverse to apply the f function.
              list, map, dict or bare value.

    Returns:
        The same data-structure with modified values by the f function.

    """
    if not data:
        return data
    if isinstance(data, map):
        return map(lambda y: fmap(f, y), (x for x in data))
    if isinstance(data, list):
        return [fmap(f, x) for x in data]
    if isinstance(data, dict):
        return {k: fmap(f, v) for (k, v) in data.items()}
    return f(data)


def prepare_data_for_view(data, encoding='utf-8'):
    def prepare_data(s):
        # Note: can only be 'data' key with bytes of raw content
        if isinstance(s, bytes):
            try:
                return s.decode(encoding)
            except:
                return "Cannot decode the data bytes, try and set another " \
                       "encoding in the url (e.g. ?encoding=utf8) or " \
                       "download directly the " \
                       "content's raw data."
        if isinstance(s, str):
            return re.sub(r'/api/1/', r'/browse/', s)

        return s

    return fmap(prepare_data, data)


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
        return (filter_field_keys(x, field_keys) for x in data)
    if isinstance(data, list):
        return [filter_field_keys(x, field_keys) for x in data]
    if isinstance(data, dict):
        return {k: v for (k, v) in data.items() if k in field_keys}
    return data


def person_to_string(person):
    """Map a person (person, committer, tagger, etc...) to a string.

    """
    return ''.join([person['name'], ' <', person['email'], '>'])


def parse_timestamp(timestamp):
    """Given a time or timestamp (as string), parse the result as datetime.

    Returns:
        a timezone-aware datetime representing the parsed value. If the parsed
        value doesn't specify a timezone, UTC is assumed.

    Samples:
        - 2016-01-12
        - 2016-01-12T09:19:12+0100
        - Today is January 1, 2047 at 8:21:00AM
        - 1452591542
    """
    default_timestamp = datetime.datetime.utcfromtimestamp(0).replace(
        tzinfo=datetime.timezone.utc)
    try:
        res = parser.parse(timestamp, ignoretz=False, fuzzy=True,
                           default=default_timestamp)
    except:
        res = datetime.datetime.utcfromtimestamp(float(timestamp)).replace(
            tzinfo=datetime.timezone.utc)
    return res


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
            obj['target_url'] = flask.url_for('api_revision',
                                              sha1_git=obj['target'])
        elif obj['target_type'] == 'release':
            obj['target_url'] = flask.url_for('api_release',
                                              sha1_git=obj['target'])
        elif obj['target_type'] == 'content':
            obj['target_url'] = flask.url_for(
                'api_content_metadata',
                q='sha1_git:' + obj['target'])

        elif obj['target_type'] == 'directory':
            obj['target_url'] = flask.url_for('api_directory',
                                              q=obj['target'])

    return obj


enrich_release = enrich_object


def enrich_directory(directory, context_url=None):
    """Enrich directory with url to content or directory.

    """
    if 'type' in directory:
        target_type = directory['type']
        target = directory['target']
        if target_type == 'file':
            directory['target_url'] = flask.url_for('api_content_metadata',
                                                    q='sha1_git:%s' % target)
            if context_url:
                directory['file_url'] = context_url + directory['name'] + '/'
        else:
            directory['target_url'] = flask.url_for('api_directory',
                                                    sha1_git=target)
            if context_url:
                directory['dir_url'] = context_url + directory['name'] + '/'

    return directory


def enrich_metadata_endpoint(content):
    """Enrich metadata endpoint with link to the upper metadata endpoint.

    """
    c = content.copy()
    c['content_url'] = flask.url_for('api_content_metadata',
                                     q='sha1:%s' % c['id'])
    return c


def enrich_content(content):
    """Enrich content with links to:
        - data_url: its raw data
        - filetype_url: its filetype information

    """
    for h in ['sha1', 'sha1_git', 'sha256']:
        if h in content:
            q = '%s:%s' % (h, content[h])
            content['data_url'] = flask.url_for('api_content_raw', q=q)
            content['filetype_url'] = flask.url_for('api_content_filetype',
                                                    q=q)
            content['language_url'] = flask.url_for('api_content_language',
                                                    q=q)
            content['license_url'] = flask.url_for('api_content_license',
                                                   q=q)
            break

    return content


def enrich_entity(entity):
    """Enrich entity with

    """
    if 'uuid' in entity:
        entity['uuid_url'] = flask.url_for('api_entity_by_uuid',
                                           uuid=entity['uuid'])

    if 'parent' in entity and entity['parent']:
        entity['parent_url'] = flask.url_for('api_entity_by_uuid',
                                             uuid=entity['parent'])
    return entity


def _get_path_list(path_string):
    """Helper for enrich_revision: get a list of the sha1 id of the navigation
    breadcrumbs, ordered from the oldest to the most recent.

    Args:
        path_string: the path as a '/'-separated string

    Returns:
        The navigation context as a list of sha1 revision ids
    """
    return path_string.split('/')


def _get_revision_contexts(rev_id, context):
    """Helper for enrich_revision: retrieve for the revision id and potentially
    the navigation breadcrumbs the context to pass to parents and children of
    of the revision.

    Args:
        rev_id: the revision's sha1 id
        context: the current navigation context

    Returns:
        The context for parents, children and the url of the direct child as a
        tuple in that order.
    """
    context_for_parents = None
    context_for_children = None
    url_direct_child = None

    if not context:
        return (rev_id, None, None)

    path_list = _get_path_list(context)
    context_for_parents = '%s/%s' % (context, rev_id)
    prev_for_children = path_list[:-1]
    if len(prev_for_children) > 0:
        context_for_children = '/'.join(prev_for_children)
    child_id = path_list[-1]
    # This commit is not the first commit in the path
    if context_for_children:
        url_direct_child = flask.url_for(
            'api_revision',
            sha1_git=child_id,
            context=context_for_children)
    # This commit is the first commit in the path
    else:
        url_direct_child = flask.url_for(
            'api_revision',
            sha1_git=child_id)

    return (context_for_parents, context_for_children, url_direct_child)


def _make_child_url(rev_children, context):
    """Helper for enrich_revision: retrieve the list of urls corresponding
    to the children of the current revision according to the navigation
    breadcrumbs.

    Args:
        rev_children: a list of revision id
        context: the '/'-separated navigation breadcrumbs

    Returns:
        the list of the children urls according to the context
    """
    children = []
    for child in rev_children:
        if context and child != _get_path_list(context)[-1]:
            children.append(flask.url_for('api_revision', sha1_git=child))
        elif not context:
            children.append(flask.url_for('api_revision', sha1_git=child))
    return children


def enrich_revision(revision, context=None):
    """Enrich revision with links where it makes sense (directory, parents).
    Keep track of the navigation breadcrumbs if they are specified.

    Args:
        revision: the revision as a dict
        context: the navigation breadcrumbs as a /-separated string of revision
        sha1_git
    """

    ctx_parents, ctx_children, url_direct_child = _get_revision_contexts(
        revision['id'], context)

    revision['url'] = flask.url_for('api_revision', sha1_git=revision['id'])
    revision['history_url'] = flask.url_for('api_revision_log',
                                            sha1_git=revision['id'])
    if context:
        revision['history_context_url'] = flask.url_for(
            'api_revision_log',
            sha1_git=revision['id'],
            prev_sha1s=context)

    if 'author' in revision:
        author = revision['author']
        revision['author_url'] = flask.url_for('api_person',
                                               person_id=author['id'])

    if 'committer' in revision:
        committer = revision['committer']
        revision['committer_url'] = flask.url_for('api_person',
                                                  person_id=committer['id'])

    if 'directory' in revision:
        revision['directory_url'] = flask.url_for(
            'api_directory',
            sha1_git=revision['directory'])

    if 'parents' in revision:
        parents = []
        for parent in revision['parents']:
            parents.append(flask.url_for('api_revision',
                                         sha1_git=parent,
                                         context=ctx_parents))
        revision['parent_urls'] = parents

    if 'children' in revision:
        children = _make_child_url(revision['children'], context)
        if url_direct_child:
            children.append(url_direct_child)
        revision['children_urls'] = children
    else:
        if url_direct_child:
            revision['children_urls'] = [url_direct_child]

    if 'message_decoding_failed' in revision:
        revision['message_url'] = flask.url_for(
            'api_revision_raw_message',
            sha1_git=revision['id'])

    return revision
