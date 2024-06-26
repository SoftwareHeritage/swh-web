# Copyright (C) 2017-2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.web.api.apiurls import api_urls
from swh.web.utils.url_path_converters import register_url_path_converters

register_url_path_converters()

import swh.web.api.views.citation  # noqa
import swh.web.api.views.content  # noqa
import swh.web.api.views.directory  # noqa
import swh.web.api.views.extid  # noqa
import swh.web.api.views.graph  # noqa
import swh.web.api.views.identifiers  # noqa
import swh.web.api.views.metadata  # noqa
import swh.web.api.views.origin  # noqa
import swh.web.api.views.ping  # noqa
import swh.web.api.views.raw  # noqa
import swh.web.api.views.release  # noqa
import swh.web.api.views.revision  # noqa
import swh.web.api.views.snapshot  # noqa
import swh.web.api.views.stat  # noqa

urlpatterns = api_urls.get_url_patterns()
