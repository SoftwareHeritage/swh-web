# Copyright (C) 2018-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.urls import re_path as url

from swh.web.config import get_config

urlpatterns = []
# when running end to end tests through cypress, declare some extra
# endpoints to provide input data for some of those tests
if get_config()["e2e_tests_mode"]:
    from swh.web.tests.views import (
        get_content_code_data_all_exts,
        get_content_code_data_all_filenames,
        get_content_code_data_by_ext,
        get_content_code_data_by_filename,
        get_content_other_data_by_ext,
    )

    urlpatterns = [
        url(
            r"^tests/data/content/code/extension/(?P<ext>.+)/$",
            get_content_code_data_by_ext,
            name="tests-content-code-extension",
        ),
        url(
            r"^tests/data/content/other/extension/(?P<ext>.+)/$",
            get_content_other_data_by_ext,
            name="tests-content-other-extension",
        ),
        url(
            r"^tests/data/content/code/extensions/$",
            get_content_code_data_all_exts,
            name="tests-content-code-extensions",
        ),
        url(
            r"^tests/data/content/code/filename/(?P<filename>.+)/$",
            get_content_code_data_by_filename,
            name="tests-content-code-filename",
        ),
        url(
            r"^tests/data/content/code/filenames/$",
            get_content_code_data_all_filenames,
            name="tests-content-code-filenames",
        ),
    ]
