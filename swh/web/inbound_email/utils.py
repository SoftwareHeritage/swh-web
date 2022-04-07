# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from dataclasses import dataclass
from email.headerregistry import Address
from email.message import EmailMessage
import logging
from typing import List, Optional, Set

from django.core.signing import Signer
from django.utils.crypto import constant_time_compare

logger = logging.getLogger(__name__)


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


ADDRESS_SIGNER_SEP = "."
"""Separator for email address signatures"""


def get_address_signer(salt: str) -> Signer:
    """Get a signer for the given seed"""
    return Signer(salt=salt, sep=ADDRESS_SIGNER_SEP)


def get_address_for_pk(salt: str, base_address: str, pk: int) -> str:
    """Get the email address that will be able to receive messages to be logged in
    this request."""
    if "@" not in base_address:
        raise ValueError("Base address needs to contain an @")

    username, domain = base_address.split("@")

    extension = get_address_signer(salt).sign(str(pk))

    return f"{username}+{extension}@{domain}"


def get_pk_from_extension(salt: str, extension: str) -> int:
    """Retrieve the primary key for the given inbound address extension.

    We reimplement `Signer.unsign`, because the extension can be casemapped at any
    point in the email chain (even though email is, theoretically, case sensitive),
    so we have to compare lowercase versions of both the extension and the
    signature...

    Raises ValueError if the signature couldn't be verified.

    """

    value, signature = extension.rsplit(ADDRESS_SIGNER_SEP, 1)
    expected_signature = get_address_signer(salt).signature(value)
    if not constant_time_compare(signature.lower(), expected_signature.lower()):
        raise ValueError(f"Invalid signature for extension {extension}")

    return int(value)


def get_pks_from_message(
    salt: str, base_address: str, message: EmailMessage
) -> Set[int]:
    """Retrieve the set of primary keys that were successfully decoded from the
    recipients of the ``message`` matching ``base_address``.

    This uses :func:`recipient_matches` to retrieve all the recipient addresses matching
    ``base_address``, then :func:`get_pk_from_extension` to decode the primary key and
    verify the signature for every extension. To generate relevant email addresses, use
    :func:`get_address_for_pk` with the same ``base_address`` and ``salt``.

    Returns:
      the set of primary keys that were successfully decoded from the recipients of the
      ``message``

    """
    ret: Set[int] = set()

    for match in recipient_matches(message, base_address):
        extension = match.extension
        if extension is None:
            logger.debug(
                "Recipient address %s cannot be matched to a request, ignoring",
                match.recipient.addr_spec,
            )
            continue

        try:
            ret.add(get_pk_from_extension(salt, extension))
        except ValueError:
            logger.debug(
                "Recipient address %s failed validation", match.recipient.addr_spec
            )
            continue

    return ret


def get_message_plaintext(message: EmailMessage) -> Optional[bytes]:
    """Get the plaintext body for a given message, if any such part exists. If only a html
    part exists, return that instead.

    If there are multiple, ambiguous plain text or html parts in the message, this
    function will return the largest of them.

    """
    if not message.is_multipart():
        single_part = message.get_payload(decode=True).rstrip(b"\n")
        return single_part or None

    text_parts: List[bytes] = []
    fallback_parts: List[bytes] = []

    for part in message.walk():
        content_type = part.get_content_type()
        content_disposition = str(part.get("Content-Disposition"))
        if "attachment" in content_disposition:
            continue
        if content_type == "text/plain":
            current_part = part.get_payload(decode=True).rstrip(b"\n")
            if current_part:
                text_parts.append(current_part)
        elif not text_parts and content_type == "text/html":
            current_part = part.get_payload(decode=True).rstrip(b"\n")
            if current_part:
                fallback_parts.append(current_part)

    if text_parts:
        return max(text_parts, key=len)

    if fallback_parts:
        return max(fallback_parts, key=len)

    return None
