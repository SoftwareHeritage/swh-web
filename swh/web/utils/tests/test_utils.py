# Copyright (C) 2017-2025  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import datetime
import math
import sys
from urllib.parse import quote

import attr
import docutils
import pytest

from django.test.utils import override_settings
from django.urls import re_path as url
from django.urls.exceptions import NoReverseMatch

from swh.web.utils import (
    cache,
    django_cache,
    format_utc_iso_date,
    gen_path_info,
    origin_visit_types,
    parse_iso8601_date_to_utc,
    reverse,
    rst_to_html,
    shorten_path,
    strtobool,
)
from swh.web.utils.exc import BadInputExc


def test_shorten_path_noop():
    noops = ["/api/", "/browse/", "/content/symbol/foobar/"]

    for noop in noops:
        assert shorten_path(noop) == noop


def test_shorten_path_sha1():
    sha1 = "aafb16d69fd30ff58afdd69036a26047f3aebdc6"
    short_sha1 = sha1[:8] + "..."

    templates = [
        "/api/1/content/sha1:%s/",
        "/api/1/content/sha1_git:%s/",
        "/api/1/directory/%s/",
    ]

    for template in templates:
        assert shorten_path(template % sha1) == template % short_sha1


def test_shorten_path_sha256():
    sha256 = "aafb16d69fd30ff58afdd69036a26047" "213add102934013a014dfca031c41aef"
    short_sha256 = sha256[:8] + "..."

    templates = [
        "/api/1/content/sha256:%s/",
        "/api/1/directory/%s/",
        "/api/1/content/sha256:%s/filetype/",
    ]

    for template in templates:
        assert shorten_path(template % sha256) == template % short_sha256


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
    assert parse_iso8601_date_to_utc(input_timestamp) == output_date


@pytest.mark.parametrize(
    "invalid_iso8601_timestamp", ["Today is January 1, 2047 at 8:21:00AM", "1452591542"]
)
def test_parse_iso8601_date_to_utc_ko(invalid_iso8601_timestamp):
    with pytest.raises(BadInputExc):
        parse_iso8601_date_to_utc(invalid_iso8601_timestamp)


def test_format_utc_iso_date():
    assert (
        format_utc_iso_date("2017-05-04T13:27:13+02:00") == "04 May 2017, 11:27:13 UTC"
    )


def test_gen_path_info():
    input_path = "/home/user/swh-environment/swh-web/"
    expected_result = [
        {"name": "home", "path": "home"},
        {"name": "user", "path": "home/user"},
        {"name": "swh-environment", "path": "home/user/swh-environment"},
        {"name": "swh-web", "path": "home/user/swh-environment/swh-web"},
    ]
    path_info = gen_path_info(input_path)
    assert path_info == expected_result

    input_path = "home/user/swh-environment/swh-web"
    path_info = gen_path_info(input_path)
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

    if docutils.__version_info__ >= (0, 17):
        expected_html = (
            '<div class="swh-rst"><main id="section">\n'
            '<h1 class="title">Section</h1>\n'
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
            "</main>\n"
            "</div>"
        )
    else:
        expected_html = (
            '<div class="swh-rst"><div class="document" id="section">\n'
            '<h1 class="title">Section</h1>\n'
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
            "</div>\n"
            "</div>"
        )

    assert rst_to_html(rst) == expected_html


