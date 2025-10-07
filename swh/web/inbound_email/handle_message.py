# Copyright (C) 2022-2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


import email
import email.message
import email.policy
import logging
from typing import Callable, Optional, Type

from swh.web.inbound_email import signals
from swh.web.utils.exc import sentry_capture_exception

logger = logging.getLogger(__name__)


class MessageHandler:
    def __init__(self, raw_message: bytes, sender: Optional[Type] = None):
        try:
            self.message = email.message_from_bytes(
                raw_message, policy=email.policy.default
            )
        except Exception as exc:
            sentry_capture_exception(exc)
            self.failed_message(raw_message)
            # XXX make sure having logging doesn't make postfix unhappy
            logger.exception("Could not convert email from bytes")
            return

        self.sender = sender or self.__class__

    def handle(self):
        responses = signals.email_received.send_robust(
            sender=self.sender, message=self.message
        )

        handled = False
        for receiver, response in responses:
            if isinstance(response, Exception):
                sentry_capture_exception(response)
                self.failing_receiver(receiver)
                logger.error(
                    "Receiver produced the following exception", exc_info=response
                )
            elif response is signals.EmailProcessingStatus.FAILED:
                self.failing_receiver(receiver)
            elif response is signals.EmailProcessingStatus.PROCESSED:
                handled = True

        if not handled:
            self.unhandled_message()

        return handled

    @classmethod
    def failed_message(cls, raw_message: bytes):
        # TODO: forward email as attachment for inspection
        logger.error("Failed message: %s", raw_message.decode("ascii", "replace"))

    def failing_receiver(self, receiver: Callable):
        # TODO: forward email for inspection
        logger.error(
            "Failed receiver %s:%s; message: %s",
            receiver.__module__,
            receiver.__qualname__,
            str(self.message),
        )

    def unhandled_message(self):
        # TODO: pass email through to a fallback alias?
        logger.error("Unhandled message: %s", str(self.message))
