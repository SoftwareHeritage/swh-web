# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from typing import Any, Dict

# from functools import wraps

from typing import List

from django import forms
from django.conf.urls import url
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404
from django.http.request import HttpRequest
from django.http.response import HttpResponse, JsonResponse
from django.shortcuts import render

from swh.web.add_forge_now.models import Request as AddForgeRequest
from swh.web.api.views.add_forge_now import (
    AddForgeNowRequestPublicSerializer,
    AddForgeNowRequestSerializer,
)
from swh.web.auth.utils import ADD_FORGE_MODERATOR_PERMISSION


def add_forge_request_list_datatables(request: HttpRequest) -> HttpResponse:
    """Dedicated endpoint used by datatables to display the add-forge
    requests in the Web UI.
    """

    draw = int(request.GET.get("draw", 0))

    add_forge_requests = AddForgeRequest.objects.all()

    table_data: Dict[str, Any] = {
        "recordsTotal": add_forge_requests.count(),
        "draw": draw,
    }

    search_value = request.GET.get("search[value]")

    column_order = request.GET.get("order[0][column]")
    field_order = request.GET.get(f"columns[{column_order}][name]", "id")
    order_dir = request.GET.get("order[0][dir]", "desc")

    if field_order:
        if order_dir == "desc":
            field_order = "-" + field_order
        add_forge_requests = add_forge_requests.order_by(field_order)

    per_page = int(request.GET.get("length", 10))
    page_num = int(request.GET.get("start", 0)) // per_page + 1

    if search_value:
        add_forge_requests = add_forge_requests.filter(
            Q(forge_type__icontains=search_value)
            | Q(forge_url__icontains=search_value)
            | Q(status__icontains=search_value)
        )

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

    table_data["recordsFiltered"] = add_forge_requests.count()
    table_data["data"] = results
    return JsonResponse(table_data)


urlpatterns = [
    url(
        r"^add-forge/request/list/datatables$",
        add_forge_request_list_datatables,
        name="add-forge-request-list-datatables",
    ),
]

FORGE_TYPES: List[str] = [
    "bitbucket",
    "cgit",
    "gitlab",
    "gitea",
    "heptapod",
]


class RequestForm(forms.Form):
    forge_type = forms.ChoiceField(choices=[(name, name) for name in FORGE_TYPES])
    forge_type.widget.attrs.update({"class": "form-control"})
    forge_url = forms.CharField(label="Forge contact name", max_length=200)
    forge_url.widget.attrs.update({"class": "form-control"})
    forge_contact_email = forms.EmailField(label="Forge contact email", max_length=100)
    forge_contact_email.widget.attrs.update({"class": "form-control"})
    forge_contact_name = forms.CharField(label="Forge contact name", max_length=100)
    forge_contact_name.widget.attrs.update({"class": "form-control"})
    forge_contact_comment = forms.CharField(label="Comment", widget=forms.Textarea)
    forge_contact_comment.widget.attrs.update({"class": "form-control", "rows": "3"})


class RequestUpdateForm(forms.Form):
    new_status = forms.ChoiceField(choices=[])
    new_status.widget.attrs.update({"class": "form-control", "id": "decisionOptions"})
    text = forms.CharField(label="Comment", widget=forms.Textarea)
    text.widget.attrs.update({"class": "form-control", "rows": "3"})


# def moderator_access(f):
#     """
#     """
#     @wraps(f)
#     def is_moderator(request, *args, **kws):
#         if not request.user.is_superuser:
#             raise Http404
#         return f(request, *args, **kws)
#     return moderator_access


def create_request(request):
    request_form = RequestForm()
    existing = AddForgeRequest.objects.all()
    return render(
        request,
        "add_forge_now/create-request.html",
        {"request_form": request_form, "existing": existing},
    )


# @moderator_access
def moderation_dashboard(request):
    """Moderation dashboard to allow listing current requests.

    """
    if not request.user.is_superuser:
        raise Http404("Page does not exist")
    existing = AddForgeRequest.objects.all()
    return render(request, "add_forge_now/moderation.html", {"existing": existing},)


# @moderator_access
def request_dashboard(request, request_id):
    """Moderation dashboard to allow listing current requests.

    Args:
        request: actual user query
        request_id: The add forge now request url (for now?)

    Return:
        Template response to moderate the request

    """

    # forge_request = AddForgeRequest.objects.get(forge_url=request_id)
    # forge_request_history = [
    #     {"date": "2022/03/10 15:44", "text": "submitted"},
    #     {"date": "2022/03/10 15:44", "text": "submitted"},
    #     {"date": "2022/03/10 15:44", "text": "submitted"},
    # ]
    if not request.user.is_superuser:
        raise Http404("Page does not exist")
    request_update_form = RequestUpdateForm()
    return render(
        request,
        "add_forge_now/request-dashboard.html",
        {"request_id": request_id, "request_update_form": request_update_form},
    )
