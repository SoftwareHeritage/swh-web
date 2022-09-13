# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.urls import re_path as url

from swh.web.metrics.views import prometheus_metrics

urlpatterns = [
    url(r"^metrics/prometheus/$", prometheus_metrics, name="metrics-prometheus"),
]
