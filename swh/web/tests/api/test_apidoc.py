# Copyright (C) 2015-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from rest_framework.test import APITestCase
from rest_framework.response import Response

from swh.web.api.apidoc import api_doc, _parse_httpdomain_doc
from swh.web.api.apiurls import api_route
from swh.web.tests.testcase import SWHWebTestCase

# flake8: noqa

httpdomain_doc = """
.. http:get:: /api/1/revision/(sha1_git)/

    Get information about a revision in the archive.
    Revisions are identified by **sha1** checksums, compatible with Git commit identifiers.
    See :func:`swh.model.identifiers.revision_identifier` in our data model module for details
    about how they are computed.

    :param string sha1_git: hexadecimal representation of the revision **sha1_git** identifier

    :reqheader Accept: the requested response content type,
        either ``application/json`` (default) or ``application/yaml``
    :resheader Content-Type: this depends on :http:header:`Accept` header of request

    :>json object author: information about the author of the revision
    :>json string author_url: link to :http:get:`/api/1/person/(person_id)/` to get
        information about the author of the revision
    :>json object committer: information about the committer of the revision
    :>json string committer_url: link to :http:get:`/api/1/person/(person_id)/` to get
        information about the committer of the revision
    :>json string committer_date: ISO representation of the commit date (in UTC)
    :>json string date: ISO representation of the revision date (in UTC)
    :>json string directory: the unique identifier that revision points to
    :>json string directory_url: link to :http:get:`/api/1/directory/(sha1_git)/[(path)/]`
        to get information about the directory associated to the revision
    :>json string id: the revision unique identifier
    :>json boolean merge: whether or not the revision corresponds to a merge commit
    :>json string message: the message associated to the revision
    :>json array parents: the parents of the revision, i.e. the previous revisions
        that head directly to it, each entry of that array contains an unique parent
        revision identifier but also a link to :http:get:`/api/1/revision/(sha1_git)/`
        to get more information about it
    :>json string type: the type of the revision

    **Allowed HTTP Methods:** :http:method:`get`, :http:method:`head`, :http:method:`options`

    :statuscode 200: no error
    :statuscode 400: an invalid **sha1_git** value has been provided
    :statuscode 404: requested revision can not be found in the archive

    **Request:**

    .. parsed-literal::

        $ curl -i :swh_web_api:`revision/aafb16d69fd30ff58afdd69036a26047f3aebdc6/`
"""


