# Copyright (C) 2017-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from pygments.lexers import (
    get_all_lexers,
    get_lexer_for_filename
)

# set of languages ids that can be highlighted
# by highlight.js library
_hljs_languages = set([
    '1c', 'abnf', 'accesslog', 'actionscript',
    'ada', 'apache', 'applescript', 'arduino',
    'armasm', 'asciidoc', 'aspectj', 'autohotkey',
    'autoit', 'avrasm', 'awk', 'axapta', 'bash',
    'basic', 'bnf', 'brainfuck', 'cal', 'capnproto',
    'ceylon', 'clean', 'clojure', 'clojure-repl',
    'cmake', 'coffeescript', 'coq', 'cos', 'cpp',
    'crmsh', 'crystal', 'cs', 'csp', 'css', 'dart',
    'delphi', 'diff', 'django', 'd', 'dns', 'dockerfile',
    'dos', 'dsconfig', 'dts', 'dust', 'ebnf', 'elixir',
    'elm', 'erb', 'erlang', 'erlang-repl', 'excel',
    'fix', 'flix', 'fortran', 'fsharp', 'gams', 'gauss',
    'gcode', 'gherkin', 'glsl', 'go', 'golo', 'gradle',
    'groovy', 'haml', 'handlebars', 'haskell', 'haxe',
    'hsp', 'htmlbars', 'http', 'hy', 'inform7',
    'ini', 'irpf90', 'java', 'javascript', 'jboss-cli',
    'json', 'julia', 'julia-repl', 'kotlin', 'lasso',
    'ldif', 'leaf', 'less', 'lisp', 'livecodeserver',
    'livescript', 'llvm', 'lsl', 'lua', 'makefile',
    'markdown', 'mathematica', 'matlab', 'maxima',
    'mel', 'mercury', 'mipsasm', 'mizar', 'mojolicious',
    'monkey', 'moonscript', 'n1ql', 'nginx', 'nimrod',
    'nix', 'nsis', 'objectivec', 'ocaml', 'openscad',
    'oxygene', 'parser3', 'perl', 'pf', 'php', 'pony',
    'powershell', 'processing', 'profile', 'prolog',
    'protobuf', 'puppet', 'purebasic', 'python', 'q',
    'qml', 'rib', 'r', 'roboconf', 'routeros', 'rsl',
    'ruby', 'ruleslanguage', 'rust', 'scala', 'scheme',
    'scilab', 'scss', 'shell', 'smali', 'smalltalk',
    'sml', 'sqf', 'sql', 'stan', 'stata', 'step21',
    'stylus', 'subunit', 'swift', 'taggerscript',
    'tap', 'tcl', 'tex', 'thrift', 'tp', 'twig',
    'typescript', 'vala', 'vbnet', 'vbscript-html',
    'vbscript', 'verilog', 'vhdl', 'vim', 'x86asm',
    'xl', 'xml', 'xquery', 'yaml', 'zephir',
])

