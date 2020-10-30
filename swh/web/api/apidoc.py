# Copyright (C) 2015-2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from collections import defaultdict
import functools
from functools import wraps
import os
import re
import textwrap
from typing import List

import docutils.nodes
import docutils.parsers.rst
import docutils.utils

from rest_framework.decorators import api_view

from swh.web.api.apiresponse import make_api_response
from swh.web.api.apiurls import APIUrls
from swh.web.common.utils import parse_rst


class _HTTPDomainDocVisitor(docutils.nodes.NodeVisitor):
    """
    docutils visitor for walking on a parsed rst document containing sphinx
    httpdomain roles. Its purpose is to extract relevant info regarding swh
    api endpoints (for instance url arguments) from their docstring written
    using sphinx httpdomain.
    """

    # httpdomain roles we want to parse (based on sphinxcontrib.httpdomain 1.6)
    parameter_roles = ("param", "parameter", "arg", "argument")

    request_json_object_roles = ("reqjsonobj", "reqjson", "<jsonobj", "<json")

    request_json_array_roles = ("reqjsonarr", "<jsonarr")

    response_json_object_roles = ("resjsonobj", "resjson", ">jsonobj", ">json")

    response_json_array_roles = ("resjsonarr", ">jsonarr")

    query_parameter_roles = ("queryparameter", "queryparam", "qparam", "query")

    request_header_roles = ("<header", "reqheader", "requestheader")

    response_header_roles = (">header", "resheader", "responseheader")

    status_code_roles = ("statuscode", "status", "code")

    def __init__(self, document, data):
        super().__init__(document)
        self.data = data
        self.args_set = set()
        self.params_set = set()
        self.inputs_set = set()
        self.returns_set = set()
        self.status_codes_set = set()
        self.reqheaders_set = set()
        self.resheaders_set = set()
        self.field_list_visited = False
        self.current_json_obj = None

    def process_paragraph(self, par):
        """
        Process extracted paragraph text before display.
        Cleanup document model markups and transform the
        paragraph into a valid raw rst string (as the apidoc
        documentation transform rst to html when rendering).
        """
        par = par.replace("\n", " ")
        # keep emphasized, strong and literal text
        par = par.replace("<emphasis>", "*")
        par = par.replace("</emphasis>", "*")
        par = par.replace("<strong>", "**")
        par = par.replace("</strong>", "**")
        par = par.replace("<literal>", "``")
        par = par.replace("</literal>", "``")
        # keep links to web pages
        if "<reference" in par:
            par = re.sub(
                r'<reference name="(.*)" refuri="(.*)".*</reference>',
                r"`\1 <\2>`_",
                par,
            )
        # remove parsed document markups but keep rst links
        par = re.sub(r"<[^<]+?>(?!`_)", "", par)
        # api urls cleanup to generate valid links afterwards
        subs_made = 1
        while subs_made:
            (par, subs_made) = re.subn(r"(:http:.*)(\(\w+\))", r"\1", par)
        subs_made = 1
        while subs_made:
            (par, subs_made) = re.subn(r"(:http:.*)(\[.*\])", r"\1", par)
        par = re.sub(r"([^:])//", r"\1/", par)
        # transform references to api endpoints doc into valid rst links
        par = re.sub(":http:get:`([^,`]*)`", r"`\1 <\1doc/>`_", par)
        # transform references to some elements into bold text
        par = re.sub(":http:header:`(.*)`", r"**\1**", par)
        par = re.sub(":func:`(.*)`", r"**\1**", par)
        return par

    def visit_field_list(self, node):
        """
        Visit parsed rst field lists to extract relevant info
        regarding api endpoint.
        """
        self.field_list_visited = True
        for child in node.traverse():
            # get the parsed field name
            if isinstance(child, docutils.nodes.field_name):
                field_name = child.astext()
            # parse field text
            elif isinstance(child, docutils.nodes.paragraph):
                text = self.process_paragraph(str(child))
                field_data = field_name.split(" ")
                # Parameters
                if field_data[0] in self.parameter_roles:
                    if field_data[2] not in self.args_set:
                        self.data["args"].append(
                            {"name": field_data[2], "type": field_data[1], "doc": text}
                        )
                        self.args_set.add(field_data[2])
                # Query Parameters
                if field_data[0] in self.query_parameter_roles:
                    if field_data[2] not in self.params_set:
                        self.data["params"].append(
                            {"name": field_data[2], "type": field_data[1], "doc": text}
                        )
                        self.params_set.add(field_data[2])
                # Request data type
                if (
                    field_data[0] in self.request_json_array_roles
                    or field_data[0] in self.request_json_object_roles
                ):
                    # array
                    if field_data[0] in self.request_json_array_roles:
                        self.data["input_type"] = "array"
                    # object
                    else:
                        self.data["input_type"] = "object"
                    # input object field
                    if field_data[2] not in self.inputs_set:
                        self.data["inputs"].append(
                            {"name": field_data[2], "type": field_data[1], "doc": text}
                        )
                        self.inputs_set.add(field_data[2])
                        self.current_json_obj = self.data["inputs"][-1]
                # Response type
                if (
                    field_data[0] in self.response_json_array_roles
                    or field_data[0] in self.response_json_object_roles
                ):
                    # array
                    if field_data[0] in self.response_json_array_roles:
                        self.data["return_type"] = "array"
                    # object
                    else:
                        self.data["return_type"] = "object"
                    # returned object field
                    if field_data[2] not in self.returns_set:
                        self.data["returns"].append(
                            {"name": field_data[2], "type": field_data[1], "doc": text}
                        )
                        self.returns_set.add(field_data[2])
                        self.current_json_obj = self.data["returns"][-1]
                # Status Codes
                if field_data[0] in self.status_code_roles:
                    if field_data[1] not in self.status_codes_set:
                        self.data["status_codes"].append(
                            {"code": field_data[1], "doc": text}
                        )
                        self.status_codes_set.add(field_data[1])
                # Request Headers
                if field_data[0] in self.request_header_roles:
                    if field_data[1] not in self.reqheaders_set:
                        self.data["reqheaders"].append(
                            {"name": field_data[1], "doc": text}
                        )
                        self.reqheaders_set.add(field_data[1])
                # Response Headers
                if field_data[0] in self.response_header_roles:
                    if field_data[1] not in self.resheaders_set:
                        resheader = {"name": field_data[1], "doc": text}
                        self.data["resheaders"].append(resheader)
                        self.resheaders_set.add(field_data[1])
                        if (
                            resheader["name"] == "Content-Type"
                            and resheader["doc"] == "application/octet-stream"
                        ):
                            self.data["return_type"] = "octet stream"

    def visit_paragraph(self, node):
        """
        Visit relevant paragraphs to parse
        """
        # only parsed top level paragraphs
        if isinstance(node.parent, docutils.nodes.block_quote):
            text = self.process_paragraph(str(node))
            # endpoint description
            if not text.startswith("**") and text not in self.data["description"]:
                self.data["description"] += "\n\n" if self.data["description"] else ""
                self.data["description"] += text

    def visit_literal_block(self, node):
        """
        Visit literal blocks
        """
        text = node.astext()
        # literal block in endpoint description
        if not self.field_list_visited:
            self.data["description"] += ":\n\n%s\n" % textwrap.indent(text, "\t")
        # extract example urls
        if ":swh_web_api:" in text:
            examples_str = re.sub(".*`(.+)`.*", r"/api/1/\1", text)
            self.data["examples"] += examples_str.split("\n")

    def visit_bullet_list(self, node):
        # bullet list in endpoint description
        if not self.field_list_visited:
            self.data["description"] += "\n\n"
            for child in node.traverse():
                # process list item
                if isinstance(child, docutils.nodes.paragraph):
                    line_text = self.process_paragraph(str(child))
                    self.data["description"] += "\t* %s\n" % line_text
        elif self.current_json_obj:
            self.current_json_obj["doc"] += "\n\n"
            for child in node.traverse():
                # process list item
                if isinstance(child, docutils.nodes.paragraph):
                    line_text = self.process_paragraph(str(child))
                    self.current_json_obj["doc"] += "\t\t* %s\n" % line_text
            self.current_json_obj = None

    def visit_warning(self, node):
        text = self.process_paragraph(str(node))
        rst_warning = "\n\n.. warning::\n%s\n" % textwrap.indent(text, "\t")
        if rst_warning not in self.data["description"]:
            self.data["description"] += rst_warning

    def unknown_visit(self, node):
        pass

    def unknown_departure(self, node):
        pass