def test_rst_to_html_topic_processing():
    rst = (
        ".. contents::\n\n"
        "Section\n"
        "=======\n\n"
        "Sub-section\n"
        "-----------\n\n"
        "* This is a bulleted list.\n"
    )

    expected_html = (
        '<div class="swh-rst"><div class="document">\n'
        '<div class="contents topic" id="contents">\n'
        '<p class="topic-title first">Contents</p>\n'
        '<ul class="simple">\n'
        '<li><p><a class="reference internal" href="#section" id="id1">Section</a></p>\n'
        "<ul>\n"
        '<li><p><a class="reference internal" href="#sub-section" id="id2">'
        "Sub-section</a></p></li>\n"
        "</ul>\n"
        "</li>\n"
        "</ul>\n"
        "</div>\n"
        '<div class="section" id="section">\n'
        '<h2><a class="toc-backref" href="#id1">Section</a></h2>\n'
        '<div class="section" id="sub-section">\n'
        '<h3><a class="toc-backref" href="#id2">Sub-section</a></h3>\n'
        '<ul class="simple">\n'
        "<li><p>This is a bulleted list.</p></li>\n"
        "</ul>\n"
        "</div>\n"
        "</div>\n"
        "</div>\n"
        "</div>"
    )

    if docutils.__version_info__ >= (0, 17):
        expected_html = (
            '<div class="swh-rst"><main>\n'
            '<div class="contents topic" id="contents">\n'
            '<p class="topic-title">Contents</p>\n'
            '<ul class="simple">\n'
            '<li><p><a class="reference internal" href="#section" id="id1">Section</a></p>\n'
            "<ul>\n"
            '<li><p><a class="reference internal" href="#sub-section" id="id2">'
            "Sub-section</a></p></li>\n"
            "</ul>\n"
            "</li>\n"
            "</ul>\n"
            "</div>\n"
            '<section id="section">\n'
            '<h2><a class="toc-backref" href="#id1">Section</a></h2>\n'
            '<section id="sub-section">\n'
            '<h3><a class="toc-backref" href="#id2">Sub-section</a></h3>\n'
            '<ul class="simple">\n'
            "<li><p>This is a bulleted list.</p></li>\n"
            "</ul>\n"
            "</section>\n"
            "</section>\n"
            "</main>\n"
            "</div>"
        )

    if docutils.__version_info__ >= (0, 18):
        title = "Contents"
        if docutils.__version_info__ >= (0, 21):
            title = '<a class="reference internal" href="#top">Contents</a>'
        expected_html = (
            '<div class="swh-rst"><main>\n'
            '<nav class="contents" id="contents" role="doc-toc">\n'
            f'<p class="topic-title">{title}</p>\n'
            '<ul class="simple">\n'
            '<li><p><a class="reference internal" href="#section" id="toc-entry-1">'
            "Section</a></p>\n"
            "<ul>\n"
            '<li><p><a class="reference internal" href="#sub-section" id="toc-entry-2">'
            "Sub-section</a></p></li>\n"
            "</ul>\n"
            "</li>\n"
            "</ul>\n"
            "</nav>\n"
            '<section id="section">\n'
            '<h2><a class="toc-backref" href="#toc-entry-1" role="doc-backlink">'
            "Section</a></h2>\n"
            '<section id="sub-section">\n'
            '<h3><a class="toc-backref" href="#toc-entry-2" role="doc-backlink">'
            "Sub-section</a></h3>\n"
            '<ul class="simple">\n'
            "<li><p>This is a bulleted list.</p></li>\n"
            "</ul>\n"
            "</section>\n"
            "</section>\n"
            "</main>\n"
            "</div>"
        )

    assert rst_to_html(rst) == expected_html


def test_rst_to_html_error():
    rst = (
        "==========\n"
        "Section\n"
        "====\n\n"
        "**Some strong text**\n\n"
        "* This is a bulleted list.\n"
    )

    expected_html = f'<div class="swh-readme-txt"><pre>{rst}</pre></div>'

    assert rst_to_html(rst) == expected_html


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
    url = reverse("sample-test-view", url_args={"string": string, "number": number})
    assert url == f"/sample/test/{string}/view/{number}/"


@override_settings(ROOT_URLCONF=__name__)
def test_reverse_url_args_only_ko():
    string = "foo"
    with pytest.raises(NoReverseMatch):
        reverse("sample-test-view", url_args={"string": string, "number": string})


@override_settings(ROOT_URLCONF=__name__)
def test_reverse_no_url_args():
    url = reverse("sample-test-view-no-url-args")
    assert url == "/sample/test/view/no/url/args/"


@override_settings(ROOT_URLCONF=__name__)
def test_reverse_query_params_only():
    start = 0
    scope = "foo"
    url = reverse(
        "sample-test-view-no-url-args", query_params={"start": start, "scope": scope}
    )
    assert url == f"/sample/test/view/no/url/args/?scope={scope}&start={start}"

    url = reverse(
        "sample-test-view-no-url-args", query_params={"start": start, "scope": None}
    )
    assert url == f"/sample/test/view/no/url/args/?start={start}"


@override_settings(ROOT_URLCONF=__name__)
def test_reverse_query_params_encode():
    libname = "libstdc++"
    url = reverse("sample-test-view-no-url-args", query_params={"libname": libname})
    assert url == f"/sample/test/view/no/url/args/?libname={quote(libname, safe='/;:')}"


@override_settings(ROOT_URLCONF=__name__)
def test_reverse_url_args_query_params():
    string = "foo"
    number = 55
    start = 10
    scope = "bar"
    url = reverse(
        "sample-test-view",
        url_args={"string": string, "number": number},
        query_params={"start": start, "scope": scope},
    )
    assert url == f"/sample/test/{string}/view/{number}/?scope={scope}&start={start}"


