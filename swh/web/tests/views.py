# Copyright (C) 2018-2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

# Implement some special endpoints used to provide input tests data
# when executing end to end tests with cypress

import os

from typing import Dict

from rest_framework.decorators import api_view
from rest_framework.response import Response

from swh.model import from_disk
from swh.model.hashutil import hash_to_hex
from swh.model.model import Content
from swh.model.from_disk import DiskBackedContent
from swh.web.common.highlightjs import get_hljs_language_from_filename
from swh.web.tests.data import get_tests_data

_content_code_data_exts = {}  # type: Dict[str, Dict[str, str]]
_content_code_data_filenames = {}  # type: Dict[str, Dict[str, str]]
_content_other_data_exts = {}  # type: Dict[str, Dict[str, str]]


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
    for name, obj_ in directory.items():
        obj = obj_.to_model()
        if obj.object_type in [Content.object_type, DiskBackedContent.object_type]:
            c = obj.with_data().to_dict()
            c["status"] = "visible"
            sha1 = hash_to_hex(c["sha1"])
            if ext_key:
                key = name.decode("utf-8").split(".")[-1]
                filename = "test." + key
            else:
                filename = name.decode("utf-8").split("/")[-1]
                key = filename
            language = get_hljs_language_from_filename(filename)
            data_dict[key] = {"sha1": sha1, "language": language}
            contents.append(Content.from_dict(c))
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
