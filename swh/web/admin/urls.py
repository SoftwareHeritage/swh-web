# Copyright (C) 2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.conf.urls import url
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect

from swh.web.admin.adminurls import AdminUrls

import swh.web.admin.origin_save # noqa
import swh.web.admin.deposit # noqa


def admin_default_view(request):
    return redirect('admin-origin-save')


urlpatterns = [url(r'^$', admin_default_view, name='admin'),
               url(r'^login/$', auth_views.login,
                   {'template_name': 'login.html'}, name='login'),
               url(r'^logout/$', auth_views.logout,
                   {'template_name': 'logout.html'}, name='logout')]

urlpatterns += AdminUrls.get_url_patterns()
