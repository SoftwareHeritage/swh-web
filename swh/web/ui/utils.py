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
    """Map f to data.
    Keep the initial data structure as original but map function f to each
    level.

    Args:
        f: function that expects one argument.
        data: data to traverse to apply the f function. list, map, dict or bare
        value.

    Returns:
        The same data-structure with modified values by the f function.
    """
    if isinstance(data, map):
        return (fmap(f, x) for x in data)
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
        datetime result of parsing values.

    Samples:
        - 2016-01-12
        - 2016-01-12T09:19:12+0100
        - Today is January 1, 2047 at 8:21:00AM
        - 1452591542
    """
    try:
        res = parser.parse(timestamp, ignoretz=False, fuzzy=True)
    except:
        res = datetime.datetime.fromtimestamp(float(timestamp))
    return res


def enrich_release(release):
    """Enrich a release with link to the 'target' of 'type' revision.

    """
    if 'target' in release and 'target_type' in release:
        if release['target_type'] == 'revision':
            release['target_url'] = flask.url_for('api_revision',
                                                  sha1_git=release['target'])
        elif release['target_type'] == 'release':
            release['target_url'] = flask.url_for('api_release',
                                                  sha1_git=release['target'])
        elif release['target_type'] == 'content':
            release['target_url'] = flask.url_for(
                'api_content_metadata',
                q='sha1_git:' + release['target'])

        elif release['target_type'] == 'directory':
            release['target_url'] = flask.url_for('api_directory',
                                                  q=release['target'])

    return release


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


def enrich_content(content):
    """Enrich content with 'data', a link to its raw content.

    """
    if 'sha1' in content:
        content['data_url'] = flask.url_for('api_content_raw',
                                            q=content['sha1'])
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


def enrich_revision(revision, context=None):
    """Enrich revision with links where it makes sense (directory, parents).

    """
    if not context:
        context = revision['id']

    revision['url'] = flask.url_for('api_revision', sha1_git=revision['id'])
    revision['history_url'] = flask.url_for('api_revision_log',
                                            sha1_git=revision['id'])

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
            parents.append(flask.url_for('api_revision_history',
                                         sha1_git_root=context,
                                         sha1_git=parent))

        revision['parent_urls'] = parents

    if 'children' in revision:
        children = []
        for child in revision['children']:
            children.append(flask.url_for('api_revision_history',
                                          sha1_git_root=context,
                                          sha1_git=child))

        revision['children_urls'] = children

    if 'message_decoding_failed' in revision:
        revision['message_url'] = flask.url_for(
            'api_revision_raw_message',
            sha1_git=revision['id'])

    return revision
