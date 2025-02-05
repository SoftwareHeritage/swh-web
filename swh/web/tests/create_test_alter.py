# Copyright (C) 2024 The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

"""Fixtures for e2e tests related to swh-web-alter."""

from datetime import timedelta

from django.utils import timezone

from swh.web.alter.models import (
    Alteration,
    AlterationCategory,
    AlterationStatus,
    BlockList,
    Event,
    EventCategory,
    EventRecipient,
    Origin,
    Token,
)

alterations = {
    # A copyright alteration request
    "00000000-0000-4000-8000-000000000001": {
        "status": AlterationStatus.PLANNING,
        "category": AlterationCategory.COPYRIGHT,
        "reasons": "not published under an open license",
        "expected_outcome": "delete everything",
        "email": "user1@domain.local",
        "origins": [
            "https://gitlab.local/user1/code",
            "https://gitlab.local/user1/project",
        ],
    }
}
for id_, a_props in alterations.items():
    origins = a_props.pop("origins")
    alteration, _ = Alteration.objects.get_or_create(id=id_, **a_props)  # type: ignore
    for url in origins:
        Origin.objects.get_or_create(url=url, alteration=alteration)

events = {
    # Events for the copyright alteration request
    "00000000-0000-4000-9000-000000000001": {
        "category": EventCategory.LOG,
        "alteration_id": "00000000-0000-4000-8000-000000000001",
        "content": "created",
        "internal": False,
    },
    "00000000-0000-4000-9000-000000000002": {
        "category": EventCategory.MESSAGE,
        "alteration_id": "00000000-0000-4000-8000-000000000001",
        "author": "Requester",
        "recipient": EventRecipient.SUPPORT,
        "content": "I would like to be informed of the progress of my request",
        "internal": False,
    },
    "00000000-0000-4000-9000-000000000003": {
        "category": EventCategory.MESSAGE,
        "alteration_id": "00000000-0000-4000-8000-000000000001",
        "author": EventRecipient.SUPPORT,
        "recipient": EventRecipient.LEGAL,
        "content": "Please check this internal message",
        "internal": True,
    },
}

for id_, e_props in events.items():
    Event.objects.get_or_create(id=id_, **e_props)  # type: ignore

# an expired access token for the copyright alteration request
Token.objects.get_or_create(
    value="ExpiredAccessToken",
    alteration_id="00000000-0000-4000-8000-000000000001",
    defaults={"expires_at": timezone.now() - timedelta(days=1)},
)
# an expired email confirmation token
Token.objects.get_or_create(
    value="ExpiredEmailToken",
    email="expired@domain.local",
    defaults={"expires_at": timezone.now() - timedelta(days=1)},
)
# an active access token for the copyright alteration request
Token.objects.get_or_create(
    value="ValidAccessToken",
    alteration_id="00000000-0000-4000-8000-000000000001",
    defaults={"expires_at": timezone.now() + timedelta(days=365)},
)

# block blocked@domain.local email
BlockList.objects.get_or_create(email_or_domain="blocked@domain.local", reason="spam")
