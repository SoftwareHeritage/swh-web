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
