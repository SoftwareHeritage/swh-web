# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import email
from email.headerregistry import Address
from email.message import EmailMessage
import email.policy
from importlib.resources import open_binary
from typing import List

import pytest

from swh.web.inbound_email import utils


def test_extract_recipients():
    message = EmailMessage()
    assert utils.extract_recipients(message) == []

    message["To"] = "Test Recipient <test-recipient@example.com>"

    assert utils.extract_recipients(message) == [
        Address(display_name="Test Recipient", addr_spec="test-recipient@example.com")
    ]

    message["Cc"] = (
        "test-recipient-2@example.com, "
        "Another Test Recipient <test-recipient-3@example.com>"
    )
    assert utils.extract_recipients(message) == [
        Address(display_name="Test Recipient", addr_spec="test-recipient@example.com"),
        Address(addr_spec="test-recipient-2@example.com"),
        Address(
            display_name="Another Test Recipient",
            addr_spec="test-recipient-3@example.com",
        ),
    ]

    del message["To"]
    assert utils.extract_recipients(message) == [
        Address(addr_spec="test-recipient-2@example.com"),
        Address(
            display_name="Another Test Recipient",
            addr_spec="test-recipient-3@example.com",
        ),
    ]


def test_single_recipient_matches():
    assert (
        utils.single_recipient_matches(
            Address(addr_spec="test@example.com"), "match@example.com"
        )
        is None
    )
    assert utils.single_recipient_matches(
        Address(addr_spec="match@example.com"), "match@example.com"
    ) == utils.AddressMatch(
        recipient=Address(addr_spec="match@example.com"), extension=None
    )
    assert utils.single_recipient_matches(
        Address(addr_spec="MaTch+12345AbC@exaMple.Com"), "match@example.com"
    ) == utils.AddressMatch(
        recipient=Address(addr_spec="MaTch+12345AbC@exaMple.Com"), extension="12345AbC"
    )


def test_recipient_matches():
    message = EmailMessage()
    assert utils.recipient_matches(message, "match@example.com") == []

    message = EmailMessage()
    message["to"] = "nomatch@example.com"
    assert utils.recipient_matches(message, "match@example.com") == []

    message = EmailMessage()
    message["to"] = "match@example.com"
    assert utils.recipient_matches(message, "match@example.com") == [
        utils.AddressMatch(
            recipient=Address(addr_spec="match@example.com"), extension=None
        )
    ]

    message = EmailMessage()
    message["to"] = "match+extension@example.com"
    assert utils.recipient_matches(message, "match@example.com") == [
        utils.AddressMatch(
            recipient=Address(addr_spec="match+extension@example.com"),
            extension="extension",
        )
    ]

    message = EmailMessage()
    message["to"] = "match+weird+plussed+extension@example.com"
    assert utils.recipient_matches(message, "match@example.com") == [
        utils.AddressMatch(
            recipient=Address(addr_spec="match+weird+plussed+extension@example.com"),
            extension="weird+plussed+extension",
        )
    ]

    message = EmailMessage()
    message["to"] = "nomatch@example.com"
    message["cc"] = ", ".join(
        (
            "match@example.com",
            "match@notamatch.example.com",
            "Another Match <match+extension@example.com>",
        )
    )
    assert utils.recipient_matches(message, "match@example.com") == [
        utils.AddressMatch(
            recipient=Address(addr_spec="match@example.com"),
            extension=None,
        ),
        utils.AddressMatch(
            recipient=Address(
                display_name="Another Match", addr_spec="match+extension@example.com"
            ),
            extension="extension",
        ),
    ]


def test_recipient_matches_casemapping():
    message = EmailMessage()
    message["to"] = "match@example.com"

    assert utils.recipient_matches(message, "Match@Example.Com")
    assert utils.recipient_matches(message, "match@example.com")

    message = EmailMessage()
    message["to"] = "Match+weirdCaseMapping@Example.Com"

    matches = utils.recipient_matches(message, "match@example.com")
    assert matches
    assert matches[0].extension == "weirdCaseMapping"


def test_get_address_for_pk():
    salt = "test_salt"
    pks = [1, 10, 1000]
    base_address = "base@example.com"

    addresses = {
        pk: utils.get_address_for_pk(salt=salt, base_address=base_address, pk=pk)
        for pk in pks
    }

    assert len(set(addresses.values())) == len(addresses)

    for pk, address in addresses.items():
        localpart, _, domain = address.partition("@")
        base_localpart, _, extension = localpart.partition("+")
        assert domain == "example.com"
        assert base_localpart == "base"
        assert extension.startswith(f"{pk}.")


def test_get_address_for_pk_salt():
    pk = 1000
    base_address = "base@example.com"
    addresses = [
        utils.get_address_for_pk(salt=salt, base_address=base_address, pk=pk)
        for salt in ["salt1", "salt2"]
    ]

    assert len(addresses) == len(set(addresses))


