# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from email.headerregistry import Address
from email.message import EmailMessage

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
            recipient=Address(addr_spec="match@example.com"), extension=None,
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
