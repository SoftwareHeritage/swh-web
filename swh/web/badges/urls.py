# Copyright (C) 2022-2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.urls import path as url

from swh.web.badges import swh_badge, swh_badge_swhid
from swh.web.utils.url_path_converters import register_url_path_converters

register_url_path_converters()

urlpatterns = [
    url(
        "badge/<swhid:object_swhid>/",
        swh_badge_swhid,
        name="swh-badge-swhid",
    ),
    url(
        "badge/<str:object_type>/<path:object_id>/",
        swh_badge,
        name="swh-badge",
    ),
]
