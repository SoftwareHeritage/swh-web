# Copyright (C) 2017-2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import datetime

import pytest

from swh.web.common import utils
from swh.web.common.exc import BadInputExc


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
        "Subsection\n"
        "----------\n\n"
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
        '<div class="section" id="subsection">\n'
        "<h2>Subsection</h2>\n"
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

    assert utils.rst_to_html(rst) == expected_html
