# Copyright (C) 2015-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import textwrap

import pytest

from rest_framework.response import Response

from swh.storage.exc import StorageAPIError, StorageDBError
from swh.web.api.apidoc import _parse_httpdomain_doc, api_doc
from swh.web.api.apiurls import api_route
from swh.web.common.exc import BadInputExc, ForbiddenExc, NotFoundExc
from swh.web.common.utils import prettify_html, reverse
from swh.web.tests.utils import check_api_get_responses, check_html_get_response

_httpdomain_doc = """
.. http:get:: /api/1/revision/(sha1_git)/

    Get information about a revision in the archive.
    Revisions are identified by **sha1** checksums, compatible with Git commit
    identifiers.
    See :func:`swh.model.identifiers.revision_identifier` in our data model
    module for details about how they are computed.

    :param string sha1_git: hexadecimal representation of the revision
        **sha1_git** identifier

    :reqheader Accept: the requested response content type,
        either ``application/json`` (default) or ``application/yaml``
    :resheader Content-Type: this depends on :http:header:`Accept` header
        of request

    :<json int n: sample input integer
    :<json string s: sample input string
    :<json array a: sample input array

    :>json object author: information about the author of the revision
    :>json object committer: information about the committer of the revision
    :>json string committer_date: ISO representation of the commit date
        (in UTC)
    :>json string date: ISO representation of the revision date (in UTC)
    :>json string directory: the unique identifier that revision points to
    :>json string directory_url: link to
        :http:get:`/api/1/directory/(sha1_git)/[(path)/]` to get information
        about the directory associated to the revision
    :>json string id: the revision unique identifier
    :>json boolean merge: whether or not the revision corresponds to a merge
        commit
    :>json string message: the message associated to the revision
    :>json array parents: the parents of the revision, i.e. the previous
        revisions that head directly to it, each entry of that array contains
        an unique parent revision identifier but also a link to
        :http:get:`/api/1/revision/(sha1_git)/` to get more information
        about it
    :>json string type: the type of the revision

    :statuscode 200: no error
    :statuscode 400: an invalid **sha1_git** value has been provided
    :statuscode 404: requested revision can not be found in the archive

    **Request:**

    .. parsed-literal::

        :swh_web_api:`revision/aafb16d69fd30ff58afdd69036a26047f3aebdc6/`
"""


_exception_http_code = {
    BadInputExc: 400,
    ForbiddenExc: 403,
    NotFoundExc: 404,
    Exception: 500,
    StorageAPIError: 503,
    StorageDBError: 503,
}


def test_apidoc_nodoc_failure():
    with pytest.raises(Exception):

        @api_doc("/my/nodoc/url/")
        def apidoc_nodoc_tester(request, arga=0, argb=0):
            return Response(arga + argb)


@api_route(r"/some/(?P<myarg>[0-9]+)/(?P<myotherarg>[0-9]+)/", "api-1-some-doc-route")
@api_doc("/some/doc/route/")
def apidoc_route(request, myarg, myotherarg, akw=0):
    """
    Sample doc
    """
    return {"result": int(myarg) + int(myotherarg) + akw}


def test_apidoc_route_doc(client):
    url = reverse("api-1-some-doc-route-doc")
    check_html_get_response(
        client, url, status_code=200, template_used="api/apidoc.html"
    )


def test_apidoc_route_fn(api_client):
    url = reverse("api-1-some-doc-route", url_args={"myarg": 1, "myotherarg": 1})
    check_api_get_responses(api_client, url, status_code=200)


@api_route(r"/test/error/(?P<exc_name>.+)/", "api-1-test-error")
@api_doc("/test/error/")
def apidoc_test_error_route(request, exc_name):
    """
    Sample doc
    """
    for e in _exception_http_code.keys():
        if e.__name__ == exc_name:
            raise e("Error")


def test_apidoc_error(api_client):
    for exc, code in _exception_http_code.items():
        url = reverse("api-1-test-error", url_args={"exc_name": exc.__name__})
        check_api_get_responses(api_client, url, status_code=code)


@api_route(
    r"/some/full/(?P<myarg>[0-9]+)/(?P<myotherarg>[0-9]+)/",
    "api-1-some-complete-doc-route",
)
@api_doc("/some/complete/doc/route/")
def apidoc_full_stack(request, myarg, myotherarg, akw=0):
    """
    Sample doc
    """
    return {"result": int(myarg) + int(myotherarg) + akw}


def test_apidoc_full_stack_doc(client):
    url = reverse("api-1-some-complete-doc-route-doc")
    check_html_get_response(
        client, url, status_code=200, template_used="api/apidoc.html"
    )


