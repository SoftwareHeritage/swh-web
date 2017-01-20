# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


from nose.tools import istest, nottest

from swh.web.ui import apidoc
from swh.web.ui.main import app
from swh.web.ui.tests.test_app import SWHApidocTestCase


class APIDocTestCase(SWHApidocTestCase):

    def setUp(self):

        self.arg_dict = {
            'name': 'my_pretty_arg',
            'default': 'some default value',
            'type': apidoc.argtypes.sha1,
            'doc': 'this arg does things'
        }
        self.stub_excs = [{'exc': apidoc.excs.badinput,
                           'doc': 'My exception documentation'}]
        self.stub_args = [{'name': 'stub_arg',
                           'default': 'some_default'}]
        self.stub_rule_list = [
            {'rule': 'some/route/with/args/',
             'methods': {'GET', 'HEAD', 'OPTIONS'}},
            {'rule': 'some/doc/route/',
             'methods': {'GET', 'HEAD', 'OPTIONS'}},
            {'rule': 'some/other/route/',
             'methods': {'GET', 'HEAD', 'OPTIONS'}}
        ]
        self.stub_return = {
            'type': apidoc.rettypes.dict.value,
            'doc': 'a dict with amazing properties'
        }

    @staticmethod
    @apidoc.route('/my/nodoc/url/')
    @nottest
    def apidoc_nodoc_tester(arga, argb):
        return arga + argb

    @istest
    def apidoc_nodoc_failure(self):
        with self.assertRaises(Exception):
            self.client.get('/my/nodoc/url/')

    @istest
    def apidoc_badorder_failure(self):
        with self.assertRaises(AssertionError):
            @app.route('/my/badorder/url/<int:foo>/')
            @apidoc.arg('foo',
                        default=True,
                        argtype=apidoc.argtypes.int,
                        argdoc='It\'s so fluffy!')
            @apidoc.route('/my/badorder/url/')
            @nottest
            def apidoc_badorder_tester(foo, bar=0):
                """
                Some irrelevant doc since the decorators are bad
                """
                return foo + bar

    @staticmethod
    @app.route('/some/<int:myarg>/<int:myotherarg>/')
    @apidoc.route('/some/doc/route/')
    @nottest
    def apidoc_route_tester(myarg, myotherarg, akw=0):
        """
        Sample doc
        """
        return {'result': myarg + myotherarg + akw}

    @istest
    def apidoc_route_doc(self):
        # when
        rv = self.client.get('/some/doc/route/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('apidoc.html')

    @istest
    def apidoc_route_fn(self):

        # when
        rv = self.client.get('/some/1/1/')

        # then
        self.assertEqual(rv.status_code, 200)

    @staticmethod
    @app.route('/some/full/<int:myarg>/<int:myotherarg>/')
    @apidoc.route('/some/complete/doc/route/')
    @apidoc.arg('myarg',
                default=67,
                argtype=apidoc.argtypes.int,
                argdoc='my arg')
    @apidoc.param('limit', default=10, doc='Result limitation')
    @apidoc.header('Link', doc='Header link returns for pagination purpose')
    @apidoc.raises(exc=apidoc.excs.badinput, doc='Oops')
    @apidoc.returns(rettype=apidoc.rettypes.dict,
                    retdoc='sum of args')
    @nottest
    def apidoc_full_stack_tester(myarg, myotherarg, akw=0):
        """
        Sample doc
        """
        return {'result': myarg + myotherarg + akw}

    @istest
    def apidoc_full_stack_doc(self):
        # when
        rv = self.client.get('/some/complete/doc/route/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('apidoc.html')

    @istest
    def apidoc_full_stack_fn(self):
        # when
        rv = self.client.get('/some/full/1/1/')

        # then
        self.assertEqual(rv.status_code, 200)
