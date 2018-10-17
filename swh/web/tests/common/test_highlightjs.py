# Copyright (C) 2017-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


from swh.web.common import highlightjs
from swh.web.tests.testcase import SWHWebTestCase


class HighlightJsTestCase(SWHWebTestCase):

    def test_get_hljs_language_from_mime_type(self):

        lang = highlightjs.get_hljs_language_from_mime_type('text/plain')
        self.assertEquals(lang, None)

        lang = highlightjs.get_hljs_language_from_mime_type('text/x-c')
        self.assertEquals(lang, 'cpp')

        lang = highlightjs.get_hljs_language_from_mime_type('text/x-c++')
        self.assertEquals(lang, 'cpp')

        lang = highlightjs.get_hljs_language_from_mime_type('text/x-perl')
        self.assertEquals(lang, 'perl')

        lang = highlightjs.get_hljs_language_from_mime_type('text/x-python')
        self.assertEquals(lang, 'python')

        lang = highlightjs.get_hljs_language_from_mime_type('text/x-msdos-batch') # noqa
        self.assertEquals(lang, 'dos')

        lang = highlightjs.get_hljs_language_from_mime_type('text/x-tex')
        self.assertEquals(lang, 'tex')

        lang = highlightjs.get_hljs_language_from_mime_type('text/x-lisp')
        self.assertEquals(lang, 'lisp')

        lang = highlightjs.get_hljs_language_from_mime_type('text/x-java')
        self.assertEquals(lang, 'java')

        lang = highlightjs.get_hljs_language_from_mime_type('text/x-makefile')
        self.assertEquals(lang, 'makefile')

        lang = highlightjs.get_hljs_language_from_mime_type('text/x-shellscript') # noqa
        self.assertEquals(lang, 'bash')

        lang = highlightjs.get_hljs_language_from_mime_type('image/png')
        self.assertEquals(lang, None)

    def test_get_hljs_language_from_filename(self):

        lang = highlightjs.get_hljs_language_from_filename('foo')
        self.assertEquals(lang, None)

        lang = highlightjs.get_hljs_language_from_filename('foo.h')
        self.assertEquals(lang, 'cpp')

        lang = highlightjs.get_hljs_language_from_filename('foo.c')
        self.assertEquals(lang, 'cpp')

        lang = highlightjs.get_hljs_language_from_filename('foo.c.in')
        self.assertEquals(lang, 'cpp')

        lang = highlightjs.get_hljs_language_from_filename('foo.cpp')
        self.assertEquals(lang, 'cpp')

        lang = highlightjs.get_hljs_language_from_filename('foo.pl')
        self.assertEquals(lang, 'perl')

        lang = highlightjs.get_hljs_language_from_filename('foo.py')
        self.assertEquals(lang, 'python')

        lang = highlightjs.get_hljs_language_from_filename('foo.md')
        self.assertEquals(lang, 'markdown')

        lang = highlightjs.get_hljs_language_from_filename('foo.js')
        self.assertEquals(lang, 'javascript')

        lang = highlightjs.get_hljs_language_from_filename('foo.bat')
        self.assertEquals(lang, 'dos')

        lang = highlightjs.get_hljs_language_from_filename('foo.json')
        self.assertEquals(lang, 'json')

        lang = highlightjs.get_hljs_language_from_filename('foo.yml')
        self.assertEquals(lang, 'yaml')

        lang = highlightjs.get_hljs_language_from_filename('foo.ini')
        self.assertEquals(lang, 'ini')

        lang = highlightjs.get_hljs_language_from_filename('foo.cfg')
        self.assertEquals(lang, 'ini')

        lang = highlightjs.get_hljs_language_from_filename('foo.hy')
        self.assertEquals(lang, 'hy')

        lang = highlightjs.get_hljs_language_from_filename('foo.lisp')
        self.assertEquals(lang, 'lisp')

        lang = highlightjs.get_hljs_language_from_filename('foo.java')
        self.assertEquals(lang, 'java')

        lang = highlightjs.get_hljs_language_from_filename('foo.sh')
        self.assertEquals(lang, 'bash')

        lang = highlightjs.get_hljs_language_from_filename('foo.cmake')
        self.assertEquals(lang, 'cmake')

        lang = highlightjs.get_hljs_language_from_filename('foo.ml')
        self.assertEquals(lang, 'ocaml')

        lang = highlightjs.get_hljs_language_from_filename('foo.mli')
        self.assertEquals(lang, 'ocaml')

        lang = highlightjs.get_hljs_language_from_filename('foo.rb')
        self.assertEquals(lang, 'ruby')

        lang = highlightjs.get_hljs_language_from_filename('foo.jl')
        self.assertEquals(lang, 'julia')

        lang = highlightjs.get_hljs_language_from_filename('Makefile')
        self.assertEquals(lang, 'makefile')

        lang = highlightjs.get_hljs_language_from_filename('CMakeLists.txt')
        self.assertEquals(lang, 'cmake')
