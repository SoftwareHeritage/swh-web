# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.urls import re_path as url

from swh.web.mailmap.views import (
    admin_mailmap,
    profile_add_mailmap,
    profile_list_mailmap,
    profile_list_mailmap_datatables,
    profile_update_mailmap,
)

urlpatterns = [
    url(
        r"^profile/mailmap/list/$",
        profile_list_mailmap,
        name="profile-mailmap-list",
    ),
    url(
        r"^profile/mailmap/add/$",
        profile_add_mailmap,
        name="profile-mailmap-add",
    ),
    url(
        r"^profile/mailmap/update/$",
        profile_update_mailmap,
        name="profile-mailmap-update",
    ),
    url(
        r"^profile/mailmap/list/datatables/$",
        profile_list_mailmap_datatables,
        name="profile-mailmap-list-datatables",
    ),
    url(r"^admin/mailmap/$", admin_mailmap, name="admin-mailmap"),
]
