# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import json
from typing import Union

from django.core.exceptions import ObjectDoesNotExist
from django.forms import ModelForm
from django.http.request import HttpRequest
from django.http.response import HttpResponse, HttpResponseForbidden
from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.response import Response

from swh.web.add_forge_now.models import Request as AddForgeRequest
from swh.web.api.apidoc import api_doc, format_docstring
from swh.web.api.apiurls import api_route
from swh.web.common.exc import BadInputExc


class AddForgeNowRequestForm(ModelForm):
    class Meta:
        model = AddForgeRequest
        fields = (
            "forge_type",
            "forge_url",
            "forge_contact_email",
            "forge_contact_name",
            "forge_contact_comment",
        )


class AddForgeNowRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddForgeRequest
        fields = "__all__"


@api_route(
    r"/add-forge/request/create", "api-1-add-forge-request-create", methods=["POST"],
)
@api_doc("/add-forge/request/create")
@format_docstring()
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

    data = AddForgeNowRequestSerializer(add_forge_request).data

    return Response(data=data, status=201)