def test_apidoc_full_stack_fn(api_client):
    url = reverse(
        "api-1-some-complete-doc-route", url_args={"myarg": 1, "myotherarg": 1}
    )
    check_api_get_responses(api_client, url, status_code=200)


@api_route(r"/test/post/only/", "api-1-test-post-only", methods=["POST"])
@api_doc("/test/post/only/")
def apidoc_test_post_only(request, exc_name):
    """
    Sample doc
    """
    return {"result": "some data"}


def test_apidoc_post_only(client):
    # a dedicated view accepting GET requests should have
    # been created to display the HTML documentation
    url = reverse("api-1-test-post-only-doc")
    check_html_get_response(
        client, url, status_code=200, template_used="api/apidoc.html"
    )


def test_api_doc_parse_httpdomain():
    doc_data = {
        "description": "",
        "urls": [],
        "args": [],
        "params": [],
        "resheaders": [],
        "reqheaders": [],
        "input_type": "",
        "inputs": [],
        "return_type": "",
        "returns": [],
        "status_codes": [],
        "examples": [],
    }

    _parse_httpdomain_doc(_httpdomain_doc, doc_data)

    expected_urls = [
        {
            "rule": "/api/1/revision/ **\\(sha1_git\\)** /",
            "methods": ["GET", "HEAD", "OPTIONS"],
        }
    ]

    assert "urls" in doc_data
    assert doc_data["urls"] == expected_urls

    expected_description = (
        "Get information about a revision in the archive. "
        "Revisions are identified by **sha1** checksums, "
        "compatible with Git commit identifiers. See "
        "**swh.model.identifiers.revision_identifier** in "
        "our data model module for details about how they "
        "are computed."
    )

    assert "description" in doc_data
    assert doc_data["description"] == expected_description

    expected_args = [
        {
            "name": "sha1_git",
            "type": "string",
            "doc": (
                "hexadecimal representation of the revision " "**sha1_git** identifier"
            ),
        }
    ]

    assert "args" in doc_data
    assert doc_data["args"] == expected_args

    expected_params = []
    assert "params" in doc_data
    assert doc_data["params"] == expected_params

    expected_reqheaders = [
        {
            "doc": (
                "the requested response content type, either "
                "``application/json`` (default) or ``application/yaml``"
            ),
            "name": "Accept",
        }
    ]

    assert "reqheaders" in doc_data
    assert doc_data["reqheaders"] == expected_reqheaders

    expected_resheaders = [
        {"doc": "this depends on **Accept** header of request", "name": "Content-Type"}
    ]

    assert "resheaders" in doc_data
    assert doc_data["resheaders"] == expected_resheaders

    expected_statuscodes = [
        {"code": "200", "doc": "no error"},
        {"code": "400", "doc": "an invalid **sha1_git** value has been provided"},
        {"code": "404", "doc": "requested revision can not be found in the archive"},
    ]

    assert "status_codes" in doc_data
    assert doc_data["status_codes"] == expected_statuscodes

    expected_input_type = "object"

    assert "input_type" in doc_data
    assert doc_data["input_type"] == expected_input_type

    expected_inputs = [
        {"name": "n", "type": "int", "doc": "sample input integer"},
        {"name": "s", "type": "string", "doc": "sample input string"},
        {"name": "a", "type": "array", "doc": "sample input array"},
    ]

    assert "inputs" in doc_data
    assert doc_data["inputs"] == expected_inputs

    expected_return_type = "object"

    assert "return_type" in doc_data
    assert doc_data["return_type"] == expected_return_type

    expected_returns = [
        {
            "name": "author",
            "type": "object",
            "doc": "information about the author of the revision",
        },
        {
            "name": "committer",
            "type": "object",
            "doc": "information about the committer of the revision",
        },
        {
            "name": "committer_date",
            "type": "string",
            "doc": "ISO representation of the commit date (in UTC)",
        },
        {
            "name": "date",
            "type": "string",
            "doc": "ISO representation of the revision date (in UTC)",
        },
        {
            "name": "directory",
            "type": "string",
            "doc": "the unique identifier that revision points to",
        },
        {
            "name": "directory_url",
            "type": "string",
            "doc": (
                "link to `/api/1/directory/ </api/1/directory/doc/>`_ "
                "to get information about the directory associated to "
                "the revision"
            ),
        },
        {"name": "id", "type": "string", "doc": "the revision unique identifier"},
        {
            "name": "merge",
            "type": "boolean",
            "doc": "whether or not the revision corresponds to a merge commit",
        },
        {
            "name": "message",
            "type": "string",
            "doc": "the message associated to the revision",
        },
        {
            "name": "parents",
            "type": "array",
            "doc": (
                "the parents of the revision, i.e. the previous revisions "
                "that head directly to it, each entry of that array "
                "contains an unique parent revision identifier but also a "
                "link to `/api/1/revision/ </api/1/revision/doc/>`_ "
                "to get more information about it"
            ),
        },
        {"name": "type", "type": "string", "doc": "the type of the revision"},
    ]

    assert "returns" in doc_data
    assert doc_data["returns"] == expected_returns

    expected_examples = ["/api/1/revision/aafb16d69fd30ff58afdd69036a26047f3aebdc6/"]

    assert "examples" in doc_data
    assert doc_data["examples"] == expected_examples