class APIDocTestCase(SWHWebTestCase, APITestCase):

    def test_apidoc_nodoc_failure(self):
        with self.assertRaises(Exception):
            @api_doc('/my/nodoc/url/')
            def apidoc_nodoc_tester(request, arga=0, argb=0):
                return Response(arga + argb)

    @staticmethod
    @api_route(r'/some/(?P<myarg>[0-9]+)/(?P<myotherarg>[0-9]+)/',
               'some-doc-route')
    @api_doc('/some/doc/route/')
    def apidoc_route(request, myarg, myotherarg, akw=0):
        """
        Sample doc
        """
        return {'result': int(myarg) + int(myotherarg) + akw}

    def test_apidoc_route_doc(self):
        # when
        rv = self.client.get('/api/1/some/doc/route/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assertTemplateUsed('api/apidoc.html')

    def test_apidoc_route_fn(self):

        # when
        rv = self.client.get('/api/1/some/1/1/')

        # then
        self.assertEqual(rv.status_code, 200)

    @staticmethod
    @api_route(r'/some/full/(?P<myarg>[0-9]+)/(?P<myotherarg>[0-9]+)/',
               'some-complete-doc-route')
    @api_doc('/some/complete/doc/route/')
    def apidoc_full_stack(request, myarg, myotherarg, akw=0):
        """
        Sample doc
        """
        return {'result': int(myarg) + int(myotherarg) + akw}

    def test_apidoc_full_stack_doc(self):
        # when
        rv = self.client.get('/api/1/some/complete/doc/route/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assertTemplateUsed('api/apidoc.html')

    def test_apidoc_full_stack_fn(self):
        # when
        rv = self.client.get('/api/1/some/full/1/1/')

        # then
        self.assertEqual(rv.status_code, 200)

    def test_api_doc_parse_httpdomain(self):
        doc_data = {
            'description': '',
            'urls': [],
            'args': [],
            'params': [],
            'resheaders': [],
            'reqheaders': [],
            'return_type': '',
            'returns': [],
            'status_codes': [],
            'examples': []
        }

        _parse_httpdomain_doc(httpdomain_doc, doc_data)

        expected_urls = [{
            'rule': '/api/1/revision/ **\\(sha1_git\\)** /',
            'methods': ['GET', 'HEAD', 'OPTIONS']
        }]

        self.assertIn('urls', doc_data)
        self.assertEqual(doc_data['urls'], expected_urls)

        expected_description = 'Get information about a revision in the archive. \
Revisions are identified by **sha1** checksums, compatible with Git commit \
identifiers. See **swh.model.identifiers.revision_identifier** in our data \
model module for details about how they are computed.'
        self.assertIn('description', doc_data)
        self.assertEqual(doc_data['description'], expected_description)

        expected_args = [{
            'name': 'sha1_git',
            'type': 'string',
            'doc': 'hexadecimal representation of the revision **sha1_git** identifier'
        }]

        self.assertIn('args', doc_data)
        self.assertEqual(doc_data['args'], expected_args)

        expected_params = []
        self.assertIn('params', doc_data)
        self.assertEqual(doc_data['params'], expected_params)

        expected_reqheaders = [{
            'doc': 'the requested response content type, either ``application/json``  or ``application/yaml``',
            'name': 'Accept'
        }]

        self.assertIn('reqheaders', doc_data)
        self.assertEqual(doc_data['reqheaders'], expected_reqheaders)

        expected_resheaders = [{
            'doc': 'this depends on **Accept** header of request',
            'name': 'Content-Type'
        }]

        self.assertIn('resheaders', doc_data)
        self.assertEqual(doc_data['resheaders'], expected_resheaders)

        expected_statuscodes = [
            {
                'code': '200',
                'doc': 'no error'
            },
            {
                'code': '400',
                'doc': 'an invalid **sha1_git** value has been provided'
            },
            {
                'code': '404',
                'doc': 'requested revision can not be found in the archive'
            }
        ]

        self.assertIn('status_codes', doc_data)
        self.assertEqual(doc_data['status_codes'], expected_statuscodes)

        expected_return_type = 'object'

        self.assertIn('return_type', doc_data)
        self.assertEqual(doc_data['return_type'], expected_return_type)

        expected_returns = [
            {
                'name': 'author',
                'type': 'object',
                'doc': 'information about the author of the revision'
            },
            {
                'name': 'author_url',
                'type': 'string',
                'doc': 'link to `</api/1/person/>`_ to get information about the author of the revision'
            },
            {
                'name': 'committer',
                'type': 'object',
                'doc': 'information about the committer of the revision'
            },
            {
                'name': 'committer_url',
                'type': 'string',
                'doc': 'link to `</api/1/person/>`_ to get information about the committer of the revision'
            },
            {
                'name': 'committer_date',
                'type': 'string',
                'doc': 'ISO representation of the commit date (in UTC)'
            },
            {
                'name': 'date',
                'type': 'string',
                'doc': 'ISO representation of the revision date (in UTC)'
            },
            {
                'name': 'directory',
                'type': 'string',
                'doc': 'the unique identifier that revision points to'
            },
            {
                'name': 'directory_url',
                'type': 'string',
                'doc': 'link to `</api/1/directory/>`_ to get information about the directory associated to the revision'
            },
            {
                'name': 'id',
                'type': 'string',
                'doc': 'the revision unique identifier'
            },
            {
                'name': 'merge',
                'type': 'boolean',
                'doc': 'whether or not the revision corresponds to a merge commit'
            },
            {
                'name': 'message',
                'type': 'string',
                'doc': 'the message associated to the revision'
            },
            {
                'name': 'parents',
                'type': 'array',
                'doc': 'the parents of the revision, i.e. the previous revisions that head directly to it, each entry of that array contains an unique parent revision identifier but also a link to `</api/1/revision/>`_ to get more information about it'
            },
            {
                'name': 'type',
                'type': 'string',
                'doc': 'the type of the revision'
            }
        ]

        self.assertIn('returns', doc_data)
        self.assertEqual(doc_data['returns'], expected_returns)

        expected_examples = ['/api/1/revision/aafb16d69fd30ff58afdd69036a26047f3aebdc6/']

        self.assertIn('examples', doc_data)
        self.assertEqual(doc_data['examples'], expected_examples)
