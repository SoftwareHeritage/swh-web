# Copyright (C) 2015-2025  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import logging
import traceback
from typing import Optional, TypeVar

from django_ratelimit.exceptions import Ratelimited
import sentry_sdk

from django.core import exceptions
from django.http import HttpRequest, HttpResponse
from django.http.response import (
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseNotFound,
    HttpResponseServerError,
    JsonResponse,
)
from django.shortcuts import render
from django.template import loader
from django.utils.html import escape, format_html
from rest_framework.exceptions import APIException
from rest_framework.renderers import JSONRenderer

from swh.core.api import RemoteException, TransientRemoteException
from swh.storage.exc import MaskedObjectException
from swh.web.api.renderers import YAMLRenderer
from swh.web.config import get_config

logger = logging.getLogger("django")


class BadInputExc(ValueError):
    """Wrong request to the api.

    Example: Asking a content with the wrong identifier format.

    """

    pass


class NotFoundExc(exceptions.ObjectDoesNotExist):
    """Good request to the api but no result were found.

    Example: Asking a content with the right identifier format but
    that content does not exist.

    """

    def __str__(self):
        return self.args[0]


class ForbiddenExc(exceptions.PermissionDenied):
    """Good request to the api, forbidden result to return due to enforce
       policy.

    Example: Asking for a raw content which exists but whose mimetype
    is not text.

    """

    pass


class UnauthorizedExc(Exception):
    """Request to Web API endpoint requires authentication."""

    pass


class LargePayloadExc(Exception):
    """The input size is too large.

    Example: Asking to resolve 10000 SWHIDs when the limit is 1000.
    """

    pass


http_status_code_message = {
    400: "Bad Request",
    401: "Unauthorized",
    403: "Access Denied",
    404: "Resource not found",
    413: "Payload Too Large",
    429: "Too Many Requests",
    500: "Internal Server Error",
    501: "Not Implemented",
    502: "Bad Gateway",
    503: "Service unavailable",
}

HttpResponseType = TypeVar("HttpResponseType", bound=HttpResponse)


def _generate_error_page(
    request: HttpRequest,
    error_description: str,
    http_response: type[HttpResponseType],
) -> HttpResponseType:
    error_code = http_response.status_code
    error_data = {
        "error": http_status_code_message[error_code],
        "reason": error_description,
    }

    accepted_media_type = request.headers.get("Accept", "application/json")

    # ensure django error is returned using same content type as Accept request header
    if accepted_media_type in ("application/json", "*/*"):
        return http_response(
            JSONRenderer().render(error_data),
            content_type="application/json",
        )
    elif accepted_media_type == "application/yaml":
        return http_response(
            YAMLRenderer().render(error_data),
            content_type="application/yaml",
        )
    else:
        return http_response(
            loader.render_to_string(
                template_name="error.html",
                context={
                    "error_code": error_code,
                    "error_message": http_status_code_message[error_code],
                    "error_description": error_description,
                },
                request=request,
            ),
            content_type="text/html",
        )


def masked_to_common_types(exc: MaskedObjectException):
    """Convert ``exc.masked`` to common types, suitable for
    JSON and YAML encoding.

    ExtendedSWHID becomes strings and MaskedStatus becomes a dict.
    """
    return {
        str(swhid): [
            {
                "request": status.request,
                "status": status.state.name.lower().replace("_", "-"),
            }
            for status in statuses
        ]
        for swhid, statuses in exc.masked.items()
    }


def _generate_masked_object_page(
    request: HttpRequest, exc: MaskedObjectException
) -> HttpResponse:
    error_code = 403  # Forbidden
    error_data = {
        "error": http_status_code_message[error_code],
        "reason": str(exc),
        "masked": masked_to_common_types(exc),
    }

    accepted_media_type = request.headers.get("Accept", "application/json")

    if accepted_media_type in ("application/json", "*/*"):
        return JsonResponse(
            error_data,
            status=error_code,
        )
    elif accepted_media_type == "application/yaml":
        return HttpResponse(
            YAMLRenderer().render(error_data),
            content_type="application/yaml",
            status=error_code,
        )
    else:
        return render(
            request,
            "masked.html",
            {
                "error_code": error_code,
                "error_message": "Access restricted",
                "error_description": str(exc),
                "masked": exc.masked,
            },
            status=error_code,
        )


