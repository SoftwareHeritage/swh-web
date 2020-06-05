# Copyright (C) 2015-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import datetime
import json
from typing import Dict, Any

from swh.core.utils import decode_with_escape
from swh.model import hashutil
from swh.web.common.typing import OriginInfo, OriginVisitInfo


def _group_checksums(data):
    """Groups checksums values computed from hash functions used in swh
    and stored in data dict under a single entry 'checksums'
    """
    if data:
        checksums = {}
        for hash in hashutil.ALGORITHMS:
            if hash in data and data[hash]:
                checksums[hash] = data[hash]
                del data[hash]
        if len(checksums) > 0:
            data["checksums"] = checksums


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
    if data is None:
        return data
    if isinstance(data, map):
        return map(lambda y: fmap(f, y), (x for x in data))
    if isinstance(data, list):
        return [fmap(f, x) for x in data]
    if isinstance(data, tuple):
        return tuple(fmap(f, x) for x in data)
    if isinstance(data, dict):
        return {k: fmap(f, v) for (k, v) in data.items()}
    return f(data)


def from_swh(
    dict_swh,
    hashess={},
    bytess={},
    dates={},
    blacklist={},
    removables_if_empty={},
    empty_dict={},
    empty_list={},
    convert={},
    convert_fn=lambda x: x,
):
    """Convert from a swh dictionary to something reasonably json
    serializable.

    Args:
        dict_swh: the origin dictionary needed to be transformed
        hashess: list/set of keys representing hashes values (sha1, sha256,
            sha1_git, etc...) as bytes. Those need to be transformed in
            hexadecimal string
        bytess: list/set of keys representing bytes values which needs to be
            decoded
        blacklist: set of keys to filter out from the conversion
        convert: set of keys whose associated values need to be converted using
            convert_fn
        convert_fn: the conversion function to apply on the value of key in
            'convert'

    The remaining keys are copied as is in the output.

    Returns:
        dictionary equivalent as dict_swh only with its keys converted.

    """

    def convert_hashes_bytes(v):
        """v is supposedly a hash as bytes, returns it converted in hex.

        """
        if isinstance(v, bytes):
            return hashutil.hash_to_hex(v)
        return v

    def convert_bytes(v):
        """v is supposedly a bytes string, decode as utf-8.

        FIXME: Improve decoding policy.
        If not utf-8, break!

        """
        if isinstance(v, bytes):
            return v.decode("utf-8")
        return v

    def convert_date(v):
        """
        Args:
            v (dict or datatime): either:

                - a dict with three keys:

                  - timestamp (dict or integer timestamp)
                  - offset
                  - negative_utc

                - or, a datetime

            We convert it to a human-readable string

        """
        if not v:
            return v
        if isinstance(v, datetime.datetime):
            return v.isoformat()

        tz = datetime.timezone(datetime.timedelta(minutes=v["offset"]))
        swh_timestamp = v["timestamp"]
        if isinstance(swh_timestamp, dict):
            date = datetime.datetime.fromtimestamp(swh_timestamp["seconds"], tz=tz)
        else:
            date = datetime.datetime.fromtimestamp(swh_timestamp, tz=tz)

        datestr = date.isoformat()

        if v["offset"] == 0 and v["negative_utc"]:
            # remove the rightmost + and replace it with a -
            return "-".join(datestr.rsplit("+", 1))

        return datestr

    if not dict_swh:
        return dict_swh

    new_dict = {}
    for key, value in dict_swh.items():
        if key in blacklist or (key in removables_if_empty and not value):
            continue

        if key in dates:
            new_dict[key] = convert_date(value)
        elif key in convert:
            new_dict[key] = convert_fn(value)
        elif isinstance(value, dict):
            new_dict[key] = from_swh(
                value,
                hashess=hashess,
                bytess=bytess,
                dates=dates,
                blacklist=blacklist,
                removables_if_empty=removables_if_empty,
                empty_dict=empty_dict,
                empty_list=empty_list,
                convert=convert,
                convert_fn=convert_fn,
            )
        elif key in hashess:
            new_dict[key] = fmap(convert_hashes_bytes, value)
        elif key in bytess:
            try:
                new_dict[key] = fmap(convert_bytes, value)
            except UnicodeDecodeError:
                if "decoding_failures" not in new_dict:
                    new_dict["decoding_failures"] = [key]
                else:
                    new_dict["decoding_failures"].append(key)
                new_dict[key] = fmap(decode_with_escape, value)
        elif key in empty_dict and not value:
            new_dict[key] = {}
        elif key in empty_list and not value:
            new_dict[key] = []
        else:
            new_dict[key] = value

    _group_checksums(new_dict)

    return new_dict


def from_origin(origin: Dict[str, Any]) -> OriginInfo:
    """Convert from a swh origin to an origin dictionary.

    """
    return from_swh(origin)


