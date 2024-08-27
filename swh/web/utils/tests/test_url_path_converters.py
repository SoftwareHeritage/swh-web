# Copyright (C) 2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import pytest

from django.http.response import HttpResponse
from django.test.utils import override_settings
from django.urls import path

from swh.model.swhids import CoreSWHID, QualifiedSWHID
from swh.web.tests.helpers import check_http_get_response
from swh.web.utils import reverse
from swh.web.utils.url_path_converters import register_url_path_converters


def sample_swhid_view(request, swhid: str) -> HttpResponse:
    return HttpResponse(swhid, content_type="text/plain")


register_url_path_converters()

urlpatterns = [
    path(
        "sample/<swhid:swhid>/",
        sample_swhid_view,
        name="sample-swhid-view",
    ),
]


@pytest.fixture
def core_swhid() -> CoreSWHID:
    return CoreSWHID.from_string("swh:1:cnt:" + "1" * 40)


@override_settings(ROOT_URLCONF=__name__, MIDDLEWARE=[])
def test_sample_swhid_view_core_swhid_object(client, core_swhid):
    core_swhid_str = str(core_swhid)
    url = reverse("sample-swhid-view", url_args={"swhid": core_swhid})
    assert core_swhid_str in url
    resp = check_http_get_response(client, url, status_code=200)
    assert resp.content.decode() == core_swhid_str


@override_settings(ROOT_URLCONF=__name__, MIDDLEWARE=[])
def test_sample_swhid_view_core_swhid_str(client, core_swhid):
    core_swhid_str = str(core_swhid)
    url = reverse("sample-swhid-view", url_args={"swhid": core_swhid_str})
    resp = check_http_get_response(client, url, status_code=200)
    assert resp.content.decode() == core_swhid_str


@override_settings(ROOT_URLCONF=__name__, MIDDLEWARE=[])
def test_sample_swhid_view_core_swhid_str_upper(client, core_swhid):
    core_swhid_str = str(core_swhid)
    core_swhid_str_upper = core_swhid_str.upper()
    url = reverse("sample-swhid-view", url_args={"swhid": core_swhid_str_upper})
    assert core_swhid_str_upper in url
    resp = check_http_get_response(client, url, status_code=200)
    assert resp.content.decode() == core_swhid_str


@pytest.fixture
def qualified_swhid(core_swhid) -> QualifiedSWHID:
    return QualifiedSWHID.from_string(str(core_swhid) + ";path=Foo/Bar")


@override_settings(ROOT_URLCONF=__name__, MIDDLEWARE=[])
def test_sample_swhid_view_qualified_swhid_object(client, qualified_swhid):
    qualified_swhid_str = str(qualified_swhid)
    url = reverse("sample-swhid-view", url_args={"swhid": qualified_swhid})
    assert qualified_swhid_str in url
    resp = check_http_get_response(client, url, status_code=200)
    assert resp.content.decode() == qualified_swhid_str


@override_settings(ROOT_URLCONF=__name__, MIDDLEWARE=[])
def test_sample_swhid_view_qualified_swhid_str(client, qualified_swhid):
    qualified_swhid_str = str(qualified_swhid)
    url = reverse("sample-swhid-view", url_args={"swhid": qualified_swhid_str})
    assert qualified_swhid_str in url
    resp = check_http_get_response(client, url, status_code=200)
    assert resp.content.decode() == qualified_swhid_str


@override_settings(ROOT_URLCONF=__name__, MIDDLEWARE=[])
def test_sample_swhid_view_qualified_swhid_str_upper(client, qualified_swhid):
    core_swhid_str, qualifiers = str(qualified_swhid).split(";", maxsplit=1)
    qualified_swhid_str_upper = f"{core_swhid_str.upper()};{qualifiers}"
    url = reverse(
        "sample-swhid-view",
        url_args={"swhid": qualified_swhid_str_upper},
    )
    assert qualified_swhid_str_upper in url
    resp = check_http_get_response(client, url, status_code=200)
    assert resp.content.decode() == str(qualified_swhid)