def test_get_pks_from_message():
    salt = "test_salt"
    pks = [1, 10, 1000]
    base_address = "base@example.com"

    addresses = {
        pk: utils.get_address_for_pk(salt=salt, base_address=base_address, pk=pk)
        for pk in pks
    }

    message = EmailMessage()
    message["To"] = "test@example.com"

    assert utils.get_pks_from_message(salt, base_address, message) == set()

    message = EmailMessage()
    message["To"] = f"Test Address <{addresses[1]}>"

    assert utils.get_pks_from_message(salt, base_address, message) == {1}

    message = EmailMessage()
    message["To"] = f"Test Address <{addresses[1]}>"
    message["Cc"] = ", ".join(
        [
            f"Test Address <{addresses[1]}>",
            f"Another Test Address <{addresses[10].lower()}>",
            "A Third Address <irrelevant@example.com>",
        ]
    )

    assert utils.get_pks_from_message(salt, base_address, message) == {1, 10}


def test_get_pks_from_message_logging(caplog):
    salt = "test_salt"
    pks = [1, 10, 1000]
    base_address = "base@example.com"

    addresses = {
        pk: utils.get_address_for_pk(salt=salt, base_address=base_address, pk=pk)
        for pk in pks
    }

    message = EmailMessage()
    message["To"] = f"Test Address <{base_address}>"

    assert utils.get_pks_from_message(salt, base_address, message) == set()

    relevant_records = [
        record
        for record in caplog.records
        if record.name == "swh.web.inbound_email.utils"
    ]
    assert len(relevant_records) == 1
    assert relevant_records[0].levelname == "DEBUG"
    assert (
        f"{base_address} cannot be matched to a request"
        in relevant_records[0].getMessage()
    )

    # Replace the signature with "mangle{signature}"
    mangled_address = addresses[1].replace(".", ".mangle", 1)

    message = EmailMessage()
    message["To"] = f"Test Address <{mangled_address}>"

    assert utils.get_pks_from_message(salt, base_address, message) == set()

    relevant_records = [
        record
        for record in caplog.records
        if record.name == "swh.web.inbound_email.utils"
    ]
    assert len(relevant_records) == 2
    assert relevant_records[0].levelname == "DEBUG"
    assert relevant_records[1].levelname == "DEBUG"

    assert f"{mangled_address} failed" in relevant_records[1].getMessage()


@pytest.mark.parametrize(
    "filename,expected_parts,expected_absent",
    (
        pytest.param(
            "plaintext.eml",
            [b"Plain text email.\n\n-- \nTest User"],
            [],
            id="plaintext",
        ),
        pytest.param(
            "multipart_alternative.eml",
            [b"*Multipart email.*\n\n-- \nTest User"],
            [],
            id="multipart_alternative",
        ),
        pytest.param(
            "multipart_alternative_html_only.eml",
            [b"<html>", b"<b>Multipart email (a much longer html part).</b>"],
            [b"<b>Multipart email (short html part)</b>"],
            id="multipart_alternative_html_only",
        ),
        pytest.param(
            "multipart_alternative_text_only.eml",
            [b"*Multipart email, but a longer text part.*\n\n--\nTest User"],
            [],
            id="multipart_alternative_text_only",
        ),
        pytest.param(
            "multipart_mixed.eml",
            [b"This is plain text", b"and <b>this is HTML</b>"],
            [b"This is a multi-part message in MIME format."],
            id="multipart_mixed",
        ),
        pytest.param(
            "multipart_mixed2.eml",
            [b"This is plain text", b"and this is more text"],
            [b"This is a multi-part message in MIME format."],
            id="multipart_mixed2",
        ),
        pytest.param(
            "multipart_mixed_text_only.eml",
            [b"My test email"],
            [
                b"HTML attachment",
                b"text attachment",
                b"This is a multi-part message in MIME format.",
            ],
            id="multipart_mixed_text_only",
        ),
        pytest.param(
            "multipart_alternative_recursive.eml",
            [b"This is plain text", b"and more plain text"],
            [b"this is HTML", b"This is a multi-part message in MIME format."],
            id="multipart_alternative_recursive",
        ),
        pytest.param(
            "multipart_related.eml",
            [
                b"See the message below\n\n---------- Forwarded message ---------",
                b"Hello everyone,\n\nSee my attachment",
            ],
            [b"this is HTML", b"This is a multi-part message in MIME format."],
            id="multipart_alternative_recursive",
        ),
    ),
)
def test_get_message_plaintext(
    filename: str, expected_parts: List[bytes], expected_absent: List[bytes]
):
    with open_binary("swh.web.inbound_email.tests.resources", filename) as f:
        message = email.message_from_binary_file(f, policy=email.policy.default)

    assert isinstance(message, EmailMessage)

    plaintext = utils.get_message_plaintext(message)
    assert plaintext is not None

    if len(expected_parts) == 1:
        assert plaintext == expected_parts[0]
    else:
        for part in expected_parts:
            assert part in plaintext
        for part in expected_absent:
            assert part not in plaintext
