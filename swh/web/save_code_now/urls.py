# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.urls import re_path as url

from swh.web.save_code_now.admin_views import (
    admin_origin_save_add_authorized_url,
    admin_origin_save_add_unauthorized_url,
    admin_origin_save_authorized_urls_list,
    admin_origin_save_filters,
    admin_origin_save_remove_authorized_url,
    admin_origin_save_remove_unauthorized_url,
    admin_origin_save_request_accept,
    admin_origin_save_request_reject,
    admin_origin_save_request_remove,
    admin_origin_save_requests,
    admin_origin_save_unauthorized_urls_list,
)

# register Web API endpoints
from swh.web.save_code_now.api_views import save_code_now_api_urls
from swh.web.save_code_now.views import (
    origin_save_help_view,
    origin_save_list_view,
    origin_save_requests_list,
    save_origin_task_info,
)

urlpatterns = [
    url(r"^save/$", origin_save_help_view, name="origin-save"),
    url(r"^save/list/$", origin_save_list_view, name="origin-save-list"),
    url(
        r"^save/requests/list/(?P<status>.+)/$",
        origin_save_requests_list,
        name="origin-save-requests-list",
    ),
    url(
        r"^save/task/info/(?P<save_request_id>.+)/$",
        save_origin_task_info,
        name="origin-save-task-info",
    ),
    url(
        r"^admin/origin/save/requests/$",
        admin_origin_save_requests,
        name="admin-origin-save-requests",
    ),
    url(
        r"^admin/origin/save/filters/$",
        admin_origin_save_filters,
        name="admin-origin-save-filters",
    ),
    url(
        r"^admin/origin/save/authorized_urls/list/$",
        admin_origin_save_authorized_urls_list,
        name="admin-origin-save-authorized-urls-list",
    ),
    url(
        r"^admin/origin/save/authorized_urls/add/(?P<origin_url>.+)/$",
        admin_origin_save_add_authorized_url,
        name="admin-origin-save-add-authorized-url",
    ),
    url(
        r"^admin/origin/save/authorized_urls/remove/(?P<origin_url>.+)/$",
        admin_origin_save_remove_authorized_url,
        name="admin-origin-save-remove-authorized-url",
    ),
    url(
        r"^admin/origin/save/unauthorized_urls/list/$",
        admin_origin_save_unauthorized_urls_list,
        name="admin-origin-save-unauthorized-urls-list",
    ),
    url(
        r"^admin/origin/save/unauthorized_urls/add/(?P<origin_url>.+)/$",
        admin_origin_save_add_unauthorized_url,
        name="admin-origin-save-add-unauthorized-url",
    ),
    url(
        r"^admin/origin/save/unauthorized_urls/remove/(?P<origin_url>.+)/$",
        admin_origin_save_remove_unauthorized_url,
        name="admin-origin-save-remove-unauthorized-url",
    ),
    url(
        r"^admin/origin/save/request/accept/(?P<visit_type>.+)/url/(?P<origin_url>.+)/$",
        admin_origin_save_request_accept,
        name="admin-origin-save-request-accept",
    ),
    url(
        r"^admin/origin/save/request/reject/(?P<visit_type>.+)/url/(?P<origin_url>.+)/$",
        admin_origin_save_request_reject,
        name="admin-origin-save-request-reject",
    ),
    url(
        r"^admin/origin/save/request/remove/(?P<sor_id>.+)/$",
        admin_origin_save_request_remove,
        name="admin-origin-save-request-remove",
    ),
    *save_code_now_api_urls.get_url_patterns(),
]
