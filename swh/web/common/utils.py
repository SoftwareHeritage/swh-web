# Copyright (C) 2017-2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from datetime import datetime, timezone
import os
import re
from typing import Any, Dict, Optional

from bs4 import BeautifulSoup
from docutils.core import publish_parts
import docutils.parsers.rst
import docutils.utils
from docutils.writers.html5_polyglot import HTMLTranslator, Writer
from iso8601 import ParseError, parse_date
from prometheus_client.registry import CollectorRegistry

from django.http import HttpRequest, QueryDict
from django.urls import reverse as django_reverse
from rest_framework.authentication import SessionAuthentication

from swh.web.common.exc import BadInputExc
from swh.web.common.typing import QueryParameters
from swh.web.config import get_config

SWH_WEB_METRICS_REGISTRY = CollectorRegistry(auto_describe=True)

swh_object_icons = {
    "alias": "mdi mdi-star",
    "branch": "mdi mdi-source-branch",
    "branches": "mdi mdi-source-branch",
    "content": "mdi mdi-file-document",
    "directory": "mdi mdi-folder",
    "origin": "mdi mdi-source-repository",
    "person": "mdi mdi-account",
    "revisions history": "mdi mdi-history",
    "release": "mdi mdi-tag",
    "releases": "mdi mdi-tag",
    "revision": "mdi mdi-rotate-90 mdi-source-commit",
    "snapshot": "mdi mdi-camera",
    "visits": "mdi mdi-calendar-month",
}


def reverse(
    viewname: str,
    url_args: Optional[Dict[str, Any]] = None,
    query_params: Optional[QueryParameters] = None,
    current_app: Optional[str] = None,
    urlconf: Optional[str] = None,
    request: Optional[HttpRequest] = None,
) -> str:
    """An override of django reverse function supporting query parameters.

    Args:
        viewname: the name of the django view from which to compute a url
        url_args: dictionary of url arguments indexed by their names
        query_params: dictionary of query parameters to append to the
            reversed url
        current_app: the name of the django app tighten to the view
        urlconf: url configuration module
        request: build an absolute URI if provided

    Returns:
        str: the url of the requested view with processed arguments and
        query parameters
    """

    if url_args:
        url_args = {k: v for k, v in url_args.items() if v is not None}

    url = django_reverse(
        viewname, urlconf=urlconf, kwargs=url_args, current_app=current_app
    )

    if query_params:
        query_params = {k: v for k, v in query_params.items() if v is not None}

    if query_params and len(query_params) > 0:
        query_dict = QueryDict("", mutable=True)
        for k in sorted(query_params.keys()):
            query_dict[k] = query_params[k]
        url += "?" + query_dict.urlencode(safe="/;:")

    if request is not None:
        url = request.build_absolute_uri(url)

    return url


def datetime_to_utc(date):
    """Returns datetime in UTC without timezone info

    Args:
        date (datetime.datetime): input datetime with timezone info

    Returns:
        datetime.datetime: datetime in UTC without timezone info
    """
    if date.tzinfo and date.tzinfo != timezone.utc:
        return date.astimezone(tz=timezone.utc)
    else:
        return date


def parse_iso8601_date_to_utc(iso_date: str) -> datetime:
    """Given an ISO 8601 datetime string, parse the result as UTC datetime.

    Returns:
        a timezone-aware datetime representing the parsed date

    Raises:
        swh.web.common.exc.BadInputExc: provided date does not respect ISO 8601 format

    Samples:
        - 2016-01-12
        - 2016-01-12T09:19:12+0100
        - 2007-01-14T20:34:22Z

    """
    try:
        date = parse_date(iso_date)
        return datetime_to_utc(date)
    except ParseError as e:
        raise BadInputExc(e)


def shorten_path(path):
    """Shorten the given path: for each hash present, only return the first
    8 characters followed by an ellipsis"""

    sha256_re = r"([0-9a-f]{8})[0-9a-z]{56}"
    sha1_re = r"([0-9a-f]{8})[0-9a-f]{32}"

    ret = re.sub(sha256_re, r"\1...", path)
    return re.sub(sha1_re, r"\1...", ret)


def format_utc_iso_date(iso_date, fmt="%d %B %Y, %H:%M UTC"):
    """Turns a string representation of an ISO 8601 datetime string
    to UTC and format it into a more human readable one.

    For instance, from the following input
    string: '2017-05-04T13:27:13+02:00' the following one
    is returned: '04 May 2017, 11:27 UTC'.
    Custom format string may also be provided
    as parameter

    Args:
        iso_date (str): a string representation of an ISO 8601 date
        fmt (str): optional date formatting string

    Returns:
        str: a formatted string representation of the input iso date
    """
    if not iso_date:
        return iso_date
    date = parse_iso8601_date_to_utc(iso_date)
    return date.strftime(fmt)


