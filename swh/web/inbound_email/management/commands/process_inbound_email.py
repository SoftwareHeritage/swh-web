# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import email
import email.message
import email.policy
import logging
import sys
from typing import Callable

from django.core.management.base import BaseCommand

from swh.web.inbound_email import signals
from swh.web.utils.exc import sentry_capture_exception

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Process a new inbound email"

    def handle(self, *args, **options):
        raw_message = sys.stdin.buffer.read()
        try:
            message = email.message_from_bytes(raw_message, policy=email.policy.default)
        except Exception as exc:
            sentry_capture_exception(exc)
            self.handle_failed_message(raw_message)
            # XXX make sure having logging doesn't make postfix unhappy
            logger.exception("Could not convert email from bytes")
            return

        responses = signals.email_received.send_robust(
            sender=self.__class__, message=message
        )

        handled = False
        for receiver, response in responses:
            if isinstance(response, Exception):
                sentry_capture_exception(response)
                self.handle_failing_receiver(message, receiver)
                logger.error(
                    "Receiver produced the following exception", exc_info=response
                )
            elif response is signals.EmailProcessingStatus.FAILED:
                self.handle_failing_receiver(message, receiver)
            elif response is signals.EmailProcessingStatus.PROCESSED:
                handled = True

        if not handled:
            self.handle_unhandled_message(message)

    def handle_failed_message(self, raw_message: bytes):
        # TODO: forward email as attachment for inspection
        logger.error("Failed message: %s", raw_message.decode("ascii", "replace"))

    def handle_failing_receiver(
        self, message: email.message.EmailMessage, receiver: Callable
    ):
        # TODO: forward email for inspection
        logger.error(
            "Failed receiver %s:%s; message: %s",
            receiver.__module__,
            receiver.__qualname__,
            str(message),
        )

    def handle_unhandled_message(self, message: email.message.EmailMessage):
        # TODO: pass email through to a fallback alias?
        logger.error("Unhandled message: %s", str(message))