def _parse_httpdomain_doc(doc, data):
    doc_lines = doc.split("\n")
    doc_lines_filtered = []
    urls = defaultdict(list)
    default_http_methods = ["HEAD", "OPTIONS"]
    # httpdomain is a sphinx extension that is unknown to docutils but
    # fortunately we can still parse its directives' content,
    # so remove lines with httpdomain directives before executing the
    # rst parser from docutils
    for doc_line in doc_lines:
        if ".. http" not in doc_line:
            doc_lines_filtered.append(doc_line)
        else:
            url = doc_line[doc_line.find("/") :]
            # emphasize url arguments for html rendering
            url = re.sub(r"\((\w+)\)", r" **\(\1\)** ", url)
            method = re.search(r"http:(\w+)::", doc_line).group(1)
            urls[url].append(method.upper())

    for url, methods in urls.items():
        data["urls"].append({"rule": url, "methods": methods + default_http_methods})
    # parse the rst docstring and do not print system messages about
    # unknown httpdomain roles
    document = parse_rst("\n".join(doc_lines_filtered), report_level=5)
    # remove the system_message nodes from the parsed document
    for node in document.traverse(docutils.nodes.system_message):
        node.parent.remove(node)
    # visit the document nodes to extract relevant endpoint info
    visitor = _HTTPDomainDocVisitor(document, data)
    document.walkabout(visitor)


