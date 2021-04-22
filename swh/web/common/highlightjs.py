# Copyright (C) 2017-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import functools
import json
from typing import Dict

from pygments.lexers import get_all_lexers, get_lexer_for_filename
import sentry_sdk

from django.contrib.staticfiles.finders import find


@functools.lru_cache()
def _hljs_languages_data():
    with open(str(find("json/highlightjs-languages.json")), "r") as hljs_languages_file:
        return json.load(hljs_languages_file)


# set of languages ids that can be highlighted by highlight.js library
@functools.lru_cache()
def _hljs_languages():
    return set(_hljs_languages_data()["languages"])


# languages aliases defined in highlight.js
@functools.lru_cache()
def _hljs_languages_aliases():
    return {
        **_hljs_languages_data()["languages_aliases"],
        "ml": "ocaml",
        "bsl": "1c",
        "ep": "mojolicious",
        "lc": "livecode",
        "p": "parser3",
        "pde": "processing",
        "rsc": "routeros",
        "s": "armasm",
        "sl": "rsl",
    }


# dictionary mapping pygment lexers to hljs languages
_pygments_lexer_to_hljs_language = {}  # type: Dict[str, str]


# dictionary mapping mime types to hljs languages
_mime_type_to_hljs_language = {
    "text/x-c": "c",
    "text/x-c++": "cpp",
    "text/x-msdos-batch": "dos",
    "text/x-lisp": "lisp",
    "text/x-shellscript": "bash",
}

# dictionary mapping filenames to hljs languages
_filename_to_hljs_language = {
    "cmakelists.txt": "cmake",
    ".htaccess": "apache",
    "httpd.conf": "apache",
    "access.log": "accesslog",
    "nginx.log": "accesslog",
    "resolv.conf": "dns",
    "dockerfile": "docker",
    "nginx.conf": "nginx",
    "pf.conf": "pf",
}


# function to fill the above dictionaries
def _init_pygments_to_hljs_map():
    if len(_pygments_lexer_to_hljs_language) == 0:
        for lexer in get_all_lexers():
            lexer_name = lexer[0]
            lang_aliases = lexer[1]
            lang_mime_types = lexer[3]
            lang = None
            for lang_alias in lang_aliases:
                if lang_alias in _hljs_languages():
                    lang = lang_alias
                    _pygments_lexer_to_hljs_language[lexer_name] = lang_alias
                    break

            if lang:
                for lang_mime_type in lang_mime_types:
                    if lang_mime_type not in _mime_type_to_hljs_language:
                        _mime_type_to_hljs_language[lang_mime_type] = lang


def get_hljs_language_from_filename(filename):
    """Function that tries to associate a language supported by highlight.js
    from a filename.

    Args:
        filename: input filename

    Returns:
        highlight.js language id or None if no correspondence has been found
    """
    _init_pygments_to_hljs_map()
    if filename:
        filename_lower = filename.lower()
        if filename_lower in _filename_to_hljs_language:
            return _filename_to_hljs_language[filename_lower]
        if filename_lower in _hljs_languages():
            return filename_lower
        exts = filename_lower.split(".")
        # check if file extension matches an hljs language
        # also handle .ext.in cases
        for ext in reversed(exts[-2:]):
            if ext in _hljs_languages():
                return ext
            if ext in _hljs_languages_aliases():
                return _hljs_languages_aliases()[ext]

        # otherwise use Pygments language database
        lexer = None
        # try to find a Pygment lexer
        try:
            lexer = get_lexer_for_filename(filename)
        except Exception as exc:
            sentry_sdk.capture_exception(exc)
        # if there is a correspondence between the lexer and an hljs
        # language, return it
        if lexer and lexer.name in _pygments_lexer_to_hljs_language:
            return _pygments_lexer_to_hljs_language[lexer.name]
        # otherwise, try to find a match between the file extensions
        # associated to the lexer and the hljs language aliases
        if lexer:
            exts = [ext.replace("*.", "") for ext in lexer.filenames]
            for ext in exts:
                if ext in _hljs_languages_aliases():
                    return _hljs_languages_aliases()[ext]
    return None


def get_hljs_language_from_mime_type(mime_type):
    """Function that tries to associate a language supported by highlight.js
    from a mime type.

    Args:
        mime_type: input mime type

    Returns:
        highlight.js language id or None if no correspondence has been found
    """
    _init_pygments_to_hljs_map()
    if mime_type and mime_type in _mime_type_to_hljs_language:
        return _mime_type_to_hljs_language[mime_type]
    return None


@functools.lru_cache()
def get_supported_languages():
    """
    Return the list of programming languages that can be highlighted using the
    highlight.js library.

    Returns:
        List[str]: the list of supported languages
    """
    return sorted(list(_hljs_languages()))
