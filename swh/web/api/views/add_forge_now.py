# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import json
from typing import Any, Dict, Union

from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models.query import QuerySet
from django.forms import CharField, ModelForm
from django.http import HttpResponseBadRequest
from django.http.request import HttpRequest
from django.http.response import HttpResponse, HttpResponseForbidden
from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.response import Response

from swh.web.add_forge_now.models import Request as AddForgeRequest
from swh.web.add_forge_now.models import RequestActorRole as AddForgeNowRequestActorRole
from swh.web.add_forge_now.models import RequestHistory as AddForgeNowRequestHistory
from swh.web.add_forge_now.models import RequestStatus as AddForgeNowRequestStatus
from swh.web.api.apidoc import api_doc, format_docstring
from swh.web.api.apiurls import api_route
from swh.web.auth.utils import ADD_FORGE_MODERATOR_PERMISSION
from swh.web.common.exc import BadInputExc
from swh.web.common.utils import has_add_forge_now_permission, reverse


def _block_while_testing():
    """Replaced by tests to check concurrency behavior"""
    pass


class AddForgeNowRequestForm(ModelForm):
    forge_contact_comment = CharField(
        required=False,
    )

    class Meta:
        model = AddForgeRequest
        fields = (
            "forge_type",
            "forge_url",
            "forge_contact_email",
            "forge_contact_name",
            "forge_contact_comment",
            "submitter_forward_username",
        )


class AddForgeNowRequestHistoryForm(ModelForm):
    new_status = CharField(
        max_length=200,
        required=False,
    )

    class Meta:
        model = AddForgeNowRequestHistory
        fields = ("text", "new_status")


class AddForgeNowRequestSerializer(serializers.ModelSerializer):
    inbound_email_address = serializers.CharField()
    forge_domain = serializers.CharField()

    last_moderator = serializers.SerializerMethodField()
    last_modified_date = serializers.SerializerMethodField()
    history: Dict[int, QuerySet] = {}

    class Meta:
        model = AddForgeRequest
        fields = "__all__"

    def _gethistory(self, request):
        if request.id not in self.history:
            self.history[request.id] = AddForgeNowRequestHistory.objects.filter(
                request=request
            ).order_by("id")
        return self.history[request.id]

    def get_last_moderator(self, request):
        last_history_with_moderator = (
            self._gethistory(request).filter(actor_role="MODERATOR").last()
        )
        return (
            last_history_with_moderator.actor if last_history_with_moderator else "None"
        )

    def get_last_modified_date(self, request):
        last_history = self._gethistory(request).last()
        return (
            last_history.date.isoformat().replace("+00:00", "Z")
            if last_history
            else None
        )


class AddForgeNowRequestPublicSerializer(serializers.ModelSerializer):
    """Serializes AddForgeRequest without private fields."""

    class Meta:
        model = AddForgeRequest
        fields = ("id", "forge_url", "forge_type", "status", "submission_date")


class AddForgeNowRequestHistorySerializer(serializers.ModelSerializer):
    message_source_url = serializers.SerializerMethodField()

    class Meta:
        model = AddForgeNowRequestHistory
        exclude = ("request", "message_source")

    def get_message_source_url(self, request_history):
        if request_history.message_source is None:
            return None

        return reverse(
            "forge-add-message-source",
            url_args={"id": request_history.pk},
            request=self.context["request"],
        )


class AddForgeNowRequestHistoryPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddForgeNowRequestHistory
        fields = ("id", "date", "new_status", "actor_role")


