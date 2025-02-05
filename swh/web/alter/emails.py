# Copyright (C) 2025  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information
from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import gettext as _

from .models import Alteration, Event, EventRecipient, Token
from .utils import get_group_emails

if TYPE_CHECKING:
    from django.http import HttpRequest


def send_alteration_notification(alteration: Alteration, request: HttpRequest) -> None:
    """Send an alteration request notification by mail to SWH.

    Args:
        alteration: an ``Alteration``
        request: an ``HttpRequest``
    """
    send_mail(
        "New archive alteration request",
        render_to_string(
            "emails/admin_alteration_notification.txt",
            context={"alteration": alteration},
            request=request,
        ),
        settings.DEFAULT_FROM_EMAIL,
        get_group_emails("support"),
    )


def send_alteration_confirmation(alteration: Alteration, request: HttpRequest) -> None:
    """Send an alteration request confirmation by mail to the requester.

    Args:
        alteration: an ``Alteration``
        request: an ``HttpRequest``
    """
    send_mail(
        _("Confirmation of your archive alteration request"),
        render_to_string(
            "emails/alteration_confirmation.txt",
            context={"alteration": alteration},
            request=request,
        ),
        settings.DEFAULT_FROM_EMAIL,
        [alteration.email],
    )


def send_message_notification(event: Event, request: HttpRequest) -> None:
    """Send a new message notification by mail to the recipient.

    Args:
        event: an ``Event``
        request: an ``HttpRequest``
    """
    alteration = event.alteration
    if event.recipient == EventRecipient.REQUESTER:
        send_mail(
            _("New message notification"),
            render_to_string(
                "emails/message_notification.txt",
                context={"alteration": alteration},
                request=request,
            ),
            settings.DEFAULT_FROM_EMAIL,
            [alteration.email],
        )
    elif event.recipient:
        send_mail(
            f"New message on {alteration}",
            render_to_string(
                "emails/admin_message_notification.txt",
                context={"event": event, "alteration": alteration},
                request=request,
            ),
            settings.DEFAULT_FROM_EMAIL,
            get_group_emails(event.recipient),
        )


def send_alteration_magic_link(token: Token, request: HttpRequest) -> None:
    """Send a magic link to access an `Alteration` the requester.

    Args:
        token: an ``Alteration`` access ``Token``
        request: an ``HttpRequest``
    """
    assert token.alteration is not None
    send_mail(
        _("Access to your alteration request"),
        render_to_string(
            "emails/alteration_magic_link.txt",
            context={"token": token},
            request=request,
        ),
        settings.DEFAULT_FROM_EMAIL,
        [token.alteration.email],
    )


def send_email_magic_link(token: Token, request: HttpRequest) -> None:
    """Send a magic link to confirm an email address.

    Args:
        token: an email access ``Token``
    """
    assert token.email is not None
    send_mail(
        _("Please confirm your email address"),
        render_to_string(
            "emails/email_magic_link.txt",
            context={"token": token},
            request=request,
        ),
        settings.DEFAULT_FROM_EMAIL,
        [token.email],
    )
