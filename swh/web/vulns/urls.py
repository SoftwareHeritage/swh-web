# Copyright (C) 2024-2026  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.web.vulns.api_views import vulns_api_urls

urlpatterns = vulns_api_urls.get_url_patterns()