@api_route(
    r"/add-forge/request/create/",
    "api-1-add-forge-request-create",
    methods=["POST"],
)
@api_doc("/add-forge/request/create")
@format_docstring()
@transaction.atomic
def api_add_forge_request_create(request: Union[HttpRequest, Request]) -> HttpResponse:
    """
    .. http:post:: /api/1/add-forge/request/create/

        Create a new request to add a forge to the list of those crawled regularly
        by Software Heritage.

        .. warning::
            That endpoint is not publicly available and requires authentication
            in order to be able to request it.

        {common_headers}

        :<json string forge_type: the type of forge
        :<json string forge_url: the base URL of the forge
        :<json string forge_contact_email: email of an administator of the forge to
            contact
        :<json string forge_contact_name: the name of the administrator
        :<json string forge_contact_comment: to explain how Software Heritage can
            verify forge administrator info are valid

        :statuscode 201: request successfully created
        :statuscode 400: missing or invalid field values
        :statuscode 403: user not authenticated
    """
    if not request.user.is_authenticated:
        return HttpResponseForbidden(
            "You must be authenticated to create a new add-forge request"
        )

    add_forge_request = AddForgeRequest()

    if isinstance(request, Request):
        # request submitted with request body in JSON (goes through DRF)
        form = AddForgeNowRequestForm(request.data, instance=add_forge_request)
    else:
        # request submitted with request body in form encoded format
        # (directly handled by Django)
        form = AddForgeNowRequestForm(request.POST, instance=add_forge_request)

    if form.errors:
        raise BadInputExc(json.dumps(form.errors))

    try:
        existing_request = AddForgeRequest.objects.get(
            forge_url=add_forge_request.forge_url
        )
    except ObjectDoesNotExist:
        pass
    else:
        return Response(
            f"Request for forge already exists (id {existing_request.id})",
            status=409,  # Conflict
        )

    add_forge_request.submitter_name = request.user.username
    add_forge_request.submitter_email = request.user.email

    form.save()

    request_history = AddForgeNowRequestHistory()
    request_history.request = add_forge_request
    request_history.new_status = AddForgeNowRequestStatus.PENDING.name
    request_history.actor = request.user.username
    request_history.actor_role = AddForgeNowRequestActorRole.SUBMITTER.name
    request_history.save()

    data = AddForgeNowRequestSerializer(add_forge_request).data

    return Response(data=data, status=201)


@api_route(
    r"/add-forge/request/(?P<id>[0-9]+)/update/",
    "api-1-add-forge-request-update",
    methods=["POST"],
)
@api_doc("/add-forge/request/update", tags=["hidden"])
@format_docstring()
@transaction.atomic
def api_add_forge_request_update(
    request: Union[HttpRequest, Request], id: int
) -> HttpResponse:
    """
    .. http:post:: /api/1/add-forge/request/update/

        Update a request to add a forge to the list of those crawled regularly
        by Software Heritage.

        .. warning::
            That endpoint is not publicly available and requires authentication
            in order to be able to request it.

        {common_headers}

        :<json string text: comment about new request status
        :<json string new_status: the new request status

        :statuscode 200: request successfully updated
        :statuscode 400: missing or invalid field values
        :statuscode 403: user is not a moderator
    """
    if not request.user.is_authenticated:
        return HttpResponseForbidden(
            "You must be authenticated to update a new add-forge request"
        )

    if not has_add_forge_now_permission(request.user):
        return HttpResponseForbidden("You are not a moderator")

    add_forge_request = (
        AddForgeRequest.objects.filter(id=id).select_for_update().first()
    )

    if add_forge_request is None:
        return HttpResponseBadRequest("Invalid request id")

    request_history = AddForgeNowRequestHistory()
    request_history.request = add_forge_request

    if isinstance(request, Request):
        # request submitted with request body in JSON (goes through DRF)
        form = AddForgeNowRequestHistoryForm(request.data, instance=request_history)
    else:
        # request submitted with request body in form encoded format
        # (directly handled by Django)
        form = AddForgeNowRequestHistoryForm(request.POST, instance=request_history)

    if form.errors:
        raise BadInputExc(json.dumps(form.errors))

    new_status_str = form["new_status"].value()
    if new_status_str is not None:
        new_status = AddForgeNowRequestStatus[new_status_str]
        current_status = AddForgeNowRequestStatus[add_forge_request.status]
        if new_status not in current_status.allowed_next_statuses():
            raise BadInputExc(
                f"New request status {new_status} cannot be reached "
                f"from current status {add_forge_request.status}"
            )

    _block_while_testing()

    request_history.actor = request.user.username
    request_history.actor_role = AddForgeNowRequestActorRole.MODERATOR.name
    form.save(commit=False)

    if request_history.new_status == "":
        request_history.new_status = None

    request_history.save()

    if request_history.new_status is not None:
        add_forge_request.status = request_history.new_status
        add_forge_request.save()

    data = AddForgeNowRequestSerializer(add_forge_request).data
    return Response(data=data, status=200)


