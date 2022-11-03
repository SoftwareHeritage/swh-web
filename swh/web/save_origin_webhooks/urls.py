# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


# register Web API endpoints
import swh.web.save_origin_webhooks.bitbucket  # noqa
import swh.web.save_origin_webhooks.gitea  # noqa
import swh.web.save_origin_webhooks.github  # noqa
import swh.web.save_origin_webhooks.gitlab  # noqa
import swh.web.save_origin_webhooks.sourceforge  # noqa

from swh.web.save_origin_webhooks.generic_receiver import (  # isort: skip
    webhooks_api_urls,
)

urlpatterns = webhooks_api_urls.get_url_patterns()