def from_release(release):
    """Convert from a swh release to a json serializable release dictionary.

    Args:
        release (dict): dictionary with keys:

            - id: identifier of the revision (sha1 in bytes)
            - revision: identifier of the revision the release points to (sha1
              in bytes)

        comment: release's comment message (bytes)
        name: release's name (string)
        author: release's author identifier (swh's id)
        synthetic: the synthetic property (boolean)

    Returns:
        dict: Release dictionary with the following keys:

        - id: hexadecimal sha1 (string)
        - revision: hexadecimal sha1 (string)
        - comment: release's comment message (string)
        - name: release's name (string)
        - author: release's author identifier (swh's id)
        - synthetic: the synthetic property (boolean)

    """
    return from_swh(
        release,
        hashess={"id", "target"},
        bytess={"message", "name", "fullname", "email"},
        dates={"date"},
    )


class SWHMetadataEncoder(json.JSONEncoder):
    """Special json encoder for metadata field which can contain bytes
    encoded value.

    """

    def default(self, obj):
        if isinstance(obj, bytes):
            try:
                return obj.decode("utf-8")
            except UnicodeDecodeError:
                # fallback to binary representation to avoid display errors
                return repr(obj)
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)


def convert_revision_metadata(metadata):
    """Convert json specific dict to a json serializable one.

    """
    if not metadata:
        return {}

    return json.loads(json.dumps(metadata, cls=SWHMetadataEncoder))


def from_revision(revision):
    """Convert from a swh revision to a json serializable revision dictionary.

    Args:
        revision (dict): dict with keys:

            - id: identifier of the revision (sha1 in bytes)
            - directory: identifier of the directory the revision points to
              (sha1 in bytes)
            - author_name, author_email: author's revision name and email
            - committer_name, committer_email: committer's revision name and
              email
            - message: revision's message
            - date, date_offset: revision's author date
            - committer_date, committer_date_offset: revision's commit date
            - parents: list of parents for such revision
            - synthetic: revision's property nature
            - type: revision's type (git, tar or dsc at the moment)
            - metadata: if the revision is synthetic, this can reference
              dynamic properties.

    Returns:
        dict: Revision dictionary with the same keys as inputs, except:

        - sha1s are in hexadecimal strings (id, directory)
        - bytes are decoded in string (author_name, committer_name,
          author_email, committer_email)

        Remaining keys are left as is

    """
    revision = from_swh(
        revision,
        hashess={"id", "directory", "parents", "children"},
        bytess={"name", "fullname", "email"},
        convert={"metadata"},
        convert_fn=convert_revision_metadata,
        dates={"date", "committer_date"},
    )

    if revision:
        if "parents" in revision:
            revision["merge"] = len(revision["parents"]) > 1
        if "message" in revision:
            try:
                revision["message"] = revision["message"].decode("utf-8")
            except UnicodeDecodeError:
                revision["message_decoding_failed"] = True
                revision["message"] = None

    return revision


def from_content(content):
    """Convert swh content to serializable content dictionary.

    """
    return from_swh(
        content,
        hashess={"sha1", "sha1_git", "sha256", "blake2s256"},
        blacklist={"ctime"},
        convert={"status"},
        convert_fn=lambda v: "absent" if v == "hidden" else v,
    )


def from_person(person):
    """Convert swh person to serializable person dictionary.

    """
    return from_swh(person, bytess={"name", "fullname", "email"})


def from_origin_visit(visit: Dict[str, Any]) -> OriginVisitInfo:
    """Convert swh origin_visit to serializable origin_visit dictionary.

    """
    ov = from_swh(
        visit,
        hashess={"target", "snapshot"},
        bytess={"branch"},
        dates={"date"},
        empty_dict={"metadata"},
    )

    return ov


def from_snapshot(snapshot):
    """Convert swh snapshot to serializable snapshot dictionary.

    """
    sv = from_swh(snapshot, hashess={"id", "target"}, bytess={"next_branch"})

    if sv and "branches" in sv:
        sv["branches"] = {decode_with_escape(k): v for k, v in sv["branches"].items()}
        for k, v in snapshot["branches"].items():
            # alias target existing branch names, not a sha1
            if v and v["target_type"] == "alias":
                branch = decode_with_escape(k)
                target = decode_with_escape(v["target"])
                sv["branches"][branch]["target"] = target

    return sv


def from_directory_entry(dir_entry):
    """Convert swh directory to serializable directory dictionary.

    """
    return from_swh(
        dir_entry,
        hashess={"dir_id", "sha1_git", "sha1", "sha256", "blake2s256", "target"},
        bytess={"name"},
        removables_if_empty={"sha1", "sha1_git", "sha256", "blake2s256", "status"},
        convert={"status"},
        convert_fn=lambda v: "absent" if v == "hidden" else v,
    )


def from_filetype(content_entry):
    """Convert swh content to serializable dictionary containing keys
    'id', 'encoding', and 'mimetype'.

    """
    return from_swh(content_entry, hashess={"id"})
