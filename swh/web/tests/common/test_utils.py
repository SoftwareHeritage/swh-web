# Copyright (C) 2017-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information
from base64 import b64encode
import datetime
import math
from os.path import join
import sys
from urllib.parse import quote

import pytest

from django.conf.urls import url
from django.test.utils import override_settings
from django.urls.exceptions import NoReverseMatch

from swh.web.common import utils
from swh.web.common.exc import BadInputExc
from swh.web.config import SWH_WEB_SERVER_NAME, SWH_WEB_STAGING_SERVER_NAMES, get_config


def test_shorten_path_noop():
    noops = ["/api/", "/browse/", "/content/symbol/foobar/"]

    for noop in noops:
        assert utils.shorten_path(noop) == noop


def test_shorten_path_sha1():
    sha1 = "aafb16d69fd30ff58afdd69036a26047f3aebdc6"
    short_sha1 = sha1[:8] + "..."

    templates = [
        "/api/1/content/sha1:%s/",
        "/api/1/content/sha1_git:%s/",
        "/api/1/directory/%s/",
        "/api/1/content/sha1:%s/ctags/",
    ]

    for template in templates:
        assert utils.shorten_path(template % sha1) == template % short_sha1


def test_shorten_path_sha256():
    sha256 = "aafb16d69fd30ff58afdd69036a26047" "213add102934013a014dfca031c41aef"
    short_sha256 = sha256[:8] + "..."

    templates = [
        "/api/1/content/sha256:%s/",
        "/api/1/directory/%s/",
        "/api/1/content/sha256:%s/filetype/",
    ]

    for template in templates:
        assert utils.shorten_path(template % sha256) == template % short_sha256


@pytest.mark.parametrize(
    "input_timestamp, output_date",
    [
        (
            "2016-01-12",
            datetime.datetime(2016, 1, 12, 0, 0, tzinfo=datetime.timezone.utc),
        ),
        (
            "2016-01-12T09:19:12+0100",
            datetime.datetime(2016, 1, 12, 8, 19, 12, tzinfo=datetime.timezone.utc),
        ),
        (
            "2007-01-14T20:34:22Z",
            datetime.datetime(2007, 1, 14, 20, 34, 22, tzinfo=datetime.timezone.utc),
        ),
    ],
)
def test_parse_iso8601_date_to_utc_ok(input_timestamp, output_date):
    assert utils.parse_iso8601_date_to_utc(input_timestamp) == output_date


@pytest.mark.parametrize(
    "invalid_iso8601_timestamp", ["Today is January 1, 2047 at 8:21:00AM", "1452591542"]
)
def test_parse_iso8601_date_to_utc_ko(invalid_iso8601_timestamp):
    with pytest.raises(BadInputExc):
        utils.parse_iso8601_date_to_utc(invalid_iso8601_timestamp)


def test_format_utc_iso_date():
    assert (
        utils.format_utc_iso_date("2017-05-04T13:27:13+02:00")
        == "04 May 2017, 11:27 UTC"
    )


def test_gen_path_info():
    input_path = "/home/user/swh-environment/swh-web/"
    expected_result = [
        {"name": "home", "path": "home"},
        {"name": "user", "path": "home/user"},
        {"name": "swh-environment", "path": "home/user/swh-environment"},
        {"name": "swh-web", "path": "home/user/swh-environment/swh-web"},
    ]
    path_info = utils.gen_path_info(input_path)
    assert path_info == expected_result

    input_path = "home/user/swh-environment/swh-web"
    path_info = utils.gen_path_info(input_path)
    assert path_info == expected_result


def test_rst_to_html():
    rst = (
        "Section\n"
        "=======\n\n"
        "**Some strong text**\n\n"
        "* This is a bulleted list.\n"
        "* It has two items, the second\n"
        "  item uses two lines.\n"
        "\n"
        "1. This is a numbered list.\n"
        "2. It has two items too.\n"
        "\n"
        "#. This is a numbered list.\n"
        "#. It has two items too.\n"
    )

    expected_html = (
        '<div class="swh-rst"><h1 class="title">Section</h1>\n'
        "<p><strong>Some strong text</strong></p>\n"
        '<ul class="simple">\n'
        "<li><p>This is a bulleted list.</p></li>\n"
        "<li><p>It has two items, the second\n"
        "item uses two lines.</p></li>\n"
        "</ul>\n"
        '<ol class="arabic simple">\n'
        "<li><p>This is a numbered list.</p></li>\n"
        "<li><p>It has two items too.</p></li>\n"
        "<li><p>This is a numbered list.</p></li>\n"
        "<li><p>It has two items too.</p></li>\n"
        "</ol>\n"
        "</div>"
    )

    assert utils.rst_to_html(rst) == expected_html


