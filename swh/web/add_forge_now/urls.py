# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.urls import re_path as url

from swh.web.add_forge_now.admin_views import (
    add_forge_now_request_dashboard,
    add_forge_now_requests_moderation_dashboard,
)

# register Web API endpoints
from swh.web.add_forge_now.api_views import add_forge_now_api_urls
from swh.web.add_forge_now.views import (
    add_forge_request_list_datatables,
    create_request_create,
    create_request_help,
    create_request_list,
    create_request_message_source,
)

urlpatterns = [
    url(
        r"^add-forge/request/list/datatables/$",
        add_forge_request_list_datatables,
        name="add-forge-request-list-datatables",
    ),
    url(r"^add-forge/request/create/$", create_request_create, name="forge-add-create"),
    url(r"^add-forge/request/list/$", create_request_list, name="forge-add-list"),
    url(
        r"^add-forge/request/message-source/(?P<id>\d+)/$",
        create_request_message_source,
        name="forge-add-message-source",
    ),
    url(r"^add-forge/request/help/$", create_request_help, name="forge-add-help"),
    url(
        r"^admin/add-forge/requests/$",
        add_forge_now_requests_moderation_dashboard,
        name="add-forge-now-requests-moderation",
    ),
    url(
        r"^admin/add-forge/request/(?P<request_id>(\d)+)/$",
        add_forge_now_request_dashboard,
        name="add-forge-now-request-dashboard",
    ),
] + add_forge_now_api_urls.get_url_patterns()