class APIDocException(Exception):
    """
    Custom exception to signal errors in the use of the APIDoc decorators
    """


def api_doc(
    route: str, noargs: bool = False, tags: List[str] = [], api_version: str = "1",
):
    """
    Decorator for an API endpoint implementation used to generate a dedicated
    view displaying its HTML documentation.

    The documentation will be generated from the endpoint docstring based on
    sphinxcontrib-httpdomain format.

    Args:
        route: documentation page's route
        noargs: set to True if the route has no arguments, and its
            result should be displayed anytime its documentation
            is requested. Default to False
        tags: Further information on api endpoints. Two values are
            possibly expected:

                * hidden: remove the entry points from the listing
                * upcoming: display the entry point but it is not followable
        api_version: api version string
    """

    tags_set = set(tags)

    # @api_doc() Decorator call
    def decorator(f):
        # if the route is not hidden, add it to the index
        if "hidden" not in tags_set:
            doc_data = get_doc_data(f, route, noargs)
            doc_desc = doc_data["description"]
            first_dot_pos = doc_desc.find(".")
            APIUrls.add_doc_route(
                route,
                doc_desc[: first_dot_pos + 1],
                noargs=noargs,
                api_version=api_version,
                tags=tags_set,
            )

        # create a dedicated view to display endpoint HTML doc
        @api_view(["GET", "HEAD"])
        @wraps(f)
        def doc_view(request):
            doc_data = get_doc_data(f, route, noargs)
            return make_api_response(request, None, doc_data)

        route_name = "%s-doc" % route[1:-1].replace("/", "-")
        urlpattern = f"^{api_version}{route}doc/$"

        view_name = "api-%s-%s" % (api_version, route_name)
        APIUrls.add_url_pattern(urlpattern, doc_view, view_name)

        @wraps(f)
        def documented_view(request, **kwargs):
            doc_data = get_doc_data(f, route, noargs)
            try:
                return {"data": f(request, **kwargs), "doc_data": doc_data}
            except Exception as exc:
                exc.doc_data = doc_data
                raise exc

        return documented_view

    return decorator


@functools.lru_cache(maxsize=32)
def get_doc_data(f, route, noargs):
    """
    Build documentation data for the decorated api endpoint function
    """
    data = {
        "description": "",
        "response_data": None,
        "urls": [],
        "args": [],
        "params": [],
        "input_type": "",
        "inputs": [],
        "resheaders": [],
        "reqheaders": [],
        "return_type": "",
        "returns": [],
        "status_codes": [],
        "examples": [],
        "route": route,
        "noargs": noargs,
    }

    if not f.__doc__:
        raise APIDocException(
            "apidoc: expected a docstring" " for function %s" % (f.__name__,)
        )

    # use raw docstring as endpoint documentation if sphinx
    # httpdomain is not used
    if ".. http" not in f.__doc__:
        data["description"] = f.__doc__
    # else parse the sphinx httpdomain docstring with docutils
    # (except when building the swh-web documentation through autodoc
    # sphinx extension, not needed and raise errors with sphinx >= 1.7)
    elif "SWH_WEB_DOC_BUILD" not in os.environ:
        _parse_httpdomain_doc(f.__doc__, data)
        # process input/returned object info for nicer html display
        inputs_list = ""
        returns_list = ""
        for inp in data["inputs"]:
            # special case for array of non object type, for instance
            # :<jsonarr string -: an array of string
            if inp["name"] != "-":
                inputs_list += "\t* **%s (%s)**: %s\n" % (
                    inp["name"],
                    inp["type"],
                    inp["doc"],
                )
        for ret in data["returns"]:
            # special case for array of non object type, for instance
            # :>jsonarr string -: an array of string
            if ret["name"] != "-":
                returns_list += "\t* **%s (%s)**: %s\n" % (
                    ret["name"],
                    ret["type"],
                    ret["doc"],
                )
        data["inputs_list"] = inputs_list
        data["returns_list"] = returns_list

    return data


DOC_COMMON_HEADERS = """
        :reqheader Accept: the requested response content type,
            either ``application/json`` (default) or ``application/yaml``
        :resheader Content-Type: this depends on :http:header:`Accept`
            header of request"""
DOC_RESHEADER_LINK = """
        :resheader Link: indicates that a subsequent result page is
            available and contains the url pointing to it
"""

DEFAULT_SUBSTITUTIONS = {
    "common_headers": DOC_COMMON_HEADERS,
    "resheader_link": DOC_RESHEADER_LINK,
}


def format_docstring(**substitutions):
    def decorator(f):
        f.__doc__ = f.__doc__.format(**{**DEFAULT_SUBSTITUTIONS, **substitutions})
        return f

    return decorator
