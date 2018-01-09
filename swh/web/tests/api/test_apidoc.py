# Copyright (C) 2015-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from nose.tools import istest, nottest
from rest_framework.test import APITestCase
from rest_framework.response import Response

from swh.web.api import apidoc
from swh.web.api.apiurls import api_route
from swh.web.tests.testbase import SWHWebTestBase


class APIDocTestCase(SWHWebTestBase, APITestCase):

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
    def apidoc_nodoc_tester(request, arga=0, argb=0):
        return Response(arga + argb)

    @istest
    def apidoc_nodoc_failure(self):
        with self.assertRaises(Exception):
            self.client.get('/api/1/my/nodoc/url/')

    @staticmethod
    @api_route(r'/some/(?P<myarg>[0-9]+)/(?P<myotherarg>[0-9]+)/',
               'some-doc-route')
    @apidoc.route('/some/doc/route/')
    @nottest
    def apidoc_route_tester(request, myarg, myotherarg, akw=0):
        """
        Sample doc
        """
        return {'result': int(myarg) + int(myotherarg) + akw}

    @istest
    def apidoc_route_doc(self):
        # when
        rv = self.client.get('/api/1/some/doc/route/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assertTemplateUsed('apidoc.html')

    @istest
    def apidoc_route_fn(self):

        # when
        rv = self.client.get('/api/1/some/1/1/')

        # then
        self.assertEqual(rv.status_code, 200)

    @staticmethod
    @api_route(r'/some/full/(?P<myarg>[0-9]+)/(?P<myotherarg>[0-9]+)/',
               'some-complete-doc-route')
    @apidoc.route('/some/complete/doc/route/')
    @apidoc.arg('myarg',
                default=67,
                argtype=apidoc.argtypes.int,
                argdoc='my arg')
    @apidoc.arg('myotherarg',
                default=42,
                argtype=apidoc.argtypes.int,
                argdoc='my other arg')
    @apidoc.param('limit', argtype=apidoc.argtypes.int, default=10,
                  doc='Result limitation')
    @apidoc.header('Link', doc='Header link returns for pagination purpose')
    @apidoc.raises(exc=apidoc.excs.badinput, doc='Oops')
    @apidoc.returns(rettype=apidoc.rettypes.dict,
                    retdoc='sum of args')
    @nottest
    def apidoc_full_stack_tester(request, myarg, myotherarg, akw=0):
        """
        Sample doc
        """
        return {'result': int(myarg) + int(myotherarg) + akw}

    @istest
    def apidoc_full_stack_doc(self):
        # when
        rv = self.client.get('/api/1/some/complete/doc/route/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assertTemplateUsed('apidoc.html')

    @istest
    def apidoc_full_stack_fn(self):
        # when
        rv = self.client.get('/api/1/some/full/1/1/')

        # then
        self.assertEqual(rv.status_code, 200)
