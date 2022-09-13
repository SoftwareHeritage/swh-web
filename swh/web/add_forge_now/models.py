# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from __future__ import annotations

import enum
from typing import Dict, List
from urllib.parse import urlparse

from django.db import models

from ..config import get_config
from ..inbound_email.utils import get_address_for_pk
from .apps import APP_LABEL


class RequestStatus(enum.Enum):
    """Request statuses.

    Values are used in the ui.

    """

    PENDING = "Pending"
    WAITING_FOR_FEEDBACK = "Waiting for feedback"
    FEEDBACK_TO_HANDLE = "Feedback to handle"
    ACCEPTED = "Accepted"
    SCHEDULED = "Scheduled"
    FIRST_LISTING_DONE = "First listing done"
    FIRST_ORIGIN_LOADED = "First origin loaded"
    REJECTED = "Rejected"
    SUSPENDED = "Suspended"
    UNSUCCESSFUL = "Unsuccessful"

    @classmethod
    def choices(cls):
        return tuple((variant.name, variant.value) for variant in cls)

    @classmethod
    def next_statuses(cls) -> Dict[RequestStatus, List[RequestStatus]]:
        return {
            cls.PENDING: [cls.WAITING_FOR_FEEDBACK, cls.REJECTED, cls.SUSPENDED],
            cls.WAITING_FOR_FEEDBACK: [cls.FEEDBACK_TO_HANDLE],
            cls.FEEDBACK_TO_HANDLE: [
                cls.WAITING_FOR_FEEDBACK,
                cls.ACCEPTED,
                cls.REJECTED,
                cls.SUSPENDED,
                cls.UNSUCCESSFUL,
            ],
            cls.ACCEPTED: [cls.SCHEDULED],
            cls.SCHEDULED: [
                cls.FIRST_LISTING_DONE,
                # in case of race condition between lister and loader:
                cls.FIRST_ORIGIN_LOADED,
            ],
            cls.FIRST_LISTING_DONE: [cls.FIRST_ORIGIN_LOADED],
            cls.FIRST_ORIGIN_LOADED: [],
            cls.REJECTED: [],
            cls.SUSPENDED: [cls.PENDING],
            cls.UNSUCCESSFUL: [],
        }

    @classmethod
    def next_statuses_str(cls) -> Dict[str, List[str]]:
        return {
            key.name: [value.name for value in values]
            for key, values in cls.next_statuses().items()
        }

    def allowed_next_statuses(self) -> List[RequestStatus]:
        return self.next_statuses()[self]


class RequestActorRole(enum.Enum):
    MODERATOR = "moderator"
    SUBMITTER = "submitter"
    FORGE_ADMIN = "forge admin"
    EMAIL = "email"

    @classmethod
    def choices(cls):
        return tuple((variant.name, variant.value) for variant in cls)


class RequestHistory(models.Model):
    """Comment or status change. This is commented or changed by either submitter or
    moderator.

    """

    request = models.ForeignKey("Request", models.DO_NOTHING)
    text = models.TextField()
    actor = models.TextField()
    actor_role = models.TextField(choices=RequestActorRole.choices())
    date = models.DateTimeField(auto_now_add=True)
    new_status = models.TextField(choices=RequestStatus.choices(), null=True)
    message_source = models.BinaryField(null=True)

    class Meta:
        app_label = APP_LABEL
        db_table = "add_forge_request_history"


class Request(models.Model):
    status = models.TextField(
        choices=RequestStatus.choices(),
        default=RequestStatus.PENDING.name,
    )
    submission_date = models.DateTimeField(auto_now_add=True)
    submitter_name = models.TextField()
    submitter_email = models.TextField()
    submitter_forward_username = models.BooleanField(default=False)
    # FIXME: shall we do create a user model inside the webapp instead?
    forge_type = models.TextField()
    forge_url = models.URLField()
    forge_contact_email = models.EmailField()
    forge_contact_name = models.TextField()
    forge_contact_comment = models.TextField(
        null=True,
        help_text="Where did you find this contact information (url, ...)",
    )

    last_moderator = models.TextField(default="None")
    last_modified_date = models.DateTimeField(null=True)

    class Meta:
        app_label = APP_LABEL
        db_table = "add_forge_request"

    @property
    def inbound_email_address(self) -> str:
        """Generate an email address for correspondence related to this request."""
        base_address = get_config()["add_forge_now"]["email_address"]
        return get_address_for_pk(salt=APP_LABEL, base_address=base_address, pk=self.pk)

    @property
    def forge_domain(self) -> str:
        """Get the domain/netloc out of the forge_url.

        Fallback to using the first part of the url path, if the netloc can't be found
        (for instance, if the url scheme hasn't been set).
        """

        parsed_url = urlparse(self.forge_url)
        domain = parsed_url.netloc
        if not domain:
            domain = parsed_url.path.split("/", 1)[0]

        return domain
