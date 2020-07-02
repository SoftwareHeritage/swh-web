# Copyright (C) 2017-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import functools
from typing import Dict

from pygments.lexers import get_all_lexers, get_lexer_for_filename
import sentry_sdk

# set of languages ids that can be highlighted
# by highlight.js library
_hljs_languages = set(
    [
        "1c",
        "abnf",
        "accesslog",
        "actionscript",
        "ada",
        "angelscript",
        "apache",
        "applescript",
        "arcade",
        "arduino",
        "armasm",
        "asciidoc",
        "aspectj",
        "autohotkey",
        "autoit",
        "avrasm",
        "awk",
        "axapta",
        "bash",
        "basic",
        "bnf",
        "brainfuck",
        "cal",
        "capnproto",
        "ceylon",
        "clean",
        "clojure",
        "clojure-repl",
        "cmake",
        "coffeescript",
        "coq",
        "cos",
        "cpp",
        "crmsh",
        "crystal",
        "cs",
        "csp",
        "css",
        "d",
        "dart",
        "delphi",
        "diff",
        "django",
        "dns",
        "dockerfile",
        "dos",
        "dsconfig",
        "dts",
        "dust",
        "ebnf",
        "elixir",
        "elm",
        "erb",
        "erlang",
        "erlang-repl",
        "excel",
        "fix",
        "flix",
        "fortran",
        "fsharp",
        "gams",
        "gauss",
        "gcode",
        "gherkin",
        "glsl",
        "gml",
        "go",
        "golo",
        "gradle",
        "groovy",
        "haml",
        "handlebars",
        "haskell",
        "haxe",
        "hsp",
        "htmlbars",
        "http",
        "hy",
        "inform7",
        "ini",
        "irpf90",
        "isbl",
        "java",
        "javascript",
        "jboss-cli",
        "json",
        "julia",
        "julia-repl",
        "kotlin",
        "lasso",
        "ldif",
        "leaf",
        "less",
        "lisp",
        "livecodeserver",
        "livescript",
        "llvm",
        "lsl",
        "lua",
        "makefile",
        "markdown",
        "mathematica",
        "matlab",
        "maxima",
        "mel",
        "mercury",
        "mipsasm",
        "mizar",
        "mojolicious",
        "monkey",
        "moonscript",
        "n1ql",
        "nginx",
        "nimrod",
        "nix",
        "nsis",
        "objectivec",
        "ocaml",
        "openscad",
        "oxygene",
        "parser3",
        "perl",
        "pf",
        "pgsql",
        "php",
        "plaintext",
        "pony",
        "powershell",
        "processing",
        "profile",
        "prolog",
        "properties",
        "protobuf",
        "puppet",
        "purebasic",
        "python",
        "q",
        "qml",
        "r",
        "reasonml",
        "rib",
        "roboconf",
        "routeros",
        "rsl",
        "ruby",
        "ruleslanguage",
        "rust",
        "sas",
        "scala",
        "scheme",
        "scilab",
        "scss",
        "shell",
        "smali",
        "smalltalk",
        "sml",
        "sqf",
        "sql",
        "stan",
        "stata",
        "step21",
        "stylus",
        "subunit",
        "swift",
        "taggerscript",
        "tap",
        "tcl",
        "tex",
        "thrift",
        "tp",
        "twig",
        "typescript",
        "vala",
        "vbnet",
        "vbscript",
        "vbscript-html",
        "verilog",
        "vhdl",
        "vim",
        "x86asm",
        "xl",
        "xml",
        "xquery",
        "yaml",
        "zephir",
    ]
)


