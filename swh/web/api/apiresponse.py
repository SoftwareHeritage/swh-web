# Copyright (C) 2017-2025 The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import json
import logging
import traceback
from typing import Any, Dict, Optional

from django.http import HttpResponse
from django.shortcuts import render
from django.urls import get_resolver
from django.utils.cache import add_never_cache_headers
from django.utils.html import escape
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.utils.encoders import JSONEncoder

from swh.storage.exc import StorageAPIError, StorageDBError
from swh.web.api import utils
from swh.web.config import get_config
from swh.web.utils import gen_path_info, shorten_path
from swh.web.utils.exc import (
    BadInputExc,
    ForbiddenExc,
    LargePayloadExc,
    MaskedObjectException,
    NotFoundExc,
    UnauthorizedExc,
    masked_to_common_types,
    sentry_capture_exception,
)

logger = logging.getLogger("django")


def compute_link_header(rv: Dict[str, Any]) -> Dict[str, Any]:
    """Add Link header in returned value results.

    Args:
        request: a DRF Request object
        rv: dictionary with keys:

            - headers: potential headers with 'link-next' and 'link-prev'
              keys
            - results: containing the result to return

    Returns:
        Headers with computed Link header

    """
    link_headers = []

    if "headers" not in rv:
        return {}

    rv_headers = rv["headers"]

    if "link-next" in rv_headers:
        link_headers.append(f'<{rv_headers.pop("link-next")}>; rel="next"')
    if "link-prev" in rv_headers:
        link_headers.append(f'<{rv_headers.pop("link-prev")}>; rel="previous"')

    if link_headers:
        link_header_str = ",".join(link_headers)
        rv_headers.update({"Link": link_header_str})

    return rv_headers


def filter_by_fields(request: Request, data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract a request parameter 'fields' if it exists to permit the filtering on
    the data dict's keys.

    If such field is not provided, returns the data as is.

    """
    fields = request.query_params.get("fields")
    if fields:
        data = utils.filter_field_keys(data, set(fields.split(",")))

    return data


def transform(rv: Dict[str, Any]) -> Dict[str, Any]:
    """Transform an eventual returned value with multiple layer of
    information with only what's necessary.

    If the returned value rv contains the 'results' key, this is the
    associated value which is returned.

    Otherwise, return the initial dict without the potential 'headers'
    key.

    """
    if "results" in rv:
        return rv["results"]

    if "headers" in rv:
        rv.pop("headers")

    return rv


def make_api_response(
    request: Request,
    data: Dict[str, Any],
    doc_data: Optional[Dict[str, Any]] = None,
    options: Optional[Dict[str, Any]] = None,
) -> HttpResponse:
    """Generates an API response based on the requested mimetype.

    Args:
        request: a DRF Request object
        data: raw data to return in the API response
        doc_data: documentation data for HTML response
        options: optional data that can be used to generate the response

    Returns:
        a DRF Response a object

    """
    options = options or {}
    if data:
        options["headers"] = compute_link_header(data)
        data = transform(data)
        data = filter_by_fields(request, data)
    doc_data = doc_data or {}
    headers = {}
    if "headers" in options:
        doc_data["headers_data"] = options["headers"]
        headers = options["headers"]

    # get request status code
    doc_data["status_code"] = options.get("status", 200)

    accepted_media_type = getattr(request, "accepted_media_type", "application/json")

    # when requesting HTML, typically when browsing the API through its
    # documented views, we need to enrich the input data with documentation
    # and render the apidoc HTML template
    if accepted_media_type == "text/html":
        doc_data["response_data"] = data
        if data is not None:
            doc_data["response_data"] = json.dumps(
                data, cls=JSONEncoder, sort_keys=True, indent=4, separators=(",", ": ")
            )

        doc_data["heading"] = shorten_path(str(request.path))

        # generate breadcrumbs data
        if "route" in doc_data:
            all_view_names = set(get_resolver().reverse_dict.keys())
            doc_data["endpoint_path"] = gen_path_info(doc_data["route"])
            for i in range(len(doc_data["endpoint_path"]) - 1):
                view_name = "api-1-" + "-".join(
                    [doc_data["endpoint_path"][i]["name"] for i in range(i + 1)]
                )
                if view_name in all_view_names:
                    doc_data["endpoint_path"][i]["path"] += "/doc/"
                else:
                    doc_data["endpoint_path"][i]["path"] = ""
            if not doc_data["noargs"]:
                doc_data["endpoint_path"][-1]["path"] += "/doc/"

        response = render(
            request, "apidoc.html", doc_data, status=doc_data["status_code"]
        )

    # otherwise simply return the raw data and let DRF picks
    # the correct renderer (JSON or YAML)
    else:
        response = Response(
            data,
            headers=headers,
            content_type=accepted_media_type,
            status=doc_data["status_code"],
        )

    if getattr(request, "never_cache", False):
        add_never_cache_headers(response)

    return response


def error_response(
    request: Request, exception: Exception, doc_data: Dict[str, Any]
) -> HttpResponse:
    """Private function to create a custom error response.

    Args:
        request: a DRF Request object
        error: the exception that caused the error
        doc_data: documentation data for HTML response

    """
    error_data: dict[str, Any]
    error_data = {
        "exception": exception.__class__.__name__,
        "reason": str(exception),
    }
    if hasattr(exception, "extra_error_data") and isinstance(
        exception.extra_error_data, dict
    ):
        error_data.update(exception.extra_error_data)

    error_code = 500
    if isinstance(exception, BadInputExc):
        error_code = 400
    elif isinstance(exception, ValidationError):
        error_code = 400
        error_data["reason"] = exception.detail
    elif isinstance(exception, UnauthorizedExc):
        error_code = 401
    elif isinstance(exception, NotFoundExc):
        error_code = 404
    elif isinstance(exception, ForbiddenExc):
        error_code = 403
    elif isinstance(exception, MaskedObjectException):
        error_code = 403
        error_data["masked"] = masked_to_common_types(exception)
    elif isinstance(exception, LargePayloadExc):
        error_code = 413
    elif isinstance(exception, StorageDBError):
        error_code = 503
    elif isinstance(exception, StorageAPIError):
        error_code = 503
    elif isinstance(exception, APIException):
        error_code = exception.status_code

    error_opts = {"status": error_code}

    if getattr(request, "accepted_media_type", None) == "text/html":
        error_data["reason"] = escape(error_data["reason"])

    if get_config()["debug"]:
        error_data["traceback"] = traceback.format_exc()
        logger.error(error_data["traceback"])

    return make_api_response(request, error_data, doc_data, options=error_opts)


def error_response_handler(
    exc: Exception, context: Dict[str, Any]
) -> Optional[HttpResponse]:
    """Custom DRF exception handler used to generate API error responses."""
    sentry_capture_exception(exc)
    doc_data = getattr(exc, "doc_data", {})
    return error_response(context["request"], exc, doc_data)
