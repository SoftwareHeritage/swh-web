# Copyright (C) 2022-2023  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.urls import re_path as url

from swh.web.banners.views import downtime_banner, fundraising_banner, hiring_banner

urlpatterns = [
    url(r"^fundraising/banner/$", fundraising_banner, name="swh-fundraising-banner"),
    url(r"^hiring/banner/$", hiring_banner, name="swh-hiring-banner"),
    url(r"^downtime/banner/$", downtime_banner, name="swh-downtime-banner"),
]
