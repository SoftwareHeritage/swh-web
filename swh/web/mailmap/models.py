# Copyright (C) 2020-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.db import models


class UserMailmapManager(models.Manager):
    """A queryset manager which defers all :class:`models.DateTimeField` fields, to avoid
    resetting them to an old value involuntarily."""

    @classmethod
    def deferred_fields(cls):
        try:
            return cls._deferred_fields
        except AttributeError:
            cls._deferred_fields = [
                field.name
                for field in UserMailmap._meta.get_fields()
                if isinstance(field, models.DateTimeField) and not field.auto_now
            ]
            return cls._deferred_fields

    def get_queryset(self):
        return super().get_queryset().defer(*self.deferred_fields())


class UserMailmap(models.Model):
    """
    Model storing mailmap settings submitted by users.
    """

    user_id = models.CharField(max_length=50, null=True)
    """Optional user id from Keycloak"""

    from_email = models.TextField(unique=True, null=False)
    """Email address to find author in the archive"""

    from_email_verified = models.BooleanField(default=False)
    """Indicates if the from email has been verified"""

    from_email_verification_request_date = models.DateTimeField(null=True)
    """Last from email verification request date"""

    display_name = models.TextField(null=False)
    """Display name to use for the author instead of the archived one"""

    display_name_activated = models.BooleanField(default=False)
    """Indicates if the new display name should be used"""

    to_email = models.TextField(null=True)
    """Optional new email to use in the display name instead of the archived one"""

    to_email_verified = models.BooleanField(default=False)
    """Indicates if the to email has been verified"""

    to_email_verification_request_date = models.DateTimeField(null=True)
    """Last to email verification request date"""

    mailmap_last_processing_date = models.DateTimeField(null=True)
    """Last mailmap synchronisation date with swh-storage"""

    last_update_date = models.DateTimeField(auto_now=True)
    """Last date that mailmap model was updated"""

    class Meta:
        app_label = "swh_web_mailmap"
        db_table = "user_mailmap"

    # Defer _date fields by default to avoid updating them by mistake
    objects = UserMailmapManager()

    @property
    def full_display_name(self) -> str:
        if self.to_email is not None and self.to_email_verified:
            return "%s <%s>" % (self.display_name, self.to_email)
        else:
            return self.display_name


class UserMailmapEvent(models.Model):
    """
    Represents an update to a mailmap object
    """

    timestamp = models.DateTimeField(auto_now=True, null=False)
    """Timestamp of the moment the event was submitted"""

    user_id = models.CharField(max_length=50, null=False)
    """User id from Keycloak of the user who changed the mailmap.
    (Not necessarily the one who the mail belongs to.)"""

    request_type = models.CharField(max_length=50, null=False)
    """Either ``add`` or ``update``."""

    request = models.TextField(null=False)
    """JSON dump of the request received."""

    successful = models.BooleanField(default=False, null=False)
    """If False, then the request failed or crashed before completing,
    and may or may not have altered the database's state."""

    class Meta:
        indexes = [
            models.Index(fields=["timestamp"]),
        ]
        app_label = "swh_web_mailmap"
        db_table = "user_mailmap_event"
