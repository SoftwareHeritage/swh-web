# Copyright (C) 2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import json

from django.conf.urls import url, include
from django.contrib.staticfiles import finders
from django.shortcuts import render

from swh.web.config import get_config


def _jslicenses(request):
    jslicenses_file = finders.find('jssources/jslicenses.json')
    jslicenses_data = json.load(open(jslicenses_file))
    jslicenses_data = sorted(jslicenses_data.items(),
                             key=lambda item: item[0].split('/')[-1])
    return render(request, "misc/jslicenses.html",
                  {'jslicenses_data': jslicenses_data})


urlpatterns = [
    url(r'^', include('swh.web.misc.coverage')),
    url(r'^jslicenses/$', _jslicenses, name='jslicenses'),
    url(r'^', include('swh.web.misc.origin_save')),
]


# when running end to end tests trough cypress, declare some extra
# endpoints to provide input data for some of those tests
if get_config()['e2e_tests_mode']:
    from swh.web.tests.data import (
        get_content_code_data_by_ext,
        get_content_other_data_by_ext,
        get_content_code_data_all_exts,
        get_content_code_data_by_filename,
        get_content_code_data_all_filenames,
     ) # noqa
    urlpatterns.append(
        url(r'^tests/data/content/code/extension/(?P<ext>.+)/$',
            get_content_code_data_by_ext,
            name='tests-content-code-extension'))
    urlpatterns.append(
        url(r'^tests/data/content/other/extension/(?P<ext>.+)/$',
            get_content_other_data_by_ext,
            name='tests-content-other-extension'))
    urlpatterns.append(url(r'^tests/data/content/code/extensions/$',
                           get_content_code_data_all_exts,
                           name='tests-content-code-extensions'))
    urlpatterns.append(
        url(r'^tests/data/content/code/filename/(?P<filename>.+)/$',
            get_content_code_data_by_filename,
            name='tests-content-code-filename'))
    urlpatterns.append(url(r'^tests/data/content/code/filenames/$',
                           get_content_code_data_all_filenames,
                           name='tests-content-code-filenames'))