# languages aliases defined in highlight.js
_hljs_languages_aliases = {
    'ado': 'stata',
    'adoc': 'asciidoc',
    'ahk': 'autohotkey',
    'apacheconf': 'apache',
    'arm': 'armasm',
    'as': 'actionscript',
    'atom': 'xml',
    'bat': 'dos',
    'bf': 'brainfuck',
    'bind': 'dns',
    'c': 'cpp',
    'c++': 'cpp',
    'capnp': 'capnproto',
    'cc': 'cpp',
    'clean': 'clean',
    'clj': 'clojure',
    'cls': 'cos',
    'cmake.in': 'cmake',
    'cmd': 'dos',
    'coffee': 'coffeescript',
    'console': 'shell',
    'cos': 'cos',
    'cr': 'crystal',
    'craftcms': 'twig',
    'crm': 'crmsh',
    'csharp': 'cs',
    'cson': 'coffeescript',
    'dcl': 'clean',
    'desktop': 'ini',
    'dfm': 'delphi',
    'do': 'stata',
    'docker': 'dockerfile',
    'dpr': 'delphi',
    'dst': 'dust',
    'el': 'lisp',
    'erl': 'erlang',
    'f90': 'fortran',
    'f95': 'fortran',
    'feature': 'gherkin',
    'freepascal': 'delphi',
    'fs': 'fsharp',
    'gemspec': 'ruby',
    'gms': 'gams',
    'golang': 'go',
    'graph': 'roboconf',
    'gss': 'gauss',
    'gyp': 'python',
    'h': 'cpp',
    'h++': 'cpp',
    'hbs': 'handlebars',
    'hpp': 'cpp',
    'hs': 'haskell',
    'html': 'xml',
    'html.handlebars': 'handlebars',
    'html.hbs': 'handlebars',
    'https': 'http',
    'hx': 'haxe',
    'hylang': 'hy',
    'i7': 'inform7',
    'iced': 'coffeescript',
    'icl': 'clean',
    'instances': 'roboconf',
    'ipynb': 'json',
    'irb': 'ruby',
    'jinja': 'django',
    'js': 'javascript',
    'jsp': 'java',
    'jsx': 'javascript',
    'k': 'q',
    'kdb': 'q',
    'lassoscript': 'lasso',
    'lazarus': 'delphi',
    'lfm': 'delphi',
    'lpr': 'delphi',
    'ls': 'livescript',
    'm': 'objectivec',
    'mak': 'makefile',
    'md': 'markdown',
    'mikrotik': 'routeros',
    'mips': 'mipsasm',
    'mk': 'makefile',
    'mkd': 'markdown',
    'mkdown': 'markdown',
    'markdown': 'markdown',
    'ml': 'ocaml',
    'mm': 'objectivec',
    'mma': 'mathematica',
    'moo': 'mercury',
    'moon': 'moonscript',
    'nc': 'gcode',
    'nginxconf': 'nginx',
    'nim': 'nimrod',
    'nixos': 'nix',
    'obj-c': 'objectivec',
    'objc': 'objectivec',
    'osascript': 'applescript',
    'p21': 'step21',
    'pas': 'delphi',
    'pascal': 'delphi',
    'patch': 'diff',
    'pb': 'purebasic',
    'pbi': 'purebasic',
    'pcmk': 'crmsh',
    'pf.conf': 'pf',
    'php3': 'php',
    'php4': 'php',
    'php5': 'php',
    'php6': 'php',
    'pl': 'perl',
    'plist': 'xml',
    'pm': 'perl',
    'podspec': 'ruby',
    'pp': 'puppet',
    'ps': 'powershell',
    'py': 'python',
    'qrc': 'xml',
    'qs': 'javascript',
    'qt': 'qml',
    'rb': 'ruby',
    'routeros': 'routeros',
    'rs': 'rust',
    'rst': 'nohighlight',
    'rss': 'xml',
    'ru': 'ruby',
    'scad': 'openscad',
    'sci': 'scilab',
    'scpt': 'applescript',
    'sh': 'bash',
    'smali': 'smali',
    'sqf': 'sqf',
    'st': 'smalltalk',
    'step': 'step21',
    'stp': 'step21',
    'styl': 'stylus',
    'sv': 'verilog',
    'svh': 'verilog',
    'tao': 'xl',
    'thor': 'ruby',
    'tk': 'tcl',
    'toml': 'ini',
    'ui': 'xml',
    'v': 'verilog',
    'vb': 'vbnet',
    'vbs': 'vbscript',
    'wildfly-cli': 'jboss-cli',
    'xhtml': 'xml',
    'xjb': 'xml',
    'xls': 'excel',
    'xlsx': 'excel',
    'xpath': 'xquery',
    'xq': 'xquery',
    'xsd': 'xml',
    'xsl': 'xml',
    'yaml': 'yaml',
    'yml': 'yaml',
    'zep': 'zephir',
    'zone': 'dns',
    'zsh': 'bash'
}

# dictionary mapping pygment lexers to hljs languages
_pygments_lexer_to_hljs_language = {}


# dictionary mapping mime types to hljs languages
_mime_type_to_hljs_language = {
    'text/x-c': 'cpp',
    'text/x-c++': 'cpp',
    'text/x-msdos-batch': 'dos',
    'text/x-lisp': 'lisp',
    'text/x-shellscript': 'bash',
}


# function to fill the above dictionnaries
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
        exts = filename.lower().split('.')
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
        except Exception:
            pass
        # if there is a correspondence between the lexer and an hljs
        # language, return it
        if lexer and lexer.name in _pygments_lexer_to_hljs_language:
            return _pygments_lexer_to_hljs_language[lexer.name]
        # otherwise, try to find a match between the file extensions
        # associated to the lexer and the hljs language aliases
        if lexer:
            exts = [ext.replace('*.', '') for ext in lexer.filenames]
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
