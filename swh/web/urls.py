# Copyright (C) 2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import django

from django.conf.urls import url, include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.shortcuts import redirect
from django.views.generic.base import RedirectView

favicon_view = RedirectView.as_view(url='/static/img/icons/swh-logo-32x32.png',
                                    permanent=True)


def default_view(request):
    return redirect('api_homepage')


urlpatterns = [
    url(r'^favicon\.ico$', favicon_view),
    url(r'^api/', include('swh.web.api.urls')),
    url(r'^browse/', include('swh.web.browse.urls')),
    url(r'^$', default_view),
]


urlpatterns += staticfiles_urlpatterns()

# hack in order for our custom template tag library
# to load on django 1.7 (debian jessie version)
if django.VERSION < (1, 8):
    from django.template.base import templatetags_modules # noqa
    templatetags_modules += ['django.templatetags',
                             'django.contrib.admin.templatetags',
                             'django.contrib.staticfiles.templatetags',
                             'rest_framework.templatetags', 'swh.web.common']
