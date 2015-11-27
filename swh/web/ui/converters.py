# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.core import hashutil


def fmap(f, data):
    if isinstance(data, list):
        return [f(x) for x in data]
    if isinstance(data, dict):
        return {k: f(v) for (k, v) in data.items()}
    return f(data)


def from_swh(dict_swh, hashess=[], bytess=[], blacklist=[]):
    """Convert from an swh dictionary to something reasonably json
    serializable.

    Args:
        - dict_swh: the origin dictionary needed to be transformed
        - hashess: list/set of keys representing hashes values (sha1, sha256,
        sha1_git, etc...) as bytes. Those need to be transformed in hexadecimal
        string
        - bytess: list/set of keys representing bytes values which needs to
        be decoded

        The remaining keys are copied as is in the output.

    Returns:
        dictionary equivalent as dict_swh only with its keys `converted`.

    """
    def convert_hashes_bytes(v):
        return hashutil.hash_to_hex(v) if v else None

    def convert_bytes(v):
        return v.decode('utf-8')

    if not dict_swh:
        return dict_swh

    new_dict = {}
    for key, value in dict_swh.items():
        if key in hashess:
            new_dict[key] = fmap(convert_hashes_bytes, value)
        elif key in bytess:
            new_dict[key] = fmap(convert_bytes, value)
        elif key in blacklist:
            continue
        else:
            new_dict[key] = value

    return new_dict


def from_origin(origin):
    """Convert from an SWH origin to an origin dictionary.

    """
    return from_swh(origin,
                    hashess=set(['revision']),
                    bytess=set(['path']))


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
    return from_swh(release,
                    hashess=set(['id', 'revision']),
                    bytess=set(['comment', 'author_name', 'author_email']))


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
    return from_swh(revision,
                    hashess=set(['id', 'directory', 'parents']),
                    bytess=set(['author_name',
                                'committer_name',
                                'author_email',
                                'committer_email',
                                'message']))


def from_content(content):
    """Convert swh content to serializable content dictionary.

    """
    return from_swh(content,
                    hashess=set(['sha1', 'sha1_git', 'sha256']),
                    bytess=set(['data']),
                    blacklist=set(['status']))


def from_person(person):
    """Convert swh person to serializable person dictionary.

    """
    return from_swh(person,
                    hashess=set(),
                    bytess=set(['name', 'email']))


def from_directory_entry(dir_entry):
    """Convert swh person to serializable person dictionary.

    """
    return from_swh(dir_entry,
                    hashess=set(['dir_id',
                                 'sha1_git',
                                 'sha1',
                                 'sha256',
                                 'target']),
                    bytess=set(['name']))