@override_settings(ROOT_URLCONF=__name__)
def test_reverse_absolute_uri(request_factory):
    request = request_factory.get(reverse("sample-test-view-no-url-args"))
    url = reverse("sample-test-view-no-url-args", request=request)
    assert url == f"http://{request.META['SERVER_NAME']}/sample/test/view/no/url/args/"


@pytest.mark.parametrize("backend", ["swh-search", "swh-storage"])
def test_origin_visit_types(mocker, backend):
    if backend != "swh-search":
        # equivalent to not configuring search in the config
        search = mocker.patch("swh.web.utils.search")
        search.return_value = None
        assert origin_visit_types() == []
    else:
        # see swh/web/tests/data.py for origins added for tests
        assert origin_visit_types() == ["git", "git-checkout", "hg", "tar"]


def add(x, y):
    return x + y


def test_django_cache(mocker):
    """Decorated function should be called once and returned value
    put in django cache."""
    spy_add = mocker.spy(sys.modules[__name__], "add")
    spy_cache_set = mocker.spy(cache, "set")

    cached_add = django_cache()(add)

    val = cached_add(1, 2)
    val2 = cached_add(1, 2)

    assert val == val2 == 3
    assert spy_add.call_count == 1
    assert spy_cache_set.call_count == 1


def test_django_cache_invalidate_cache_pred(mocker):
    """Decorated function should be called twice and returned value
    put in django cache twice."""
    spy_add = mocker.spy(sys.modules[__name__], "add")
    spy_cache_set = mocker.spy(cache, "set")

    cached_add = django_cache(invalidate_cache_pred=lambda val: val == 3)(add)

    val = cached_add(1, 2)
    val2 = cached_add(1, 2)

    assert val == val2 == 3
    assert spy_add.call_count == 2
    assert spy_cache_set.call_count == 2


def test_django_cache_raise_exception(mocker):
    """Decorated function should be called twice, exceptions should be
    raised and no value put in django cache"""
    spy_add = mocker.spy(sys.modules[__name__], "add")
    spy_cache_set = mocker.spy(cache, "set")

    cached_add = django_cache()(add)

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
    spy_cache_set = mocker.spy(cache, "set")

    cached_add = django_cache(catch_exception=True, exception_return_value=math.nan)(
        add
    )

    val = cached_add(1, "2")
    val2 = cached_add(1, "2")

    assert math.isnan(val)
    assert math.isnan(val2)
    assert spy_add.call_count == 2
    assert spy_cache_set.call_count == 0


@attr.s
class AddResult:
    val = attr.ib(type=int)


def add_result(x: int, y: int) -> AddResult:
    return AddResult(val=x + y)


def test_django_cache_with_extra_encoder_and_decoder(mocker):
    """Decorated function should be called once and returned value
    put in django cache."""
    spy_add = mocker.spy(sys.modules[__name__], "add_result")
    spy_cache_set = mocker.spy(cache, "set")

    cached_add = django_cache(
        extra_encoders=[(AddResult, "add_result", attr.asdict)],
        extra_decoders={"add_result": lambda d: AddResult(**d)},
    )(add_result)

    val = cached_add(1, 2)
    val2 = cached_add(1, 2)

    assert val == val2 == AddResult(val=3)
    assert spy_add.call_count == 1
    assert spy_cache_set.call_count == 1


def test_django_cache_set_pass_through_on_errors(mocker):
    spy_cache_get = mocker.spy(cache, "get")
    mocker.patch.object(cache, "set").side_effect = Exception("Cache error")
    cached_add = django_cache()(add)

    # function still returns a value
    assert cached_add(1, 1) == 2

    # but it should not be in cache
    cache_key = spy_cache_get.mock_calls[0].args[0]
    assert cache.get(cache_key) is None


def test_django_cache_get_pass_through_on_errors(mocker):
    spy_cache_set = mocker.spy(cache, "set")
    cached_add = django_cache()(add)

    # first call works and has been cached
    assert cached_add(1, 1) == 2
    assert len(spy_cache_set.mock_calls) == 1
    # second call will raise a caching exception while getting the key
    # but function still returns a value
    mocker.patch.object(cache, "get").side_effect = Exception("Cache error")
    assert cached_add(1, 1) == 2


@pytest.mark.parametrize("value", ["y", "YES", "t", "True", "on", "1"])
def test_strtobool_true(value):
    assert strtobool(value)


@pytest.mark.parametrize("value", ["N", "no", "f", "False", "off", "0"])
def test_strtobool_false(value):
    assert not strtobool(value)


def test_strtobool_exc():
    with pytest.raises(BadInputExc, match="Invalid truth value vrai"):
        strtobool("vrai")
