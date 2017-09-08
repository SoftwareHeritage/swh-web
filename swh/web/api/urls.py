# Copyright (C) 2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import swh.web.api.views.origin # noqa
import swh.web.api.views.content # noqa
import swh.web.api.views.person # noqa
import swh.web.api.views.release # noqa
import swh.web.api.views.revision # noqa
import swh.web.api.views.directory # noqa
import swh.web.api.views.entity # noqa
import swh.web.api.views.stat # noqa

from swh.web.api.apiurls import APIUrls

urlpatterns = APIUrls.get_url_patterns()
