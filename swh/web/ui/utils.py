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


def prepare_directory_listing(files):
    """Given a list of dictionary files, return a dictionary ready for view.

    Args:
        files: List of files to enrich

    Returns:
        List of enriched files with urls to other resources

    """
    ls = []
    for entry in files:
        new_entry = {'name': entry['name'],
                     'type': entry['type']}
        if entry['type'] == 'dir':
            new_entry['link'] = flask.url_for('browse_directory',
                                              sha1_git=entry['target'])
        else:
            new_entry['link'] = flask.url_for('browse_content_data',
                                              q=entry['sha1'])
        ls.append(new_entry)

    return ls


def prepare_revision_view(revision):
    """Given a revision, return a dictionary ready view.

    """
    author = revision.get('author')
    if author:
        revision['author'] = person_to_string(author)

    committer = revision.get('committer')
    if committer:
        revision['committer'] = person_to_string(committer)

    revision['parents'] = list(map(lambda p: flask.url_for('browse_revision',
                                                           sha1_git=p),
                                   revision.get('parents', [])))

    if 'children' in revision:
        revision['children'] = list(map(lambda child: flask.url_for(
            'browse_revision',
            sha1_git=child),
                                        revision['children']))

    directory = revision.get('directory')
    if directory:
        revision['directory'] = flask.url_for('browse_directory',
                                              sha1_git=revision['directory'])

    return revision


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
    if isinstance(data, (list, map)):
        return [fmap(f, x) for x in data]
    if isinstance(data, dict):
        return {k: fmap(f, v) for (k, v) in data.items()}
    return f(data)


def prepare_data_for_view(data):
    def replace_api_url(s):
        if isinstance(s, str):
            return re.sub(r'/api/1/', r'/browse/', s)
        return s

    return fmap(replace_api_url, data)


def filter_field_keys(obj, field_keys):
    """Given an object instance (directory or list), and a csv field keys
    to filter on.

    Return the object instance with filtered keys.

    Note: Returns obj as is if it's an instance of types not in (dictionary,
    list)

    Args:
        - obj: one object (dictionary, list...) to filter.
        - field_keys: csv or set of keys to filter the object on

    Returns:
        obj filtered on field_keys

    """
    if isinstance(obj, dict):
        filt_dict = {}
        for key, value in obj.items():
            if key in field_keys:
                filt_dict[key] = value
        return filt_dict
    elif isinstance(obj, list):
        filt_list = []
        for e in obj:
            filt_list.append(filter_field_keys(e, field_keys))
        return filt_list
    return obj


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
