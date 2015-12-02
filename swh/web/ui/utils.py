# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import flask


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
    for r in url_map._rules:
        rule = r.rule
        if rule == prefix_url_rule or rule in blacklist:
            continue

        if rule.startswith(prefix_url_rule):
            out[r.rule] = {'methods': sorted(map(str, r.methods)),
                           'endpoint': r.endpoint}
    return out


def prepare_directory_listing(files):
    """Given a list of dictionary files, return a view ready dictionary.

    """
    ls = []
    for entry in files:
        new_entry = {'name': entry['name'],
                     'type': entry['type']}
        if entry['type'] == 'dir':
            new_entry['link'] = flask.url_for('browse_directory',
                                              sha1_git=entry['target'])
        else:
            new_entry['link'] = flask.url_for('show_content',
                                              q=entry['sha1'])
        ls.append(new_entry)

    return ls


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
