# Copyright (C) 2025  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import unicodedata
from urllib.parse import urljoin

import pytest
from pytest_django.asserts import assertTemplateUsed

from swh.web.alter.emails import (
    send_alteration_confirmation,
    send_alteration_magic_link,
    send_alteration_notification,
    send_email_magic_link,
    send_message_notification,
)
from swh.web.alter.models import Token

URL = "http://testserver"  # RequestFactory sets `testserver` as the default host
FROM = "no-replay@swh.localhost"


@pytest.fixture(autouse=True)
def _default_url(settings):
    settings.DEFAULT_URL = URL
    settings.DEFAULT_FROM_EMAIL = FROM


def test_admin_alteration_notification(alteration, mailoutbox, rf):
    with assertTemplateUsed("emails/admin_alteration_notification.txt"):
        send_alteration_notification(alteration, rf.get("/"))
    assert len(mailoutbox) == 1
    message = mailoutbox[0]
    assert message.subject == "New archive alteration request"
    assert message.from_email == FROM
    assert message.to == ["alter-support@localhost"]
    assert alteration.get_category_display() in message.body
    assert urljoin(URL, alteration.get_admin_url()) in message.body
    assert "https://forge.org/repo1" in message.body
    assert "https://forge.org/repo2" in message.body
    assert "My reasons." in message.body
    assert "My expected outcome handles aujourd'hui." in message.body


def test_alteration_confirmation(alteration, mailoutbox, rf):
    with assertTemplateUsed("emails/alteration_confirmation.txt"):
        send_alteration_confirmation(alteration, rf.get("/"))
    assert len(mailoutbox) == 1
    message = mailoutbox[0]
    assert message.subject == "Confirmation of your archive alteration request"
    assert message.from_email == FROM
    assert message.to == ["requester@example.com"]
    assert alteration.get_category_display() not in message.body
    assert urljoin(URL, alteration.get_absolute_url()) in message.body
    assert alteration.get_admin_url() not in message.body
    assert "https://forge.org/repo1" in message.body
    assert "https://forge.org/repo2" in message.body
    assert "My reasons." not in message.body
    assert "My expected outcome handles aujourd'hui." not in message.body


def test_new_message_notification(message_event, mailoutbox, rf):
    with assertTemplateUsed("emails/message_notification.txt"):
        send_message_notification(message_event, rf.get("/"))
    assert len(mailoutbox) == 1
    message = mailoutbox[0]
    alteration = message_event.alteration
    assert message.subject == "New message notification"
    assert message.from_email == FROM
    assert message.to == ["requester@example.com"]
    assert alteration.get_category_display() in message.body
    assert urljoin(URL, alteration.get_absolute_url()) in message.body
    assert alteration.get_admin_url() not in message.body
    assert "Être message." not in message.body


def test_admin_message_notification(admin_message_event, mailoutbox, rf):
    with assertTemplateUsed("emails/admin_message_notification.txt"):
        send_message_notification(admin_message_event, rf.get("/"))
    assert len(mailoutbox) == 1
    message = mailoutbox[0]
    alteration = admin_message_event.alteration
    assert message.subject == f"New message on {alteration}"
    assert message.from_email == FROM
    assert message.to == ["alter-legal@localhost"]
    assert alteration.get_category_display() in message.body
    assert urljoin(URL, alteration.get_admin_url()) in message.body
    assert "Être message." in message.body
    assert "From: Susan Kare" in message.body


def test_alteration_magic_link(token, mailoutbox, rf):
    with assertTemplateUsed("emails/alteration_magic_link.txt"):
        send_alteration_magic_link(token, rf.get("/"))
    assert len(mailoutbox) == 1
    message = mailoutbox[0]
    assert message.subject == "Access to your alteration request"
    assert message.from_email == FROM
    assert message.to == [token.alteration.email]
    assert urljoin(URL, token.get_absolute_url()) in message.body
    assert "this link will expire in 14 minutes." in unicodedata.normalize(
        "NFKD",
        message.body,  # remove non-breaking space added by django's timeuntil
    )


@pytest.mark.django_db
def test_email_magic_link(mailoutbox, rf):
    email = "mail@domain.localhost"
    token = Token.create_for(email)
    with assertTemplateUsed("emails/email_magic_link.txt"):
        send_email_magic_link(token, rf.get("/"))
    assert len(mailoutbox) == 1
    message = mailoutbox[0]
    assert message.subject == "Please confirm your email address"
    assert message.from_email == FROM
    assert message.to == [email]
    assert urljoin(URL, token.get_absolute_url()) in message.body
    assert "This link will expire in 14 minutes." in unicodedata.normalize(
        "NFKD",
        message.body,  # remove non-breaking space added by django's timeuntil
    )