# languages aliases defined in highlight.js
_hljs_languages_aliases = {
    "ado": "stata",
    "adoc": "asciidoc",
    "ahk": "autohotkey",
    "aj": "aspectj",
    "apacheconf": "apache",
    "arm": "armasm",
    "as": "actionscript",
    "asc": "asciidoc",
    "atom": "xml",
    "bas": "basic",
    "bat": "dos",
    "bf": "brainfuck",
    "bind": "dns",
    "bsl": "1c",
    "c-al": "cal",
    "c": "cpp",
    "c++": "cpp",
    "capnp": "capnproto",
    "cc": "cpp",
    "clj": "clojure",
    "cls": "cos",
    "cmake.in": "cmake",
    "cmd": "dos",
    "coffee": "coffeescript",
    "console": "shell",
    "cr": "crystal",
    "craftcms": "twig",
    "crm": "crmsh",
    "csharp": "cs",
    "cson": "coffeescript",
    "dcl": "clean",
    "dfm": "delphi",
    "do": "stata",
    "docker": "dockerfile",
    "dpr": "delphi",
    "dst": "dust",
    "dtsi": "dts",
    "ep": "mojolicious",
    "erl": "erlang",
    "ex": "elixir",
    "exs": "elixir",
    "f90": "fortran",
    "f95": "fortran",
    "feature": "gherkin",
    "freepascal": "delphi",
    "fs": "fsharp",
    "fsx": "fsharp",
    "gemspec": "ruby",
    "GML": "gml",
    "gms": "gams",
    "golang": "go",
    "graph": "roboconf",
    "gss": "gauss",
    "gyp": "python",
    "h": "cpp",
    "h++": "cpp",
    "hbs": "handlebars",
    "hpp": "cpp",
    "hs": "haskell",
    "html": "xml",
    "html.handlebars": "handlebars",
    "html.hbs": "handlebars",
    "https": "http",
    "hx": "haxe",
    "hylang": "hy",
    "i7": "inform7",
    "i7x": "inform7",
    "iced": "coffeescript",
    "icl": "clean",
    "ino": "arduino",
    "instances": "roboconf",
    "ipynb": "json",
    "irb": "ruby",
    "jinja": "django",
    "js": "javascript",
    "jsp": "java",
    "jsx": "javascript",
    "k": "q",
    "kdb": "q",
    "kt": "kotlin",
    "lassoscript": "lasso",
    "lazarus": "delphi",
    "lc": "livecode",
    "lfm": "delphi",
    "ll": "llvm",
    "lpr": "delphi",
    "ls": "livescript",
    "m": "matlab",
    "mak": "makefile",
    "md": "markdown",
    "mikrotik": "routeros",
    "mips": "mipsasm",
    "mk": "monkey",
    "mkd": "markdown",
    "mkdown": "markdown",
    "ml": "ocaml",
    "mli": "ocaml",
    "mm": "objectivec",
    "mma": "mathematica",
    "moo": "mercury",
    "moon": "moonscript",
    "nav": "cal",
    "nb": "mathematica",
    "nc": "gcode",
    "nginxconf": "nginx",
    "ni": "inform7",
    "nim": "nimrod",
    "nixos": "nix",
    "nsi": "nsis",
    "obj-c": "objectivec",
    "objc": "objectivec",
    "osascript": "applescript",
    "osl": "rsl",
    "p": "parser3",
    "p21": "step21",
    "pas": "delphi",
    "pascal": "delphi",
    "patch": "diff",
    "pb": "purebasic",
    "pbi": "purebasic",
    "pcmk": "crmsh",
    "pde": "processing",
    "pf.conf": "pf",
    "php3": "php",
    "php4": "php",
    "php5": "php",
    "php6": "php",
    "php7": "php",
    "pl": "perl",
    "plist": "xml",
    "pm": "perl",
    "podspec": "ruby",
    "postgres": "pgsql",
    "postgresql": "pgsql",
    "pp": "puppet",
    "proto": "protobuf",
    "ps": "powershell",
    "ps1": "powershell",
    "psd1": "powershell",
    "psm1": "powershell",
    "py": "python",
    "qt": "qml",
    "rb": "ruby",
    "re": "reasonml",
    "rei": "reasonml",
    "rs": "rust",
    "rsc": "routeros",
    "rss": "xml",
    "rst": "nohighlight",
    "s": "armasm",
    "SAS": "sas",
    "scad": "openscad",
    "sci": "scilab",
    "scm": "scheme",
    "sh": "bash",
    "sig": "sml",
    "sl": "rsl",
    "st": "smalltalk",
    "step": "step21",
    "stp": "step21",
    "styl": "stylus",
    "sv": "verilog",
    "svh": "verilog",
    "tao": "xl",
    "thor": "ruby",
    "tk": "tcl",
    "toml": "ini",
    "ts": "typescript",
    "txt": "nohighlight",
    "v": "coq",
    "vb": "vbnet",
    "vbs": "vbscript",
    "vhd": "vhdl",
    "wildfly-cli": "jboss-cli",
    "wl": "mathematica",
    "wls": "mathematica",
    "xhtml": "xml",
    "xjb": "xml",
    "xls": "excel",
    "xlsx": "excel",
    "xpath": "xquery",
    "xpo": "axapta",
    "xpp": "axapta",
    "xq": "xquery",
    "xqy": "xquery",
    "xsd": "xml",
    "xsl": "xml",
    "YAML": "yaml",
    "yml": "yaml",
    "zep": "zephir",
    "zone": "dns",
    "zsh": "bash",
}

# dictionary mapping pygment lexers to hljs languages
_pygments_lexer_to_hljs_language = {}  # type: Dict[str, str]


# dictionary mapping mime types to hljs languages
_mime_type_to_hljs_language = {
    "text/x-c": "cpp",
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
                if lang_alias in _hljs_languages:
                    lang = lang_alias
                    _pygments_lexer_to_hljs_language[lexer_name] = lang_alias
                    break

            if lang:
                for lang_mime_type in lang_mime_types:
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
        if filename_lower in _hljs_languages:
            return filename_lower
        exts = filename_lower.split(".")
        # check if file extension matches an hljs language
        # also handle .ext.in cases
        for ext in reversed(exts[-2:]):
            if ext in _hljs_languages:
                return ext
            if ext in _hljs_languages_aliases:
                return _hljs_languages_aliases[ext]

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
                if ext in _hljs_languages_aliases:
                    return _hljs_languages_aliases[ext]
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
    return sorted(list(_hljs_languages))