@api_route(r"/post/endpoint/", "api-1-post-endpoint", methods=["POST"])
@api_doc("/post/endpoint/")
def apidoc_test_post_endpoint(request):
    """
    .. http:post:: /api/1/post/endpoint/

        Endpoint documentation

        :<jsonarr string -: Input array of SWHIDs

        :>json object <swhid>: an object whose keys are input SWHIDs
            and values objects with the following keys:

                * **known (bool)**: whether the object was found

    """
    pass


def test_apidoc_input_output_doc(client):
    url = reverse("api-1-post-endpoint-doc")
    rv = check_html_get_response(
        client, url, status_code=200, template_used="api/apidoc.html"
    )

    input_html_doc = textwrap.indent(
        (
            '<dl class="row">\n'
            ' <dt class="col col-md-2 text-right">\n'
            "  array\n"
            " </dt>\n"
            ' <dd class="col col-md-9">\n'
            "  <p>\n"
            "   Input array of SWHIDs\n"
            "  </p>\n"
            " </dd>\n"
            "</dl>\n"
        ),
        " " * 7,
    )

    output_html_doc = textwrap.indent(
        (
            '<dl class="row">\n'
            ' <dt class="col col-md-2 text-right">\n'
            "  object\n"
            " </dt>\n"
            ' <dd class="col col-md-9">\n'
            "  <p>\n"
            "   an object containing the following keys:\n"
            "  </p>\n"
            '  <div class="swh-rst">\n'
            "   <blockquote>\n"
            "    <ul>\n"
            "     <li>\n"
            "      <p>\n"
            "       <strong>\n"
            "        &lt;swhid&gt; (object)\n"
            "       </strong>\n"
            "       : an object whose keys are input SWHIDs"
            " and values objects with the following keys:\n"
            "      </p>\n"
            "      <blockquote>\n"
            '       <ul class="simple">\n'
            "        <li>\n"
            "         <p>\n"
            "          <strong>\n"
            "           known (bool)\n"
            "          </strong>\n"
            "          : whether the object was found\n"
            "         </p>\n"
            "        </li>\n"
            "       </ul>\n"
            "      </blockquote>\n"
            "     </li>\n"
            "    </ul>\n"
            "   </blockquote>\n"
            "  </div>\n"
            " </dd>\n"
            "</dl>\n"
        ),
        " " * 7,
    )

    html = prettify_html(rv.content)

    assert input_html_doc in html
    assert output_html_doc in html


@api_route(r"/endpoint/links/in/doc/", "api-1-endpoint-links-in-doc")
@api_doc("/endpoint/links/in/doc/")
def apidoc_test_endpoint_with_links_in_doc(request):
    """
    .. http:get:: /api/1/post/endpoint/

        Endpoint documentation with links to
        :http:get:`/api/1/content/[(hash_type):](hash)/`,
        :http:get:`/api/1/directory/(sha1_git)/[(path)/]`
        and `archive <https://archive.softwareheritage.org>`_.
    """
    pass


def test_apidoc_with_links(client):
    url = reverse("api-1-endpoint-links-in-doc")
    rv = check_html_get_response(
        client, url, status_code=200, template_used="api/apidoc.html"
    )

    html = prettify_html(rv.content)

    first_link = textwrap.indent(
        (
            '<a class="reference external" href="/api/1/content/doc/">\n'
            " /api/1/content/\n"
            "</a>"
        ),
        " " * 9,
    )

    second_link = textwrap.indent(
        (
            '<a class="reference external" href="/api/1/directory/doc/">\n'
            " /api/1/directory/\n"
            "</a>"
        ),
        " " * 9,
    )

    third_link = textwrap.indent(
        (
            '<a class="reference external" '
            'href="https://archive.softwareheritage.org">\n'
            " archive\n"
            "</a>"
        ),
        " " * 9,
    )

    assert first_link in html
    assert second_link in html
    assert third_link in html
