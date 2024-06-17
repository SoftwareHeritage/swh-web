# Copyright (C) 2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.urls import path as url

from swh.web.save_bulk.api_views import save_bulk_api_urls
from swh.web.save_bulk.views import api_save_bulk_origins_list

urlpatterns = [
    url(
        "origin/save/bulk/<uuid:request_id>/list/",
        api_save_bulk_origins_list,
        name="save-origin-bulk-origins-list",
    ),
]
urlpatterns += save_bulk_api_urls.get_url_patterns()