@api_route(
    r"/add-forge/request/list/",
    "api-1-add-forge-request-list",
    methods=["GET"],
)
@api_doc("/add-forge/request/list")
@format_docstring()
def api_add_forge_request_list(request: Request):
    """
    .. http:get:: /api/1/add-forge/request/list/

        List add forge requests submitted by users.

        {common_headers}
        {resheader_link}

        :query int page: optional page number
        :query int per_page: optional number of elements per page (bounded to 1000)

        :statuscode 200: always
    """

    add_forge_requests = AddForgeRequest.objects.order_by("-id")

    page_num = int(request.GET.get("page", 1))
    per_page = int(request.GET.get("per_page", 10))
    per_page = min(per_page, 1000)

    if (
        int(request.GET.get("user_requests_only", "0"))
        and request.user.is_authenticated
    ):
        add_forge_requests = add_forge_requests.filter(
            submitter_name=request.user.username
        )

    paginator = Paginator(add_forge_requests, per_page)
    page = paginator.page(page_num)

    if request.user.has_perm(ADD_FORGE_MODERATOR_PERMISSION):
        requests = AddForgeNowRequestSerializer(page.object_list, many=True).data
    else:
        requests = AddForgeNowRequestPublicSerializer(page.object_list, many=True).data

    results = [dict(request) for request in requests]

    response: Dict[str, Any] = {"results": results, "headers": {}}

    if page.has_previous():
        response["headers"]["link-prev"] = reverse(
            "api-1-add-forge-request-list",
            query_params={
                "page": page.previous_page_number(),
                "per_page": per_page,
            },
            request=request,
        )

    if page.has_next():
        response["headers"]["link-next"] = reverse(
            "api-1-add-forge-request-list",
            query_params={"page": page.next_page_number(), "per_page": per_page},
            request=request,
        )

    return response


@api_route(
    r"/add-forge/request/(?P<id>[0-9]+)/get/",
    "api-1-add-forge-request-get",
    methods=["GET"],
)
@api_doc("/add-forge/request/get")
@format_docstring()
def api_add_forge_request_get(request: Request, id: int):
    """
    .. http:get:: /api/1/add-forge/request/get/

        Return all details about an add-forge request.

        {common_headers}

        :param int id: add-forge request identifier

        :statuscode 200: request details successfully returned
        :statuscode 400: request identifier does not exist
    """

    try:
        add_forge_request = AddForgeRequest.objects.get(id=id)
    except ObjectDoesNotExist:
        raise BadInputExc("Request id does not exist")

    request_history = AddForgeNowRequestHistory.objects.filter(
        request=add_forge_request
    ).order_by("id")

    if request.user.is_authenticated and request.user.has_perm(
        ADD_FORGE_MODERATOR_PERMISSION
    ):
        data = AddForgeNowRequestSerializer(add_forge_request).data
        history = AddForgeNowRequestHistorySerializer(
            request_history, many=True, context={"request": request}
        ).data
    else:
        data = AddForgeNowRequestPublicSerializer(add_forge_request).data
        history = AddForgeNowRequestHistoryPublicSerializer(
            request_history, many=True
        ).data

    return {"request": data, "history": history}
