# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from dataclasses import dataclass
from email.headerregistry import Address, AddressHeader
from email.message import EmailMessage, Message
import logging
from typing import List, Optional, Set, Tuple, Union, cast

from django.conf import settings
from django.core.signing import Signer
from django.utils.crypto import constant_time_compare

logger = logging.getLogger(__name__)

# Cribbed from the procmail TO_ macro:
#
# #define TO_substitute "(^((Original-)?(Resent-)?(To|Cc|Bcc)|\
#   (X-Envelope|Apparently(-Resent)?)-To):(.*[^-a-zA-Z0-9_.])?)"

HEADERS = (
    "to",
    "cc",
    "bcc",
    "original-to",
    "original-cc",
    "original-bcc",
    "resent-to",
    "resent-cc",
    "resent-bcc",
    "original-resent-to",
    "original-resent-cc",
    "original-resent-bcc",
    "x-envelope-to",
    "apparently-to",
    "apparently-resent-to",
)


def extract_recipients(message: EmailMessage) -> List[Address]:
    """Extract a list of recipients of the `message`.

    This uses all the fields in :data:`HEADERS`
    """

    ret = []

    for header_name in HEADERS:
        for header in filter(
            lambda h: isinstance(h, AddressHeader), message.get_all(header_name, [])
        ):
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

ADDRESS_SIGNER_DEFAULT = "sha1"
"""Default algorithm for signed address creation"""

ADDRESS_SIGNER_SUPPORTED = (ADDRESS_SIGNER_DEFAULT, "sha256")
"""Supported algorithms for signed address validation"""


def get_address_signer(
    salt: str, algorithm: str = ADDRESS_SIGNER_DEFAULT, key: Optional[str] = None
) -> Signer:
    """Get an address signer for the given salt, algorithm and secret key."""
    if key is None:
        key = settings.SECRET_KEY
    return Signer(salt=salt, sep=ADDRESS_SIGNER_SEP, algorithm=algorithm, key=key)


def get_address_for_pk(
    salt: str,
    base_address: str,
    pk: int,
    algorithm: str = ADDRESS_SIGNER_DEFAULT,
    key: Optional[str] = None,
) -> str:
    """Get the email address that will be able to receive messages to be logged in
    this request."""
    if "@" not in base_address:
        raise ValueError("Base address needs to contain an @")

    username, domain = base_address.split("@")

    extension = get_address_signer(salt, algorithm=algorithm, key=key).sign(str(pk))

    return f"{username}+{extension}@{domain}"


def get_pk_from_extension(salt: str, extension: str) -> int:
    """Retrieve the primary key for the given inbound address extension.

    We reimplement `Signer.unsign`, because the extension can be casemapped at
    any point in the email chain (even though email is, theoretically, case
    sensitive), so we have to compare lowercase versions of both the extension
    and the signature... We also support addresses generated with multiple
    signature algorithms, to keep compatibility with older pre-Django 3.1
    deployments.

    Raises ValueError if the signature couldn't be verified.

    """

    value, signature = extension.rsplit(ADDRESS_SIGNER_SEP, 1)

    valid = False
    for algorithm in ADDRESS_SIGNER_SUPPORTED:
        for key in [settings.SECRET_KEY] + settings.SECRET_KEY_FALLBACKS:
            signer = get_address_signer(salt, algorithm=algorithm, key=key)
            expected_signature = signer.signature(value)
            if constant_time_compare(signature.lower(), expected_signature.lower()):
                valid = True

    if valid:
        return int(value)
    else:
        raise ValueError(f"Invalid signature for extension {extension}")


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


def _get_message_text(message: Union[Message, EmailMessage]) -> Tuple[bool, List[str]]:
    """Recursively parses a message, and returns ``(is_plain_text, parts)``."""

    # Ignore all attachments; only consider message body
    content_disposition = str(message.get("Content-Disposition"))
    if "attachment" in content_disposition:
        return (False, [])

    maintype = message.get_content_maintype()
    subtype = message.get_content_subtype()
    if maintype == "text":
        # This is a simple message (message part)
        # XXX email.message API says we are sure to get a bytes here, but mypy cannot tell
        current_part_bytes = cast(bytes, message.get_payload(decode=True)).rstrip(b"\n")
        # XXX same, we know we get a str, but mypy cannot tell, so make it happy
        charset = str(message.get_param("charset", "utf-8"))
        current_part = current_part_bytes.decode(charset, errors="replace")

        if subtype == "plain":
            if current_part:
                return (True, [current_part])
        elif subtype == "html":
            if current_part:
                return (False, [current_part])
        return (True, [])
    elif maintype == "multipart":
        # This message (message part) contains sub-parts.
        text_parts: List[str] = []
        fallback_parts: List[str] = []
        all_parts: List[str] = []

        # Parse each part independently:
        for part in message.get_payload():
            (is_plain_text, current_part_list) = _get_message_text(
                cast(Union[Message, EmailMessage], part)
            )
            if is_plain_text:
                text_parts.append("".join(current_part_list))
            else:
                fallback_parts.append("".join(current_part_list))
            all_parts.extend(current_part_list)

        if subtype == "alternative":
            # Return the largest plain text part if any; or the largest HTML otherwise
            if text_parts:
                return (True, [max(text_parts, key=len)])

            if fallback_parts:
                return (False, [max(fallback_parts, key=len)])
        else:
            # Handles multipart/mixed; but this should be an appropriate handling for
            # other multipart formats
            is_plain_text = len(fallback_parts) == 0
            return (is_plain_text, all_parts)

    return (False, [])


def get_message_plaintext(message: EmailMessage) -> Optional[str]:
    """Get the plaintext body for a given message, if any such part exists. If only a html
    part exists, return that instead.

    If there are multiple, ambiguous plain text or html parts in the message, this
    function will return the largest of them.

    """
    (is_plain_text, parts) = _get_message_text(message)
    return "".join(parts) or None
