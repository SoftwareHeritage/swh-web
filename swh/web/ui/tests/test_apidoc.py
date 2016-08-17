# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


import json
import yaml

from unittest.mock import MagicMock, patch
from nose.tools import istest

from flask import Response

from swh.web.ui import apidoc
from swh.web.ui.tests import test_app


class APIDocTestCase(test_app.SWHApidocTestCase):

    def setUp(self):
        self.arg_dict = {
            'name': 'my_pretty_arg',
            'default': 'some default value',
            'type': 'str',
            'doc': 'this arg does things'
        }
        self.stub_excs = [{'exc': 'catastrophic_exception',
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
            'type': 'some_return_type',
            'doc': 'a dict with amazing properties'
        }

    @patch('swh.web.ui.apidoc.APIUrls')
    @patch('swh.web.ui.apidoc.app')
    @istest
    def apidoc_route(self, mock_app, mock_api_urls):
        # given
        decorator = apidoc.route('/some/url/for/doc/')
        mock_fun = MagicMock(return_value=123)
        mock_fun.__doc__ = 'Some documentation'
        mock_fun.__name__ = 'some_fname'
        decorated = decorator.__call__(mock_fun)

        # when
        decorated('some', 'value', kws='and a kw')

        # then
        mock_fun.assert_called_once_with(
            call_args=(('some', 'value'), {'kws': 'and a kw'}),
            doc_route='/some/url/for/doc/',
            noargs=False
        )
        mock_api_urls.index_add_route.assert_called_once_with(
            '/some/url/for/doc/',
            'Some documentation')
        mock_app.add_url_rule.assert_called_once_with(
            '/some/url/for/doc/', 'some_fname', decorated)

    @istest
    def apidoc_arg_noprevious(self):
        # given
        decorator = apidoc.arg('my_pretty_arg',
                               default='some default value',
                               argtype='str',
                               argdoc='this arg does things')
        mock_fun = MagicMock(return_value=123)
        decorated = decorator.__call__(mock_fun)

        # when
        decorated(call_args=((), {}), doc_route='some/route/')

        # then
        mock_fun.assert_called_once_with(
            call_args=((), {}),
            doc_route='some/route/',
            args=[self.arg_dict]
        )

    @istest
    def apidoc_arg_previous(self):
        # given
        decorator = apidoc.arg('my_other_arg',
                               default='some other value',
                               argtype='str',
                               argdoc='this arg is optional')
        mock_fun = MagicMock(return_value=123)
        decorated = decorator.__call__(mock_fun)

        # when
        decorated(call_args=((), {}),
                  doc_route='some/route/',
                  args=[self.arg_dict])

        # then
        mock_fun.assert_called_once_with(
            call_args=((), {}),
            doc_route='some/route/',
            args=[self.arg_dict,
                  {'name': 'my_other_arg',
                   'default': 'some other value',
                   'type': 'str',
                   'doc': 'this arg is optional'}])

    @istest
    def apidoc_raises_noprevious(self):
        # given
        decorator = apidoc.raises(exc='catastrophic_exception',
                                  doc='My exception documentation')
        mock_fun = MagicMock(return_value=123)
        decorated = decorator.__call__(mock_fun)

        # when
        decorated(call_args=((), {}), doc_route='some/route/')

        # then
        mock_fun.assert_called_once_with(
            call_args=((), {}),
            doc_route='some/route/',
            excs=self.stub_excs
        )

    @istest
    def apidoc_raises_previous(self):
        # given
        decorator = apidoc.raises(exc='cataclysmic_exception',
                                  doc='Another documentation')
        mock_fun = MagicMock(return_value=123)
        decorated = decorator.__call__(mock_fun)
        expected_excs = self.stub_excs + [{
            'exc': 'cataclysmic_exception',
            'doc': 'Another documentation'}]

        # when
        decorated(call_args=((), {}),
                  doc_route='some/route/',
                  excs=self.stub_excs)

        # then
        mock_fun.assert_called_once_with(
            call_args=((), {}),
            doc_route='some/route/',
            excs=expected_excs)

    @patch('swh.web.ui.apidoc.render_template')
    @patch('swh.web.ui.apidoc.url_for')
    @patch('swh.web.ui.apidoc.APIUrls')
    @patch('swh.web.ui.apidoc.request')
    @istest
    def apidoc_returns_doc_call(self,
                                mock_request,
                                mock_api_urls,
                                mock_url_for,
                                mock_render):
        # given
        decorator = apidoc.returns(rettype='some_return_type',
                                   retdoc='a dict with amazing properties')
        mock_fun = MagicMock(return_value=123)
        mock_fun.__name__ = 'some_fname'
        mock_fun.__doc__ = 'Some documentation'
        decorated = decorator.__call__(mock_fun)

        mock_api_urls.get_method_endpoints.return_value = self.stub_rule_list

        mock_request.url = 'http://my-domain.tld/some/doc/route/'
        mock_url_for.return_value = 'http://my-domain.tld/meaningful_route/'

        expected_env = {
            'urls': [{'rule': 'some/route/with/args/',
                      'methods': {'GET', 'HEAD', 'OPTIONS'}},
                     {'rule': 'some/other/route/',
                      'methods': {'GET', 'HEAD', 'OPTIONS'}}],
            'docstring': 'Some documentation',
            'args': self.stub_args,
            'excs': self.stub_excs,
            'route': 'some/doc/route/',
            'example': 'http://my-domain.tld/meaningful_route/',
            'return': self.stub_return
        }

        # when
        decorated(
            docstring='Some documentation',
            call_args=(('some', 'args'), {'kw': 'kwargs'}),
            args=self.stub_args,
            excs=self.stub_excs,
            doc_route='some/doc/route/',
            noargs=False
        )

        # then
        self.assertEqual(mock_fun.call_args_list, [])  # function not called
        mock_render.assert_called_once_with(
            'apidoc.html',
            **expected_env
        )

    @patch('swh.web.ui.apidoc.make_response_from_mimetype')
    @patch('swh.web.ui.apidoc.url_for')
    @patch('swh.web.ui.apidoc.APIUrls')
    @patch('swh.web.ui.apidoc.request')
    @istest
    def apidoc_returns_noargs(self,
                              mock_request,
                              mock_api_urls,
                              mock_url_for,
                              mock_make_resp):

        # given
        decorator = apidoc.returns(rettype='some_return_type',
                                   retdoc='a dict with amazing properties')
        mock_fun = MagicMock(return_value=123)
        mock_fun.__name__ = 'some_fname'
        mock_fun.__doc__ = 'Some documentation'
        decorated = decorator.__call__(mock_fun)

        mock_api_urls.get_method_endpoints.return_value = [
            {'rule': 'some/doc/route/',
             'methods': {'GET', 'HEAD', 'OPTIONS'}}]

        mock_request.url = 'http://my-domain.tld/some/doc/route/'

        # when
        decorated(
            call_args=((), {}),
            doc_route='some/doc/route/',
            noargs=True
        )

        # then
        mock_fun.assert_called_once_with()
        mock_make_resp.assert_called_once_with(
            123,
            {
                'urls': [
                    {'rule': 'some/doc/route/',
                     'methods': {'GET', 'HEAD', 'OPTIONS'}}],
                'docstring': 'Some documentation',
                'route': 'some/doc/route/',
                'return': {'type': 'some_return_type',
                           'doc': 'a dict with amazing properties'}
            }
        )

    @patch('swh.web.ui.apidoc.make_response_from_mimetype')
    @patch('swh.web.ui.apidoc.url_for')
    @patch('swh.web.ui.apidoc.APIUrls')
    @patch('swh.web.ui.apidoc.request')
    @istest
    def apidoc_return_endpoint_call(self,
                                    mock_request,
                                    mock_api_urls,
                                    mock_url_for,
                                    mock_resp):
        # given
        decorator = apidoc.returns(rettype='some_return_type',
                                   retdoc='a dict with amazing properties')
        mock_fun = MagicMock(return_value=123)
        mock_fun.__name__ = 'some_fname'
        mock_fun.__doc__ = 'Some documentation'
        decorated = decorator.__call__(mock_fun)

        mock_api_urls.get_method_endpoints.return_value = self.stub_rule_list

        mock_request.url = 'http://my-domain.tld/some/arg/route/'
        mock_url_for.return_value = 'http://my-domain.tld/some/arg/route'

        # when
        decorated(
            docstring='Some documentation',
            call_args=(('some', 'args'), {'kw': 'kwargs'}),
            args=self.stub_args,
            excs=self.stub_excs,
            noargs=False,
            doc_route='some/doc/route/',
        )

        # then
        mock_fun.assert_called_once_with('some', 'args', kw='kwargs')
        mock_resp.assert_called_with(
            123,
            {
                'urls': [{'rule': 'some/route/with/args/',
                          'methods': {'GET', 'HEAD', 'OPTIONS'}},
                         {'rule': 'some/other/route/',
                          'methods': {'GET', 'HEAD', 'OPTIONS'}}],
                'docstring': 'Some documentation',
                'args': self.stub_args,
                'excs': self.stub_excs,
                'route': 'some/doc/route/',
                'example': 'http://my-domain.tld/some/arg/route',
                'return': self.stub_return
            }
        )

    @patch('swh.web.ui.apidoc.json')
    @patch('swh.web.ui.apidoc.request')
    @patch('swh.web.ui.apidoc.render_template')
    @istest
    def apidoc_make_response_html(self,
                                  mock_render,
                                  mock_request,
                                  mock_json):
        # given
        data = {'data': [12, 34],
                'id': 'adc83b19e793491b1c6ea0fd8b46cd9f32e592fc'}
        env = {'my_key': 'my_display_value'}

        def mock_mimetypes(key):
            mimetypes = {
                'text/html': 10,
                'application/json': 0.1,
                'application/yaml': 0.1
            }
            return mimetypes[key]
        accept_mimetypes = MagicMock()
        accept_mimetypes.__getitem__.side_effect = mock_mimetypes
        accept_mimetypes.best_match = MagicMock(
            return_value='text/html')
        mock_request.accept_mimetypes = accept_mimetypes

        mock_json.dumps.return_value = json.dumps(data)

        expected_env = {
            'my_key': 'my_display_value',
            'response_data': json.dumps(data),
            'request': mock_request
        }

        # when
        rv = apidoc.make_response_from_mimetype(data, env)

        # then
        self.assertEqual(mock_request.accept_mimetypes['text/html'], 10)
        mock_render.assert_called_with(
            'apidoc.html',
            **expected_env
        )
        self.assertEqual(rv.mimetype, 'text/html')

    @patch('swh.web.ui.apidoc.json')
    @patch('swh.web.ui.apidoc.request')
    @istest
    def apidoc_make_response_json(self,
                                  mock_request,
                                  mock_json):
        # given
        data = {'data': [12, 34],
                'id': 'adc83b19e793491b1c6ea0fd8b46cd9f32e592fc'}
        env = {'my_key': 'my_display_value'}

        def mock_mimetypes(key):
            mimetypes = {
                'application/json': 10,
                'text/html': 0.1,
                'application/yaml': 0.1
            }
            return mimetypes[key]
        accept_mimetypes = MagicMock()
        accept_mimetypes.__getitem__.side_effect = mock_mimetypes
        accept_mimetypes.best_match = MagicMock(
            return_value='application/json')
        mock_request.accept_mimetypes = accept_mimetypes
        mock_json.dumps.return_value = json.dumps(data)

        # when
        rv = apidoc.make_response_from_mimetype(data, env)

        # then
        mock_json.dumps.assert_called_once_with(data)

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.mimetype, 'application/json')
        self.assertEqual(data, json.loads(rv.data.decode('utf-8')))

    @patch('swh.web.ui.apidoc.yaml')
    @patch('swh.web.ui.apidoc.request')
    @istest
    def apidoc_make_response_yaml(self,
                                  mock_request,
                                  mock_yaml):
        # given
        data = ['adc83b19e793491b1c6ea0fd8b46cd9f32e592fc']
        env = {'my_key': 'my_display_value'}

        def mock_mimetypes(key):
            mimetypes = {
                'application/yaml': 10,
                'application/json': 0.1,
                'text/html': 0.1
            }
            return mimetypes[key]
        accept_mimetypes = MagicMock()
        accept_mimetypes.__getitem__.side_effect = mock_mimetypes
        accept_mimetypes.best_match = MagicMock(
            return_value='application/yaml')
        mock_request.accept_mimetypes = accept_mimetypes
        mock_yaml.dump.return_value = yaml.dump(data)

        # when
        rv = apidoc.make_response_from_mimetype(data, env)

        # then
        mock_yaml.dump.assert_called_once_with(data)

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.mimetype, 'application/yaml')
        self.assertEqual(data, yaml.load(rv.data.decode('utf-8')))

    @istest
    def apidoc_make_response_not_list_dict(self):
        # given
        incoming = Response()

        # when
        rv = apidoc.make_response_from_mimetype(incoming, {})

        # then
        self.assertEqual(rv, incoming)
