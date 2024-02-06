# Copyright (C) 2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.urls import re_path as url

from .views import InboundEmailView

urlpatterns = [
    url(r"^inbound-email/$", InboundEmailView.as_view(), name="process-inbound-email")
]