def sample_test_view(request, string, number):
    pass


def sample_test_view_no_url_args(request):
    pass


urlpatterns = [
    url(
        r"^sample/test/(?P<string>.+)/view/(?P<number>[0-9]+)/$",
        sample_test_view,
        name="sample-test-view",
    ),
    url(
        r"^sample/test/view/no/url/args/$",
        sample_test_view_no_url_args,
        name="sample-test-view-no-url-args",
    ),
]


@override_settings(ROOT_URLCONF=__name__)
def test_reverse_url_args_only_ok():
    string = "foo"
    number = 55
    url = utils.reverse(
        "sample-test-view", url_args={"string": string, "number": number}
    )
    assert url == f"/sample/test/{string}/view/{number}/"


@override_settings(ROOT_URLCONF=__name__)
def test_reverse_url_args_only_ko():
    string = "foo"
    with pytest.raises(NoReverseMatch):
        utils.reverse("sample-test-view", url_args={"string": string, "number": string})


@override_settings(ROOT_URLCONF=__name__)
def test_reverse_no_url_args():
    url = utils.reverse("sample-test-view-no-url-args")
    assert url == "/sample/test/view/no/url/args/"


@override_settings(ROOT_URLCONF=__name__)
def test_reverse_query_params_only():
    start = 0
    scope = "foo"
    url = utils.reverse(
        "sample-test-view-no-url-args", query_params={"start": start, "scope": scope}
    )
    assert url == f"/sample/test/view/no/url/args/?scope={scope}&start={start}"

    url = utils.reverse(
        "sample-test-view-no-url-args", query_params={"start": start, "scope": None}
    )
    assert url == f"/sample/test/view/no/url/args/?start={start}"


@override_settings(ROOT_URLCONF=__name__)
def test_reverse_query_params_encode():
    libname = "libstc++"
    url = utils.reverse(
        "sample-test-view-no-url-args", query_params={"libname": libname}
    )
    assert url == f"/sample/test/view/no/url/args/?libname={quote(libname, safe='/;:')}"


@override_settings(ROOT_URLCONF=__name__)
def test_reverse_url_args_query_params():
    string = "foo"
    number = 55
    start = 10
    scope = "bar"
    url = utils.reverse(
        "sample-test-view",
        url_args={"string": string, "number": number},
        query_params={"start": start, "scope": scope},
    )
    assert url == f"/sample/test/{string}/view/{number}/?scope={scope}&start={start}"


@override_settings(ROOT_URLCONF=__name__)
def test_reverse_absolute_uri(request_factory):
    request = request_factory.get(utils.reverse("sample-test-view-no-url-args"))
    url = utils.reverse("sample-test-view-no-url-args", request=request)
    assert url == f"http://{request.META['SERVER_NAME']}/sample/test/view/no/url/args/"


def test_get_deposits_list(requests_mock):
    deposits_data = {
        "count": 2,
        "results": [
            {
                "check_task_id": "351820217",
                "client": 2,
                "collection": 1,
                "complete_date": "2021-01-21T07:52:19.919312Z",
                "external_id": "hal-03116143",
                "id": 1412,
                "load_task_id": "351820260",
                "origin_url": "https://hal.archives-ouvertes.fr/hal-03116143",
                "parent": None,
                "reception_date": "2021-01-21T07:52:19.471019Z",
                "status": "done",
                "status_detail": None,
                "swhid": "swh:1:dir:f25157ad1b13cb20ac3457d4f6756b49ac63d079",
            },
            {
                "check_task_id": "381576507",
                "client": 2,
                "collection": 1,
                "complete_date": "2021-07-07T08:00:44.726676Z",
                "external_id": "hal-03275052",
                "id": 1693,
                "load_task_id": "381576508",
                "origin_url": "https://hal.archives-ouvertes.fr/hal-03275052",
                "parent": None,
                "reception_date": "2021-07-07T08:00:44.327661Z",
                "status": "done",
                "status_detail": None,
                "swhid": "swh:1:dir:825fa96d1810177ec08a772ffa5bd34bbd08b89c",
            },
        ],
    }

    config = get_config()["deposit"]
    deposits_list_url = config["private_api_url"] + "deposits"

    basic_auth_payload = (
        config["private_api_user"] + ":" + config["private_api_password"]
    ).encode()

    requests_mock.get(
        deposits_list_url,
        json=deposits_data,
        request_headers={
            "Authorization": f"Basic {b64encode(basic_auth_payload).decode('ascii')}"
        },
    )

    assert utils.get_deposits_list() == deposits_data["results"]


