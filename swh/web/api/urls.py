# Copyright (C) 2017-2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import swh.web.api.views.content  # noqa
import swh.web.api.views.directory  # noqa
import swh.web.api.views.identifiers  # noqa
import swh.web.api.views.origin  # noqa
import swh.web.api.views.origin_save  # noqa
import swh.web.api.views.release  # noqa
import swh.web.api.views.revision  # noqa
import swh.web.api.views.snapshot  # noqa
import swh.web.api.views.stat  # noqa
import swh.web.api.views.vault  # noqa
import swh.web.api.views.ping  # noqa

from swh.web.api.apiurls import APIUrls

urlpatterns = APIUrls.get_url_patterns()
