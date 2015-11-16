# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.core import hashutil


def from_origin(origin):
    """Convert from an SWH origin to an origin dictionary.

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
    """Convert from an SWH release to a json serializable release dictionary.

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
        if key in ['id', 'revision']:
            new_release[key] = hashutil.hash_to_hex(value) if value else None
        elif key == 'comment':
            new_release[key] = value.decode('utf-8')
        else:
            new_release[key] = value
    return new_release


def from_revision(revision):
    """Convert from an SWH revision to a json serializable revision dictionary.

    Args:
        revision: Dict with the following keys
        - id: identifier of the revision (sha1 in bytes)
        - directory: identifier of the directory the revision points to (sha1
        in bytes)
        - author_name, author_email: author's revision name and email
        - committer_name, committer_email: committer's revision name and email
        - message: revision's message
        - date, date_offset: revision's author date
        - committer_date, committer_date_offset: revision's commit date
        - parents: list of parents for such revision
        - synthetic: revision's property nature
        - type: revision's type (git, tar or dsc at the moment)
        - metadata: if the revision is synthetic, this can reference dynamic
        properties.

    Returns:
        Revision dictionary with the same keys as inputs, only:
        - sha1s are in hexadecimal strings (id, directory)
        - bytes are decoded in string (author_name, committer_name,
        author_email, committer_email, message)
        - remaining keys are left as is

    """
    new_revision = {}
    for key, value in revision.items():
        if key in ['id', 'directory']:
            new_revision[key] = hashutil.hash_to_hex(value) if value else None
        elif key in ['author_name',
                     'committer_name',
                     'author_email',
                     'committer_email',
                     'message']:
            new_revision[key] = value.decode('utf-8')
        else:
            new_revision[key] = value

    return new_revision