@pytest.mark.parametrize("backend", ["swh-search", "swh-storage"])
def test_origin_visit_types(mocker, backend):
    if backend != "swh-search":
        # equivalent to not configuring search in the config
        search = mocker.patch("swh.web.common.utils.search")
        search.return_value = None
        assert utils.origin_visit_types() == []
    else:
        # see swh/web/tests/data.py for origins added for tests
        assert utils.origin_visit_types() == ["git", "tar"]


@pytest.mark.parametrize("server_name", ["localhost", "127.0.0.1", "testserver"])
def test_is_swh_web_development(request_factory, server_name):
    request = request_factory.get("/", SERVER_NAME=server_name)
    assert utils.is_swh_web_development(request)


@pytest.mark.parametrize("server_name", SWH_WEB_STAGING_SERVER_NAMES)
def test_is_swh_web_staging(request_factory, server_name):
    request = request_factory.get("/", SERVER_NAME=server_name)
    assert utils.is_swh_web_staging(request)


def test_is_swh_web_production(request_factory):
    request = request_factory.get("/", SERVER_NAME=SWH_WEB_SERVER_NAME)
    assert utils.is_swh_web_production(request)


@pytest.mark.parametrize(
    "raw_metadata_file,expected_url",
    [
        ("raw-metadata-provenance.xml", "https://example.org/metadata/provenance"),
        ("raw-metadata-no-swh.xml", None),
    ],
)
def test_parse_swh_provenance(datadir, raw_metadata_file, expected_url):
    metadata_path = join(datadir, "deposit", raw_metadata_file)
    with open(metadata_path, "r") as f:
        raw_metadata = f.read()

    actual_url = utils.parse_swh_metadata_provenance(raw_metadata)

    assert actual_url == expected_url


@pytest.mark.parametrize(
    "raw_metadata_file,expected_url",
    [
        (
            "raw-metadata-create-origin.xml",
            "https://example.org/metadata/create-origin",
        ),
        (
            "raw-metadata-add-to-origin.xml",
            "https://example.org/metadata/add-to-origin",
        ),
        ("raw-metadata-no-swh.xml", None),
    ],
)
def test_parse_swh_origins(datadir, raw_metadata_file, expected_url):
    metadata_path = join(datadir, "deposit", raw_metadata_file)
    with open(metadata_path, "r") as f:
        raw_metadata = f.read()

    actual_url = utils.parse_swh_deposit_origin(raw_metadata)

    assert actual_url == expected_url


def add(x, y):
    return x + y


def test_django_cache(mocker):
    """Decorated function should be called once and returned value
    put in django cache."""
    spy_add = mocker.spy(sys.modules[__name__], "add")
    spy_cache_set = mocker.spy(utils.cache, "set")

    cached_add = utils.django_cache()(add)

    val = cached_add(1, 2)
    val2 = cached_add(1, 2)

    assert val == val2 == 3
    assert spy_add.call_count == 1
    assert spy_cache_set.call_count == 1


def test_django_cache_invalidate_cache_pred(mocker):
    """Decorated function should be called twice and returned value
    put in django cache twice."""
    spy_add = mocker.spy(sys.modules[__name__], "add")
    spy_cache_set = mocker.spy(utils.cache, "set")

    cached_add = utils.django_cache(invalidate_cache_pred=lambda val: val == 3)(add)

    val = cached_add(1, 2)
    val2 = cached_add(1, 2)

    assert val == val2 == 3
    assert spy_add.call_count == 2
    assert spy_cache_set.call_count == 2


def test_django_cache_raise_exception(mocker):
    """Decorated function should be called twice, exceptions should be
    raised and no value put in django cache"""
    spy_add = mocker.spy(sys.modules[__name__], "add")
    spy_cache_set = mocker.spy(utils.cache, "set")

    cached_add = utils.django_cache()(add)

    with pytest.raises(TypeError):
        cached_add(1, "2")

    with pytest.raises(TypeError):
        cached_add(1, "2")

    assert spy_add.call_count == 2
    assert spy_cache_set.call_count == 0


def test_django_cache_catch_exception(mocker):
    """Decorated function should be called twice, exceptions should not be
    raised, specified fallback value should be returned and no value put
    in django cache"""
    spy_add = mocker.spy(sys.modules[__name__], "add")
    spy_cache_set = mocker.spy(utils.cache, "set")

    cached_add = utils.django_cache(
        catch_exception=True, exception_return_value=math.nan
    )(add)

    val = cached_add(1, "2")
    val2 = cached_add(1, "2")

    assert math.isnan(val)
    assert math.isnan(val2)
    assert spy_add.call_count == 2
    assert spy_cache_set.call_count == 0
