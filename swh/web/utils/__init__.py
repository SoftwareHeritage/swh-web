# Copyright (C) 2017-2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from datetime import datetime, timezone
import functools
import gzip
import hashlib
from importlib.metadata import version
import os
import re
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple
import urllib.parse

from docutils.core import publish_parts
import docutils.parsers.rst
import docutils.utils
from docutils.utils import SystemMessage
from docutils.writers.html5_polyglot import HTMLTranslator, Writer
from iso8601 import ParseError, parse_date
import requests
from requests.auth import HTTPBasicAuth
import sentry_sdk

from django.conf import settings
from django.core.cache import cache
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.http import HttpRequest, QueryDict
from django.shortcuts import redirect
from django.urls import resolve
from django.urls import reverse as django_reverse

from swh.core.api.serializers import msgpack_dumps, msgpack_loads
from swh.web.auth.utils import (
    ADD_FORGE_MODERATOR_PERMISSION,
    ADMIN_LIST_DEPOSIT_PERMISSION,
    MAILMAP_ADMIN_PERMISSION,
    SWH_AMBASSADOR_PERMISSION,
)
from swh.web.config import get_config, oidc_enabled, search
from swh.web.utils.exc import BadInputExc, sentry_capture_exception

DATATABLES_MAX_PAGE_SIZE = get_config().get("datatables_max_page_size", 1000)


swh_object_icons = {
    "alias": "mdi mdi-star",
    "branch": "mdi mdi-source-branch",
    "branches": "mdi mdi-source-branch",
    "content": "mdi mdi-file-document",
    "cnt": "mdi mdi-file-document",
    "directory": "mdi mdi-folder",
    "dir": "mdi mdi-folder",
    "origin": "mdi mdi-source-repository",
    "ori": "mdi mdi-source-repository",
    "person": "mdi mdi-account",
    "revisions history": "mdi mdi-history",
    "release": "mdi mdi-tag",
    "rel": "mdi mdi-tag",
    "releases": "mdi mdi-tag",
    "revision": "mdi mdi-rotate-90 mdi-source-commit",
    "rev": "mdi mdi-rotate-90 mdi-source-commit",
    "snapshot": "mdi mdi-camera",
    "snp": "mdi mdi-camera",
    "visits": "mdi mdi-calendar-month",
}


