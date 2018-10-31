# Copyright (C) 2017-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


from swh.web.common import highlightjs
from swh.web.tests.testcase import SWHWebTestCase


class HighlightJsTestCase(SWHWebTestCase):

    def test_get_hljs_language_from_mime_type(self):

        lang = highlightjs.get_hljs_language_from_mime_type('text/plain')
        self.assertEqual(lang, None)

        lang = highlightjs.get_hljs_language_from_mime_type('text/x-c')
        self.assertEqual(lang, 'cpp')

        lang = highlightjs.get_hljs_language_from_mime_type('text/x-c++')
        self.assertEqual(lang, 'cpp')

        lang = highlightjs.get_hljs_language_from_mime_type('text/x-perl')
        self.assertEqual(lang, 'perl')

        lang = highlightjs.get_hljs_language_from_mime_type('text/x-python')
        self.assertEqual(lang, 'python')

        lang = highlightjs.get_hljs_language_from_mime_type('text/x-msdos-batch') # noqa
        self.assertEqual(lang, 'dos')

        lang = highlightjs.get_hljs_language_from_mime_type('text/x-tex')
        self.assertEqual(lang, 'tex')

        lang = highlightjs.get_hljs_language_from_mime_type('text/x-lisp')
        self.assertEqual(lang, 'lisp')

        lang = highlightjs.get_hljs_language_from_mime_type('text/x-java')
        self.assertEqual(lang, 'java')

        lang = highlightjs.get_hljs_language_from_mime_type('text/x-makefile')
        self.assertEqual(lang, 'makefile')

        lang = highlightjs.get_hljs_language_from_mime_type('text/x-shellscript') # noqa
        self.assertEqual(lang, 'bash')

        lang = highlightjs.get_hljs_language_from_mime_type('image/png')
        self.assertEqual(lang, None)

    def test_get_hljs_language_from_filename(self):

        lang = highlightjs.get_hljs_language_from_filename('foo')
        self.assertEqual(lang, None)

        lang = highlightjs.get_hljs_language_from_filename('foo.h')
        self.assertEqual(lang, 'cpp')

        lang = highlightjs.get_hljs_language_from_filename('foo.c')
        self.assertEqual(lang, 'cpp')

        lang = highlightjs.get_hljs_language_from_filename('foo.c.in')
        self.assertEqual(lang, 'cpp')

        lang = highlightjs.get_hljs_language_from_filename('foo.cpp')
        self.assertEqual(lang, 'cpp')

        lang = highlightjs.get_hljs_language_from_filename('foo.pl')
        self.assertEqual(lang, 'perl')

        lang = highlightjs.get_hljs_language_from_filename('foo.py')
        self.assertEqual(lang, 'python')

        lang = highlightjs.get_hljs_language_from_filename('foo.md')
        self.assertEqual(lang, 'markdown')

        lang = highlightjs.get_hljs_language_from_filename('foo.js')
        self.assertEqual(lang, 'javascript')

        lang = highlightjs.get_hljs_language_from_filename('foo.bat')
        self.assertEqual(lang, 'dos')

        lang = highlightjs.get_hljs_language_from_filename('foo.json')
        self.assertEqual(lang, 'json')

        lang = highlightjs.get_hljs_language_from_filename('foo.yml')
        self.assertEqual(lang, 'yaml')

        lang = highlightjs.get_hljs_language_from_filename('foo.ini')
        self.assertEqual(lang, 'ini')

        lang = highlightjs.get_hljs_language_from_filename('foo.cfg')
        self.assertEqual(lang, 'ini')

        lang = highlightjs.get_hljs_language_from_filename('foo.hy')
        self.assertEqual(lang, 'hy')

        lang = highlightjs.get_hljs_language_from_filename('foo.lisp')
        self.assertEqual(lang, 'lisp')

        lang = highlightjs.get_hljs_language_from_filename('foo.java')
        self.assertEqual(lang, 'java')

        lang = highlightjs.get_hljs_language_from_filename('foo.sh')
        self.assertEqual(lang, 'bash')

        lang = highlightjs.get_hljs_language_from_filename('foo.cmake')
        self.assertEqual(lang, 'cmake')

        lang = highlightjs.get_hljs_language_from_filename('foo.ml')
        self.assertEqual(lang, 'ocaml')

        lang = highlightjs.get_hljs_language_from_filename('foo.mli')
        self.assertEqual(lang, 'ocaml')

        lang = highlightjs.get_hljs_language_from_filename('foo.rb')
        self.assertEqual(lang, 'ruby')

        lang = highlightjs.get_hljs_language_from_filename('foo.jl')
        self.assertEqual(lang, 'julia')

        lang = highlightjs.get_hljs_language_from_filename('Makefile')
        self.assertEqual(lang, 'makefile')

        lang = highlightjs.get_hljs_language_from_filename('CMakeLists.txt')
        self.assertEqual(lang, 'cmake')
