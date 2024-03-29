# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


from swh.web.api.apiurls import api_route
from swh.web.tests.helpers import check_api_get_responses
from swh.web.utils import reverse


@api_route(r"/some/route/(?P<int_arg>[0-9]+)/", "api-1-some-route")
def api_some_route(request, int_arg):
    return {"result": int(int_arg)}


@api_route(
    r"/never/cache/route/(?P<int_arg>[0-9]+)/",
    "api-1-never-cache-route",
    never_cache=True,
)
def api_never_cache_route(request, int_arg):
    return {"result": int(int_arg)}


@api_route(
    r"/never/cache/route/error/",
    "api-1-never-cache-route-with-error",
    never_cache=True,
)
def api_never_cache_route_with_error(request):
    raise Exception("error")


def test_api_route_with_cache(api_client):
    url = reverse("api-1-some-route", url_args={"int_arg": 1})
    resp = check_api_get_responses(api_client, url, status_code=200)
    assert resp.data == {"result": 1}
    assert "Cache-Control" not in resp


_cache_control = "max-age=0, no-cache, no-store, must-revalidate"


def test_api_route_never_cache(api_client):
    url = reverse("api-1-never-cache-route", url_args={"int_arg": 1})
    resp = check_api_get_responses(api_client, url, status_code=200)
    assert resp.data == {"result": 1}
    assert "Cache-Control" in resp
    assert resp["Cache-Control"].startswith(_cache_control)


def test_api_route_never_cache_with_error(api_client):
    url = reverse("api-1-never-cache-route-with-error")
    resp = check_api_get_responses(api_client, url, status_code=500)
    assert "Cache-Control" in resp
    assert resp["Cache-Control"].startswith(_cache_control)
