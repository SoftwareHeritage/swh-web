# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.urls import re_path as url

from swh.web.badges import swh_badge, swh_badge_swhid

urlpatterns = [
    url(
        r"^badge/(?P<object_type>[a-z]+)/(?P<object_id>.+)/$",
        swh_badge,
        name="swh-badge",
    ),
    url(
        r"^badge/(?P<object_swhid>swh:[0-9]+:[a-z]+:[0-9a-f]+.*)/$",
        swh_badge_swhid,
        name="swh-badge-swhid",
    ),
]
