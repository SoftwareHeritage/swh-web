# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.core import hashutil


def from_origin(origin):
    """Convert from an swh origin to an origin dictionary.

    """
    new_origin = {}
    for key, value in origin.items():
        if key == 'revision':
            new_origin[key] = hashutil.hash_to_hex(value)
        elif key == 'path':
            new_origin[key] = value.decode('utf-8')
        else:
            new_origin[key] = value

    return new_origin


def from_release(release):
    """Convert from an swh release to a json serializable release dictionary.

    Args:
        release: Dict with the following keys
        - id: identifier of the revision (sha1 in bytes)
        - revision: identifier of the revision the release points to (sha1 in
        bytes)
        - comment: release's comment message (bytes)
        - name: release's name (string)
        - author: release's author identifier (swh's id)
        - synthetic: the synthetic property (boolean)

    Returns:
        Release dictionary with the following keys:
        - id: hexadecimal sha1 (string)
        - revision: hexadecimal sha1 (string)
        - comment: release's comment message (string)
        - name: release's name (string)
        - author: release's author identifier (swh's id)
        - synthetic: the synthetic property (boolean)

    """
    new_release = {}
    for key, value in release.items():
        if key == 'id' or key == 'revision':
            new_release[key] = hashutil.hash_to_hex(value) if value else None
        elif key == 'comment':
            new_release[key] = value.decode('utf-8')
        else:
            new_release[key] = value
    return new_release
