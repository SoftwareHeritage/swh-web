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
