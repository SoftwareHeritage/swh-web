# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import enum

from django.db import models


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
    DENIED = "Denied"

    @classmethod
    def choices(cls):
        return tuple((variant.name, variant.value) for variant in cls)


class RequestActorRole(enum.Enum):
    MODERATOR = "moderator"
    SUBMITTER = "submitter"

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


class Request(models.Model):
    status = models.TextField(
        choices=RequestStatus.choices(), default=RequestStatus.PENDING.name,
    )
    submission_date = models.DateTimeField(auto_now_add=True)
    submitter_name = models.TextField()
    submitter_email = models.TextField()
    # FIXME: shall we do create a user model inside the webapp instead?
    forge_type = models.TextField()
    forge_url = models.TextField()
    forge_contact_email = models.EmailField()
    forge_contact_name = models.TextField()
    forge_contact_comment = models.TextField(
        help_text="Where did you find this contact information (url, ...)",
    )
