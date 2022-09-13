# Copyright (C) 2017-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import re

import pytest

from swh.model.model import Content
from swh.web.browse.utils import (
    gen_link,
    gen_person_mail_link,
    gen_revision_link,
    get_mimetype_and_encoding_for_content,
    get_readme_to_display,
    prepare_content_for_display,
    re_encode_content,
)
from swh.web.tests.data import get_tests_data
from swh.web.utils import reverse


def test_get_mimetype_and_encoding_for_content():
    text = b"Hello world!"
    assert get_mimetype_and_encoding_for_content(text) == (
        "text/plain",
        "us-ascii",
    )


def test_gen_link():
    assert (
        gen_link("https://www.softwareheritage.org/", "swh")
        == '<a href="https://www.softwareheritage.org/">swh</a>'
    )


def test_gen_revision_link():
    revision_id = "28a0bc4120d38a394499382ba21d6965a67a3703"
    revision_url = reverse("browse-revision", url_args={"sha1_git": revision_id})

    assert gen_revision_link(
        revision_id, link_text=None, link_attrs=None
    ) == '<a href="%s">%s</a>' % (revision_url, revision_id)
    assert gen_revision_link(
        revision_id, shorten_id=True, link_attrs=None
    ) == '<a href="%s">%s</a>' % (revision_url, revision_id[:7])


def test_gen_person_mail_link():
    person_full = {
        "name": "John Doe",
        "email": "john.doe@swh.org",
        "fullname": "John Doe <john.doe@swh.org>",
    }

    assert gen_person_mail_link(person_full) == '<a href="mailto:%s">%s</a>' % (
        person_full["email"],
        person_full["name"],
    )

    link_text = "Mail"
    assert gen_person_mail_link(
        person_full, link_text=link_text
    ) == '<a href="mailto:%s">%s</a>' % (person_full["email"], link_text)

    person_partial_email = {"name": None, "email": None, "fullname": "john.doe@swh.org"}

    assert gen_person_mail_link(
        person_partial_email
    ) == '<a href="mailto:%s">%s</a>' % (
        person_partial_email["fullname"],
        person_partial_email["fullname"],
    )

    person_partial = {
        "name": None,
        "email": None,
        "fullname": "John Doe <john.doe@swh.org>",
    }

    assert gen_person_mail_link(person_partial) == person_partial["fullname"]

    person_none = {"name": None, "email": None, "fullname": None}

    assert gen_person_mail_link(person_none) == "None"


@pytest.mark.parametrize(
    "path, expected_language",
    [("CMakeLists.txt", "cmake"), ("path/CMakeLists.txt", "cmake")],
)
def test_prepare_content_display_language_for_filename(path, expected_language):
    content_display = prepare_content_for_display(
        content_data=b"", mime_type="", path=path
    )
    assert content_display["language"] == expected_language


def test_re_encode_content_for_shift_jis_encoding():
    data = b"/* \x8a\xd6\x98A\x82\xcc\x95\xb6\x8e\x9a\x83R\x81[\x83h\x95\xcf\x8a\xb7 */"
    mime_type, encoding = get_mimetype_and_encoding_for_content(data)

    _, encoding, re_encoded_data = re_encode_content(mime_type, encoding, data)

    assert encoding == "SHIFT_JIS"
    assert data.decode(encoding) == re_encoded_data.decode("utf-8")
    assert re_encoded_data.decode("utf-8") == "/* 関連の文字コード変換 */"


@pytest.mark.parametrize(
    "input_,expected_output",
    [
        (b"foo bar", "<p>foo bar</p>"),
        (b"foo *bar* baz", "<p>foo <em>bar</em> baz</p>"),
        (
            b".. raw:: html\n\n   <script>foo</script>",
            "&lt;script&gt;foo&lt;/script&gt;",
        ),
    ],
)
def test_rst_readme(input_, expected_output):
    content = Content.from_data(input_)
    storage = get_tests_data()["storage"]
    storage.content_add([content])
    assert re.search(
        expected_output, get_readme_to_display({"readme.rst": content.sha1.hex()})[2]
    )


def test_rst_readme_no_leak():
    input_ = b".. include:: /etc/passwd"
    content = Content.from_data(input_)
    storage = get_tests_data()["storage"]
    storage.content_add([content])
    assert "root:" not in get_readme_to_display({"readme.rst": content.sha1.hex()})[2]


def test_rst_readme_no_xss():
    input_ = b".. raw:: html\n\n   <script>foo</script>"
    content = Content.from_data(input_)
    storage = get_tests_data()["storage"]
    storage.content_add([content])
    assert (
        "<script>" not in get_readme_to_display({"readme.rst": content.sha1.hex()})[2]
    )
