# Copyright (C) 2025  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import pytest

from swh.web.alter.models import (
    Alteration,
    AlterationCategory,
    Event,
    EventCategory,
    EventRecipient,
    Origin,
    Token,
)


@pytest.fixture
def alteration(db):
    """An `Alteration` request with 2 origins."""
    alteration = Alteration.objects.create(
        category=AlterationCategory.COPYRIGHT,
        reasons="My reasons.",
        expected_outcome="My expected outcome handles aujourd'hui.",
        email="requester@example.com",
    )
    alteration.origins.add(
        Origin(url="https://forge.org/repo1"),
        Origin(url="https://forge.org/repo2"),
        bulk=False,
    )
    Event.objects.create(
        alteration=alteration,
        category=EventCategory.LOG,
        content="Public log event.",
        internal=False,
    )
    Event.objects.create(
        alteration=alteration,
        category=EventCategory.LOG,
        content="Internal log event.",
        internal=True,
    )
    return alteration


@pytest.fixture
def message_event(alteration):
    """A message `Event` to the requester."""
    return Event.objects.create(
        alteration=alteration,
        category=EventCategory.MESSAGE,
        recipient=EventRecipient.REQUESTER,
        content="Être message.",
        internal=False,
    )


@pytest.fixture
def admin_message_event(alteration):
    """A private message `Event` to the legal role."""
    return Event.objects.create(
        alteration=alteration,
        author="Susan Kare",
        category=EventCategory.MESSAGE,
        recipient=EventRecipient.LEGAL,
        content="Être message.",
        internal=True,
    )


@pytest.fixture
def token(alteration):
    """A magic link `Token` for an `Alteration` request."""
    return Token.create_for(alteration)
