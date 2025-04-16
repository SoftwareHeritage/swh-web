# Copyright (C) 2017-2025  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import pytest

from swh.web.utils import highlightjs


@pytest.mark.parametrize(
    "mime_type, language",
    [
        ("text/plain", "plaintext"),
        ("text/x-c", "c"),
        ("text/x-c++", "cpp"),
        ("text/x-perl", "perl"),
        ("text/x-python", "python"),
        ("text/x-msdos-batch", "dos"),
        ("text/x-tex", "latex"),
        ("text/x-lisp", "lisp"),
        ("text/x-java", "java"),
        ("text/x-makefile", "makefile"),
        ("text/x-shellscript", "bash"),
        ("text/html", "xml"),
        ("image/png", None),
    ],
)
def test_get_hljs_language_from_mime_type(mime_type, language):
    lang = highlightjs.get_hljs_language_from_mime_type(mime_type)
    assert lang == language


@pytest.mark.parametrize(
    "filename, language",
    [
        ("foo", None),
        ("foo.h", "c"),
        ("foo.c", "c"),
        ("foo.c.in", "c"),
        ("foo.cpp", "cpp"),
        ("foo.pl", "perl"),
        ("foo.py", "python"),
        ("foo.md", "markdown"),
        ("foo.js", "javascript"),
        ("foo.bat", "dos"),
        ("foo.json", "json"),
        ("foo.yml", "yaml"),
        ("foo.ini", "ini"),
        ("foo.cfg", "ini"),
        ("foo.hy", "hy"),
        ("foo.lisp", "lisp"),
        ("foo.java", "java"),
        ("foo.sh", "bash"),
        ("foo.cmake", "cmake"),
        ("foo.ml", "ocaml"),
        ("foo.mli", "ocaml"),
        ("foo.rb", "ruby"),
        ("foo.jl", "julia"),
        ("Makefile", "makefile"),
        ("CMakeLists.txt", "cmake"),
        ("robots.txt", "robots-txt"),
    ],
)
def test_get_hljs_language_from_filename(filename, language):
    lang = highlightjs.get_hljs_language_from_filename(filename)
    assert lang == language


def test_hljs_languages_aliases():
    for alias, language in highlightjs._hljs_languages_aliases().items():
        lang = highlightjs.get_hljs_language_from_filename(f"foo.{alias}")
        assert lang == language
