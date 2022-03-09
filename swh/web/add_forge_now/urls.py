# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


from django.conf.urls import url

from swh.web.add_forge_now import views

urlpatterns = [
    url(r"^add/$", views.create_request, name="forge-add"),
    url(r"^moderation/$", views.moderation_dashboard, name="moderation-forge-add"),
    url(
        r"^request/(?P<request_id>.+)/$",
        views.request_dashboard,
        name="request-dashboard-forge-add",
    ),
]
