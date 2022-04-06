# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from dataclasses import dataclass
from email.headerregistry import Address
from email.message import EmailMessage
from typing import List, Optional


def extract_recipients(message: EmailMessage) -> List[Address]:
    """Extract a list of recipients of the `message`.

    This uses the ``To`` and ``Cc`` fields.
    """

    ret = []

    for header_name in ("to", "cc"):
        for header in message.get_all(header_name, []):
            ret.extend(header.addresses)

    return ret


@dataclass
class AddressMatch:
    """Data related to a recipient match"""

    recipient: Address
    """The original recipient that matched the expected address"""
    extension: Optional[str]
    """The parsed +-extension of the matched recipient address"""


def single_recipient_matches(
    recipient: Address, address: str
) -> Optional[AddressMatch]:
    """Check whether a single address matches the provided base address.

    The match is case-insensitive, which is not really RFC-compliant but is consistent
    with what most people would expect.

    This function supports "+-addressing", where the local part of the email address is
    appended with a `+`.

    """
    parsed_address = Address(addr_spec=address.lower())

    if recipient.domain.lower() != parsed_address.domain:
        return None

    base_username, _, extension = recipient.username.partition("+")

    if base_username.lower() != parsed_address.username:
        return None

    return AddressMatch(recipient=recipient, extension=extension or None)


def recipient_matches(message: EmailMessage, address: str) -> List[AddressMatch]:
    """Check whether any of the message recipients match the given address.

    The match is case-insensitive, which is not really RFC-compliant but matches what
    most people would expect.

    This function supports "+-addressing", where the local part of the email address is
    appended with a `+`.

    """

    ret = []

    for recipient in extract_recipients(message):
        match = single_recipient_matches(recipient, address)
        if match:
            ret.append(match)

    return ret