def reverse(
    viewname: str,
    url_args: Optional[Dict[str, Any]] = None,
    query_params: Optional[Mapping[str, Optional[str]]] = None,
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

    params: Dict[str, str] = {}
    if query_params:
        params = {k: v for k, v in query_params.items() if v is not None}

    if params:
        query_dict = QueryDict("", mutable=True)
        query_dict.update(dict(sorted(params.items())))
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
        swh.web.utils.exc.BadInputExc: provided date does not respect ISO 8601 format

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


def format_utc_iso_date(iso_date, fmt="%d %B %Y, %H:%M:%S UTC"):
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
    settings = docutils.frontend.get_default_settings(docutils.parsers.rst.Parser)
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

    context = {
        "swh_object_icons": swh_object_icons,
        "available_languages": None,
        "swh_client_config": config["client_config"],
        "oidc_enabled": oidc_enabled(),
        "browsers_supported_image_mimes": browsers_supported_image_mimes,
        "keycloak": config["keycloak"],
        "site_base_url": request.build_absolute_uri("/")[:-1],
        "DJANGO_SETTINGS_MODULE": os.environ["DJANGO_SETTINGS_MODULE"],
        "status": config.get("status", {}),
        "swh_web_version": version("swh.web"),
        "iframe_mode": False,
        "ADMIN_LIST_DEPOSIT_PERMISSION": ADMIN_LIST_DEPOSIT_PERMISSION,
        "ADD_FORGE_MODERATOR_PERMISSION": ADD_FORGE_MODERATOR_PERMISSION,
        "MAILMAP_ADMIN_PERMISSION": MAILMAP_ADMIN_PERMISSION,
        "lang": "en",
        "sidebar_state": request.COOKIES.get("sidebar-state", "expanded"),
        "SWH_DJANGO_APPS": settings.SWH_DJANGO_APPS,
        "login_url": settings.LOGIN_URL,
        "logout_url": settings.LOGOUT_URL,
        "SWH_MIRROR_CONFIG": settings.SWH_MIRROR_CONFIG,
        "top_bar": config.get("top_bar", {}),
        "matomo": config.get("matomo", {}),
        "show_corner_ribbon": config.get("show_corner_ribbon", False),
        "corner_ribbon_text": config.get("corner_ribbon_text", ""),
        "activate_citations_ui": config.get("activate_citations_ui", False),
        "user_is_ambassador": (
            hasattr(request, "user")
            and request.user.has_perm(SWH_AMBASSADOR_PERMISSION)
        ),
    }

    if (
        "swh.web.save_code_now" in settings.SWH_DJANGO_APPS
        and hasattr(request, "user")
        and request.user.is_staff
    ):
        from swh.web.save_code_now.origin_save import has_pending_save_code_now_requests

        context["pending_save_code_now_requests"] = has_pending_save_code_now_requests()

    return context


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
            from swh.web.utils import archive

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
        self.body_prefix = [""]
        self.body_suffix = [""]


_HTML_WRITER = Writer()
_HTML_WRITER.translator_class = _NoHeaderHTMLTranslator


def rst_to_html(rst: str, raw_enabled: bool = False) -> str:
    """
    Convert reStructuredText document into HTML.

    Args:
        rst: A string containing a reStructuredText document

    Returns:
        Body content of the produced HTML conversion.

    """
    settings = {
        "initial_header_level": 2,
        "halt_level": 4,
        "traceback": True,
        "file_insertion_enabled": False,
        "raw_enabled": raw_enabled,
    }
    try:
        pp = publish_parts(rst, writer=_HTML_WRITER, settings_overrides=settings)
        return f'<div class="swh-rst">{pp["html_body"]}</div>'
    except SystemMessage:
        return f'<div class="swh-readme-txt"><pre>{rst}</pre></div>'


def _compute_final_cache_key(cache_key: str) -> str:
    key_prefix = get_config().get("instance_name", "localhost")
    return f"swh.web.cache.internal.{key_prefix}.{cache_key}"


def cache_set(
    cache_key: str,
    obj: Any,
    timeout: int = DEFAULT_TIMEOUT,
    extra_encoders: Optional[List[Tuple[type, str, Callable]]] = None,
) -> None:
    """Set a value in django cache.

    For optimizing cache size, the value to cache is serialized to binary
    using msgpack and then compressed with gzip.

    Args:
        cache_key: string key for the value to set in cache
        obj: value to store in cache
        timeout: the duration in seconds after which the cache expires
        extra_encoders: optional encoders for serializing types that are
            not default supported by msgpack, see :mod:`swh.core.api.serializers`
    """
    payload = gzip.compress(msgpack_dumps(obj, extra_encoders=extra_encoders))

    try:
        cache.set(_compute_final_cache_key(cache_key), payload, timeout=timeout)
    except Exception as exc:
        sentry_sdk.capture_exception(exc)


def cache_get(
    cache_key: str, extra_decoders: Optional[Dict[str, Callable]] = None
) -> Optional[Any]:
    """Get a value from the django cache.

    For optimizing cache size, values to cache are serialized to binary using
    msgpack and then compressed with gzip.

    Args:
        cache_key: string key for the value to get from cache
        extra_decoders: optional decoders for deserializing types that are
            not default supported by msgpack, see :mod:`swh.core.api.serializers`

    Returns:
        the cached value or :const:`None` if it does not exist
    """
    try:
        payload = cache.get(_compute_final_cache_key(cache_key))
    except Exception as exc:
        sentry_sdk.capture_exception(exc)
        payload = None
    return (
        msgpack_loads(gzip.decompress(payload), extra_decoders=extra_decoders)
        if payload
        else None
    )


def django_cache(
    timeout: int = DEFAULT_TIMEOUT,
    catch_exception: bool = False,
    exception_return_value: Any = None,
    invalidate_cache_pred: Callable[[Any], bool] = lambda val: False,
    extra_encoders: Optional[List[Tuple[type, str, Callable]]] = None,
    extra_decoders: Optional[Dict[str, Callable]] = None,
):
    """Decorator to put the result of a function call in Django cache,
    subsequent calls will directly return the cached value.

    For optimizing cache size, values to cache are serialized to binary using
    msgpack and then compressed with gzip.

    Args:
        timeout: The number of seconds value will be hold in cache
        catch_exception: If :const:`True`, any thrown exception by
            the decorated function will be caught and not reraised
        exception_return_value: The value to return if previous
            parameter is set to :const:`True`
        invalidate_cache_pred: A predicate function enabling to
            invalidate the cache under certain conditions, decorated
            function will then be called again
        extra_encoders: optional encoders for serializing types that are
            not default supported by msgpack, see :mod:`swh.core.api.serializers`
        extra_decoders: optional decoders for deserializing types that are
            not default supported by msgpack, see :mod:`swh.core.api.serializers`

    Returns:
        The returned value of the decorated function for the specified
        parameters

    """

    def hash_object(obj: Any) -> str:
        return hashlib.md5(
            msgpack_dumps(obj, extra_encoders=extra_encoders),
            usedforsecurity=False,
        ).hexdigest()

    def inner(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            func_args = args + (0,) + tuple(sorted(kwargs.items()))
            cache_key = hash_object((func.__module__, func.__name__))
            cache_key += hash_object(func_args)
            ret = cache_get(cache_key, extra_decoders=extra_decoders)
            if ret is None or invalidate_cache_pred(ret):
                try:
                    ret = func(*args, **kwargs)
                except Exception as exc:
                    if catch_exception:
                        sentry_capture_exception(exc)
                        return exception_return_value
                    else:
                        raise
                else:
                    cache_set(
                        cache_key,
                        ret,
                        timeout=timeout,
                        extra_encoders=extra_encoders,
                    )
            return ret

        return wrapper

    return inner


def _deposits_list_url(
    deposits_list_base_url: str, page_size: int, page: int, username: Optional[str]
) -> str:
    params = {"page_size": str(page_size), "page": page}
    if username is not None:
        params["username"] = username
    return f"{deposits_list_base_url}?{urllib.parse.urlencode(params)}"


def get_deposits_list(username: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return the list of software deposits using swh-deposit API"""
    config = get_config()["deposit"]
    if "private_api_url" not in config:
        return []
    private_api_url = config["private_api_url"].rstrip("/") + "/"
    deposits_list_base_url = private_api_url + "deposits/"
    deposits_list_auth = HTTPBasicAuth(
        config["private_api_user"], config["private_api_password"]
    )

    page = 1
    page_size = 1000
    deposits = []

    while True:
        deposits_list_url = _deposits_list_url(
            deposits_list_base_url, page_size=page_size, page=page, username=username
        )
        deposits_data = (
            requests.get(
                deposits_list_url,
                auth=deposits_list_auth,
                timeout=30,
            )
            .json()
            .get("results", [])
        )

        deposits += deposits_data
        page += 1

        if len(deposits_data) < page_size:
            break

    return deposits


_origin_visit_types_cache_timeout = 24 * 60 * 60  # 24 hours


def origin_visit_types(use_cache: bool = True) -> List[str]:
    """Return the exhaustive list of visit types for origins
    ingested into the archive.

    Args:
        use_cache: if :const:`True`, store visit types in django
            cache for 24 hours.
    """

    @django_cache(
        timeout=_origin_visit_types_cache_timeout,
        catch_exception=True,
        exception_return_value=[],
        invalidate_cache_pred=lambda val: not use_cache,
    )
    def _origin_visit_types_internal() -> List[str]:
        return sorted(search().visit_types_count().keys())

    return _origin_visit_types_internal()


def redirect_to_new_route(request, new_route, permanent=True):
    """Redirect a request to another route with url args and query parameters
    eg: /origin/<url:url-val>/log?path=test can be redirected as
    /log?url=<url-val>&path=test. This can be used to deprecate routes
    """
    request_path = resolve(request.path_info)
    args = {**request_path.kwargs, **request.GET.dict()}
    return redirect(
        reverse(new_route, query_params=args),
        permanent=permanent,
    )


def demangle_url(url: str) -> str:
    """Fix URL where the ``://`` character sequence was mangled into ``:/``
    by HTTP clients"""
    try:
        parsed_url = urllib.parse.urlparse(url)
        if (
            parsed_url.scheme
            and not parsed_url.netloc
            and url.startswith(f"{parsed_url.scheme}:/")
            and not url.startswith(f"{parsed_url.scheme}://")
        ):
            url = url.replace(f"{parsed_url.scheme}:/", f"{parsed_url.scheme}://", 1)
    except Exception:
        pass
    finally:
        return url


def datatables_pagination_params(request: HttpRequest) -> Tuple[int, int]:
    """Datatables paginations parameters.

    Args:
        request: an HttpRequest to get the length and start query parameters

    Returns:
        A tuple with the number of results per page and the current page number
    """

    length = min(int(request.GET.get("length", 10)), DATATABLES_MAX_PAGE_SIZE)
    page = int(request.GET.get("start", 0)) / length + 1
    return length, page


def strtobool(value: str) -> bool:
    """Convert a string representation of truth to True or False.

    Port of `distutils.util.strtobool` due to distutils deprecation and to better
    handle invalid values as BadInputExc exceptions will result in HTTP 400 errors.

    Raises:
        BadInputExc: ``value`` is not a valid truthy/falsy string
    """
    value = value.lower()
    if value in ["y", "yes", "t", "true", "on", "1"]:
        return True
    elif value in ["n", "no", "f", "false", "off", "0"]:
        return False
    raise BadInputExc(f"Invalid truth value {value}")
