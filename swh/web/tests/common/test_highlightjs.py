# Copyright (C) 2017-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


from swh.web.common import highlightjs


def test_get_hljs_language_from_mime_type():
    lang = highlightjs.get_hljs_language_from_mime_type("text/plain")
    assert lang == "plaintext"

    lang = highlightjs.get_hljs_language_from_mime_type("text/x-c")
    assert lang == "c"

    lang = highlightjs.get_hljs_language_from_mime_type("text/x-c++")
    assert lang == "cpp"

    lang = highlightjs.get_hljs_language_from_mime_type("text/x-perl")
    assert lang == "perl"

    lang = highlightjs.get_hljs_language_from_mime_type("text/x-python")
    assert lang == "python"

    lang = highlightjs.get_hljs_language_from_mime_type("text/x-msdos-batch")
    assert lang == "dos"

    lang = highlightjs.get_hljs_language_from_mime_type("text/x-tex")
    assert lang == "latex"

    lang = highlightjs.get_hljs_language_from_mime_type("text/x-lisp")
    assert lang == "lisp"

    lang = highlightjs.get_hljs_language_from_mime_type("text/x-java")
    assert lang == "java"

    lang = highlightjs.get_hljs_language_from_mime_type("text/x-makefile")
    assert lang == "makefile"

    lang = highlightjs.get_hljs_language_from_mime_type("text/x-shellscript")
    assert lang == "bash"

    lang = highlightjs.get_hljs_language_from_mime_type("text/html")
    assert lang == "xml"

    lang = highlightjs.get_hljs_language_from_mime_type("image/png")
    assert lang is None


def test_get_hljs_language_from_filename():

    for filename, language in (
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
    ):
        lang = highlightjs.get_hljs_language_from_filename(filename)
        assert lang == language

    for alias, language in highlightjs._hljs_languages_aliases().items():
        lang = highlightjs.get_hljs_language_from_filename(f"foo.{alias}")
        assert lang == language
