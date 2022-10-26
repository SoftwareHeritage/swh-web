# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from typing import List, Union

from django.urls import URLPattern, URLResolver

# register Web API endpoints
import swh.web.save_origin_webhooks.bitbucket  # noqa
import swh.web.save_origin_webhooks.gitea  # noqa
import swh.web.save_origin_webhooks.github  # noqa
import swh.web.save_origin_webhooks.gitlab  # noqa
import swh.web.save_origin_webhooks.sourceforge  # noqa

urlpatterns: List[Union[URLPattern, URLResolver]] = []
