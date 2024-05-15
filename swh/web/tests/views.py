# Copyright (C) 2018-2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

# Implement some special endpoints used to provide input tests data
# when executing end to end tests with cypress

import json
import os
import tempfile
from typing import Dict

from rest_framework.decorators import api_view
from rest_framework.response import Response

from swh.model import from_disk
from swh.model.hashutil import hash_to_hex
from swh.model.model import (
    Content,
    Origin,
    OriginVisit,
    OriginVisitStatus,
    Person,
    Revision,
    RevisionType,
    Snapshot,
    SnapshotBranch,
    SnapshotTargetType,
    TimestampWithTimezone,
)
from swh.storage.utils import now
from swh.web.tests.data import get_tests_data
from swh.web.utils.highlightjs import get_hljs_language_from_filename

_content_code_data_exts: Dict[str, Dict[str, str]] = {}
_content_code_data_filenames: Dict[str, Dict[str, str]] = {}
_content_other_data_exts: Dict[str, Dict[str, str]] = {}


def _init_content_tests_data(data_path, data_dict, ext_key):
    """
    Helper function to read the content of a directory, store it
    into a test archive and add some files metadata (sha1 and/or
    expected programming language) in a dict.

    Args:
        data_path (str): path to a directory relative to the tests
            folder of swh-web
        data_dict (dict): the dict that will store files metadata
        ext_key (bool): whether to use file extensions or filenames
            as dict keys
    """
    test_contents_dir = os.path.join(os.path.dirname(__file__), data_path).encode(
        "utf-8"
    )
    directory = from_disk.Directory.from_disk(path=test_contents_dir)

    contents = []
    for name, obj in directory.items():
        if obj.object_type == "content":
            with open(obj.data["path"], "rb") as f:
                content = Content.from_data(f.read())
            sha1 = hash_to_hex(content.sha1)
            if ext_key:
                key = name.decode("utf-8").split(".")[-1]
                filename = "test." + key
            else:
                filename = name.decode("utf-8").split("/")[-1]
                key = filename
            language = get_hljs_language_from_filename(filename)
            data_dict[key] = {"sha1": sha1, "language": language}
            contents.append(content)

    storage = get_tests_data()["storage"]
    storage.content_add(contents)


def _init_content_code_data_exts():
    """
    Fill a global dictionary which maps source file extension to
    a code content example.
    """
    global _content_code_data_exts
    if not _content_code_data_exts:
        _init_content_tests_data(
            "resources/contents/code/extensions", _content_code_data_exts, True
        )


def _init_content_other_data_exts():
    """
    Fill a global dictionary which maps a file extension to
    a content example.
    """
    global _content_other_data_exts
    if not _content_other_data_exts:
        _init_content_tests_data(
            "resources/contents/other/extensions", _content_other_data_exts, True
        )


def _init_content_code_data_filenames():
    """
    Fill a global dictionary which maps a filename to
    a content example.
    """
    global _content_code_data_filenames
    if not _content_code_data_filenames:
        _init_content_tests_data(
            "resources/contents/code/filenames", _content_code_data_filenames, False
        )


@api_view(["GET"])
def get_content_code_data_all_exts(request):
    """
    Endpoint implementation returning a list of all source file
    extensions to test for highlighting using cypress.
    """
    _init_content_code_data_exts()
    return Response(
        sorted(_content_code_data_exts.keys()),
        status=200,
        content_type="application/json",
    )


@api_view(["GET"])
def get_content_code_data_by_ext(request, ext):
    """
    Endpoint implementation returning metadata of a code content example
    based on the source file extension.
    """
    data = None
    status = 404
    _init_content_code_data_exts()
    if ext in _content_code_data_exts:
        data = _content_code_data_exts[ext]
        status = 200
    return Response(data, status=status, content_type="application/json")


@api_view(["GET"])
def get_content_other_data_by_ext(request, ext):
    """
    Endpoint implementation returning metadata of a content example
    based on the file extension.
    """
    _init_content_other_data_exts()
    data = None
    status = 404
    if ext in _content_other_data_exts:
        data = _content_other_data_exts[ext]
        status = 200
    return Response(data, status=status, content_type="application/json")


@api_view(["GET"])
def get_content_code_data_all_filenames(request):
    """
    Endpoint implementation returning a list of all source filenames
    to test for highlighting using cypress.
    """
    _init_content_code_data_filenames()
    return Response(
        sorted(_content_code_data_filenames.keys()),
        status=200,
        content_type="application/json",
    )


@api_view(["GET"])
def get_content_code_data_by_filename(request, filename):
    """
    Endpoint implementation returning metadata of a code content example
    based on the source filename.
    """
    data = None
    status = 404
    _init_content_code_data_filenames()
    if filename in _content_code_data_filenames:
        data = _content_code_data_filenames[filename]
        status = 200
    return Response(data, status=status, content_type="application/json")


@api_view(["POST"])
def add_origin_with_contents(request):
    """Endpoint to dynamically add a new origin with some directories and contents
    into the test archive.

    This is useful in cypress tests to add some contents and check their rendering.

    The origin URL must be provided in the ``origin_url`` query parameter and such
    following POST data must be provided to add contents:

    .. code-block:: json

    [
        {'path': 'bar', 'data': 'bar'},
        {'path': 'files/foo', 'data': 'foo'}
    ]
    """
    origin_url = request.GET.get("origin_url")
    storage = get_tests_data()["storage"]
    contents = json.loads(request.body)

    with tempfile.TemporaryDirectory() as tmpdir:
        for content in contents:
            path = os.path.join(tmpdir, content["path"])
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                f.write(content["data"])
        directory = from_disk.Directory.from_disk(path=tmpdir.encode())
        contents, _, directories = from_disk.iter_directory(directory)
        storage.content_add(contents)
        storage.directory_add(directories)

    origin = Origin(url=origin_url)
    storage.origin_add([origin])
    date = now()
    visit_type = "git"
    visit = OriginVisit(origin=origin_url, date=date, type=visit_type)
    visit = storage.origin_visit_add([visit])[0]
    author = Person(
        email=b"author@example.org",
        fullname=b"author <author@example.org>",
        name=b"author",
    )
    revision = Revision(
        directory=directory.hash,
        author=author,
        committer=author,
        message=b"commit message",
        date=TimestampWithTimezone.from_datetime(date),
        committer_date=TimestampWithTimezone.from_datetime(date),
        synthetic=False,
        type=RevisionType.GIT,
    )
    storage.revision_add([revision])
    snapshot = Snapshot(
        branches={
            b"main": SnapshotBranch(
                target=revision.id, target_type=SnapshotTargetType.REVISION
            ),
        },
    )
    storage.snapshot_add([snapshot])
    visit_status = OriginVisitStatus(
        origin=origin_url,
        visit=visit.visit,
        date=date,
        type=visit.type,
        status="full",
        snapshot=snapshot.id,
    )
    storage.origin_visit_status_add([visit_status])
    return Response({}, status=200, content_type="application/json")