def swh_handle400(
    request: HttpRequest,
    exception: Optional[Exception] = None,
    template_name: str = "",
) -> HttpResponseBadRequest:
    """
    Custom Django HTTP error 400 handler for swh-web.
    """
    error_description = (
        "The server cannot process the request to %s due to "
        "something that is perceived to be a client error."
        % escape(request.META["PATH_INFO"])
    )
    return _generate_error_page(request, error_description, HttpResponseBadRequest)


def swh_handle403(
    request,
    exception: Optional[Exception] = None,
    template_name: str = "",
) -> HttpResponseForbidden:
    """
    Custom Django HTTP error 403 handler for swh-web.
    """
    error_description = "The resource %s requires an authentication." % escape(
        request.META["PATH_INFO"]
    )
    return _generate_error_page(request, error_description, HttpResponseForbidden)


def swh_handle404(
    request,
    exception: Optional[Exception] = None,
    template_name: str = "",
) -> HttpResponseNotFound:
    """
    Custom Django HTTP error 404 handler for swh-web.
    """
    error_description = "The resource %s could not be found on the server." % escape(
        request.META["PATH_INFO"]
    )
    return _generate_error_page(request, error_description, HttpResponseNotFound)


def swh_handle500(
    request: HttpRequest,
    template_name: str = "",
) -> HttpResponseServerError:
    """
    Custom Django HTTP error 500 handler for swh-web.
    """
    error_description = (
        "An unexpected condition was encountered when "
        "requesting resource %s." % escape(request.META["PATH_INFO"])
    )
    return _generate_error_page(request, error_description, HttpResponseServerError)


def sentry_capture_exception(exc: Exception) -> None:
    if isinstance(
        exc,
        (
            exceptions.ObjectDoesNotExist,
            exceptions.DisallowedHost,
            exceptions.PermissionDenied,
            BadInputExc,
            NotFoundExc,
            RemoteException,
            TransientRemoteException,
            Ratelimited,
            UnauthorizedExc,
        ),
    ):
        # ignore noisy exceptions we cannot do anything about
        pass
    elif isinstance(exc, APIException) and 400 <= exc.status_code < 500:
        # ignore client errors (4xx status codes)
        pass
    else:
        # log everything else
        sentry_sdk.capture_exception(exc)


class HttpResponseUnauthorized(HttpResponse):
    status_code = 401


class HttpResponseTooManyRequests(HttpResponse):
    status_code = 429


def handle_view_exception(request: HttpRequest, exc: Exception) -> HttpResponse:
    """
    Function used to generate an error page when an exception
    was raised inside a swh-web browse view.
    """
    sentry_capture_exception(exc)

    error_description = format_html("{}: {}", type(exc).__name__, str(exc))
    if get_config()["debug"]:
        traceback_str = traceback.format_exc()
        logger.error(traceback_str)
        error_description = escape(traceback_str)

    http_response: type[HttpResponse] = HttpResponseServerError
    if isinstance(exc, BadInputExc):
        http_response = HttpResponseBadRequest
    elif isinstance(exc, UnauthorizedExc):
        http_response = HttpResponseUnauthorized
    elif isinstance(exc, ForbiddenExc):
        http_response = HttpResponseForbidden
    elif isinstance(exc, NotFoundExc):
        http_response = HttpResponseNotFound
    elif isinstance(exc, Ratelimited):
        http_response = HttpResponseTooManyRequests
    elif isinstance(exc, MaskedObjectException):
        return _generate_masked_object_page(request, exc)

    resp = _generate_error_page(request, error_description, http_response)
    if get_config()["debug"]:
        resp.traceback = error_description  # type: ignore[attr-defined]
    return resp