def gen_path_info(path):
    """Function to generate path data navigation for use
    with a breadcrumb in the swh web ui.

    For instance, from a path /folder1/folder2/folder3,
    it returns the following list::

        [{'name': 'folder1', 'path': 'folder1'},
         {'name': 'folder2', 'path': 'folder1/folder2'},
         {'name': 'folder3', 'path': 'folder1/folder2/folder3'}]

    Args:
        path: a filesystem path

    Returns:
        list: a list of path data for navigation as illustrated above.

    """
    path_info = []
    if path:
        sub_paths = path.strip("/").split("/")
        path_from_root = ""
        for p in sub_paths:
            path_from_root += "/" + p
            path_info.append({"name": p, "path": path_from_root.strip("/")})
    return path_info


def parse_rst(text, report_level=2):
    """
    Parse a reStructuredText string with docutils.

    Args:
        text (str): string with reStructuredText markups in it
        report_level (int): level of docutils report messages to print
            (1 info 2 warning 3 error 4 severe 5 none)

    Returns:
        docutils.nodes.document: a parsed docutils document
    """
    parser = docutils.parsers.rst.Parser()
    components = (docutils.parsers.rst.Parser,)
    settings = docutils.frontend.OptionParser(
        components=components
    ).get_default_values()
    settings.report_level = report_level
    document = docutils.utils.new_document("rst-doc", settings=settings)
    parser.parse(text, document)
    return document


def get_client_ip(request):
    """
    Return the client IP address from an incoming HTTP request.

    Args:
        request (django.http.HttpRequest): the incoming HTTP request

    Returns:
        str: The client IP address
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


browsers_supported_image_mimes = set(
    [
        "image/gif",
        "image/png",
        "image/jpeg",
        "image/bmp",
        "image/webp",
        "image/svg",
        "image/svg+xml",
    ]
)


def context_processor(request):
    """
    Django context processor used to inject variables
    in all swh-web templates.
    """
    config = get_config()
    if (
        hasattr(request, "user")
        and request.user.is_authenticated
        and not hasattr(request.user, "backend")
    ):
        # To avoid django.template.base.VariableDoesNotExist errors
        # when rendering templates when standard Django user is logged in.
        request.user.backend = "django.contrib.auth.backends.ModelBackend"
    return {
        "swh_object_icons": swh_object_icons,
        "available_languages": None,
        "swh_client_config": config["client_config"],
        "oidc_enabled": bool(config["keycloak"]["server_url"]),
        "browsers_supported_image_mimes": browsers_supported_image_mimes,
        "keycloak": config["keycloak"],
        "site_base_url": request.build_absolute_uri("/"),
        "DJANGO_SETTINGS_MODULE": os.environ["DJANGO_SETTINGS_MODULE"],
        "status": config["status"],
    }


class EnforceCSRFAuthentication(SessionAuthentication):
    """
    Helper class to enforce CSRF validation on a DRF view
    when a user is not authenticated.
    """

    def authenticate(self, request):
        user = getattr(request._request, "user", None)
        self.enforce_csrf(request)
        return (user, None)


def resolve_branch_alias(
    snapshot: Dict[str, Any], branch: Optional[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """
    Resolve branch alias in snapshot content.

    Args:
        snapshot: a full snapshot content
        branch: a branch alias contained in the snapshot
    Returns:
        The real snapshot branch that got aliased.
    """
    while branch and branch["target_type"] == "alias":
        if branch["target"] in snapshot["branches"]:
            branch = snapshot["branches"][branch["target"]]
        else:
            from swh.web.common import archive

            snp = archive.lookup_snapshot(
                snapshot["id"], branches_from=branch["target"], branches_count=1
            )
            if snp and branch["target"] in snp["branches"]:
                branch = snp["branches"][branch["target"]]
            else:
                branch = None
    return branch


class _NoHeaderHTMLTranslator(HTMLTranslator):
    """
    Docutils translator subclass to customize the generation of HTML
    from reST-formatted docstrings
    """

    def __init__(self, document):
        super().__init__(document)
        self.body_prefix = []
        self.body_suffix = []


_HTML_WRITER = Writer()
_HTML_WRITER.translator_class = _NoHeaderHTMLTranslator


def rst_to_html(rst: str) -> str:
    """
    Convert reStructuredText document into HTML.

    Args:
        rst: A string containing a reStructuredText document

    Returns:
        Body content of the produced HTML conversion.

    """
    settings = {
        "initial_header_level": 2,
    }
    pp = publish_parts(rst, writer=_HTML_WRITER, settings_overrides=settings)
    return f'<div class="swh-rst">{pp["html_body"]}</div>'


def prettify_html(html: str) -> str:
    """
    Prettify an HTML document.

    Args:
        html: Input HTML document

    Returns:
        The prettified HTML document
    """
    return BeautifulSoup(html, "lxml").prettify()
