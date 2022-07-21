# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from enum import Enum, auto

import django.dispatch

email_received = django.dispatch.Signal()
"""This signal is sent by the `process_inbound_email` management command.

Arguments:
  message (:class:`email.message.EmailMessage`): the inbound email message

Signal receivers must return an :class:`EmailProcessingStatus` value so that the
management command knows if the email has been processed.

Signal receivers will be called for all received emails and are expected to do their own
filtering (e.g. using the original destination address).

Receivers ignoring a message must return `EmailProcessingStatus.IGNORED` to let the
management command know that the message hasn't been processed.

"""


class EmailProcessingStatus(Enum):
    """Return values for the email processing signal listeners"""

    PROCESSED = auto()
    """The email has been successfully processed"""
    FAILED = auto()
    """The email has been processed, but the processing failed"""
    IGNORED = auto()
    """The email has been ignored (e.g. unknown recipient)"""
