# Copyright (C) 2025  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, Any, Union
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_domain_name, validate_email
from django.db import IntegrityError, models, transaction
from django.db.models import Q
from django.db.models.query import QuerySet
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.translation import gettext as _

from .apps import APP_LABEL

if TYPE_CHECKING:
    from django.contrib.sessions.backends.base import SessionBase


class BaseModel(models.Model):
    """An abstract base model to provide UUID pks and timestamps."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    """UUID primary key"""

    created_at = models.DateTimeField(_("created"), auto_now_add=True)
    """Creation date"""

    updated_at = models.DateTimeField(_("updated"), auto_now=True)
    """Last update"""

    class Meta:
        abstract = True


class OriginOutcome(models.TextChoices):
    VALIDATING = "validating", _("Validating")
    REJECTED = "rejected", _("Rejected")
    MAILMAP = "mailmap", _("Mailmap")
    MASK = "mask", _("Permanent mask")
    TAKEDOWN = "takedown", _("Takedown")
    BLOCK = "block", _("Takedown and block")


class OriginOwnership(models.TextChoices):
    UNKNOWN = "unknown", _("?")
    OWNER = "owner", _("Requester is the owner of the origin")
    FORK = "fork", _("Fork of an origin owned by the requester")
    OTHER = "other", _("Origin has no direct link with the requester")


class Origin(BaseModel):
    """Origins concerned by an `Alteration`."""

    url = models.URLField(_("URL"))
    """Origin's URL"""

    alteration = models.ForeignKey(
        "Alteration",
        related_name="origins",
        on_delete=models.RESTRICT,
        null=False,
    )
    """Alteration FK"""

    outcome = models.CharField(
        _("outcome"),
        max_length=20,
        choices=OriginOutcome,
        default=OriginOutcome.VALIDATING,
    )
    """Outcome for this origin"""

    reason = models.TextField(_("reason for this outcome"), blank=True)
    """Outcome's reason"""

    code_license = models.TextField(_("license found in code"), blank=True)
    """License found in / guessed from the source code"""

    available = models.BooleanField(
        _("available"),
        help_text=_("Is this URL is still available online ?"),
        null=True,
    )
    """URL is still available"""

    ownership = models.CharField(
        _("owner"),
        help_text=_("Is Requester the owner of this origin or is it a fork ?"),
        max_length=20,
        choices=OriginOwnership,
        default=OriginOwnership.UNKNOWN,
    )
    """Is Requester the owner of this origin or is it a fork"""

    class Meta:
        app_label = APP_LABEL
        db_table = "origin"
        indexes = [models.Index(fields=["url"])]
        constraints = [
            models.UniqueConstraint(fields=["alteration_id", "url"], name="unique_url"),
        ]

    def __repr__(self) -> str:
        return f"<Origin: {self.url} ({self.pk})>"

    def __str__(self) -> str:
        return self.url

    def get_admin_url(self):
        return reverse(
            "alteration-origin-admin",
            kwargs={"pk": self.pk, "alteration_pk": self.alteration_id},
        )


class AlterationManager(models.Manager["Alteration"]):
    """Custom ``Alteration`` manager."""

    def search(self, query: str) -> QuerySet[Alteration, Alteration]:
        """A basic search for requests.

        Will find requests where `query` is to be found (case insensitive) in either:
        * its ``reasons`` field
        * its ``expected_outcome`` field
        * one of its ``Origin`` url
        * Requester's email

        Args:
            query: search query
        """
        base_queryset = super().get_queryset()
        search_filters = (
            Q(reasons__icontains=query)
            | Q(expected_outcome__icontains=query)
            | Q(origins__url__icontains=query)
            | Q(email__icontains=query)
        )
        return base_queryset.filter(search_filters).distinct()


class AlterationStatus(models.TextChoices):
    VALIDATING = "validating", _("Validating")
    PLANNING = "planning", _("Planning")
    EXECUTING = "executing", _("Executing")
    PROCESSED = "processed", _("Processed")
    REJECTED = "rejected", _("Rejected")
    CLOSED = "closed", _("Closed")
    ARCHIVED = "archived", _("Archived")

    __empty__ = _("Filter by status")


class AlterationCategory(models.TextChoices):
    COPYRIGHT = "copyright", _("Copyright / License infringement")
    PII = "pii", _("Personal Identifiable Information")
    LEGAL = "legal", _("Other legal matters")

    __empty__ = _("Filter by category")


class Alteration(BaseModel):
    """An alteration request."""

    status = models.CharField(
        _("status"),
        max_length=20,
        choices=AlterationStatus,
        default=AlterationStatus.VALIDATING,
    )
    """Progression indicator"""

    category = models.CharField(
        _("category"), max_length=20, choices=AlterationCategory
    )
    """The category/type of this alteration"""

    reasons = models.TextField(_("reasons"), null=False)
    """The alteration request reasons"""

    expected_outcome = models.TextField(_("expected outcome"), null=False)
    """The Requester expectations"""

    email = models.EmailField(_("requester's email"))
    """Requester's email"""

    objects = AlterationManager()

    class Meta:
        app_label = APP_LABEL
        db_table = "alteration"
        ordering = ["-created_at"]

    def get_absolute_url(self):
        return reverse("alteration-details", kwargs={"pk": self.pk})

    def get_admin_url(self):
        return reverse("alteration-admin", kwargs={"pk": self.pk})

    @classmethod
    def create_from_assistant(cls, session: SessionBase) -> Alteration:
        """Create an alteration request from the alteration request assistant.

        Email notifications are sent to the requester & operators.

        Args:
            session: django's session store

        Returns:
            an Alteration instance

        Raises:
            DatabaseError: something went wrong while creating objects in the database
        """
        with transaction.atomic():
            alteration = Alteration.objects.create(
                category=session["alteration_category"],
                reasons=session["alteration_reasons"],
                expected_outcome=session["alteration_expected_outcome"],
                email=session["alteration_email"],
            )
            Origin.objects.bulk_create(
                [
                    Origin(alteration=alteration, url=url)
                    for url in session["alteration_origins"]
                ]
            )
            Event.objects.create(
                alteration=alteration,
                category=EventCategory.LOG,
                author=_("Requester"),
                content=_("Alteration request created."),
                internal=False,
            )
        return alteration

    @property
    def is_read_only(self) -> bool:
        return self.status == AlterationStatus.ARCHIVED

    def __repr__(self) -> str:
        return f"<Alteration: {self.category} [{self.email}] ({self.pk})>"

    def __str__(self) -> str:
        return f"{self.get_category_display()} by {self.email}"


class EventRecipient(models.TextChoices):
    REQUESTER = "requester", _("Requester")
    SUPPORT = "support", _("Support")
    MANAGER = "manager", _("Manager")
    LEGAL = "legal", _("Legal")
    TECHNICAL = "technical", _("Technical")


class EventCategory(models.TextChoices):
    LOG = "log", _("Event")
    MESSAGE = "message", _("Message")


class EventManager(models.Manager["Event"]):
    """Custom ``Event`` manager."""

    def get_queryset(self) -> QuerySet[Event, Event]:
        """Filters internal events.

        Returns:
            An ``Event`` queryset with ``internal`` events filtered out.
        """
        return super().get_queryset().filter(internal=False)


class Event(BaseModel):
    """An event on an `Alteration`.

    An event could be
    * a log of a status change or a modification of any another field / Origin
    * a message between recipients
    """

    alteration = models.ForeignKey(
        "Alteration",
        related_name="events",
        on_delete=models.RESTRICT,
        null=False,
    )
    """Alteration FK"""

    category = models.CharField(_("category"), max_length=20, choices=EventCategory)
    """Category/type of event"""

    author = models.CharField(_("author"), max_length=200, blank=True)
    """The name of the author of this event"""

    recipient = models.CharField(
        _("recipient role"), max_length=20, choices=EventRecipient, blank=True
    )
    """The role targeted by this event, a value is required to send notifications"""

    content = models.TextField(_("content"), blank=True)
    """The event's textual content"""

    internal = models.BooleanField(
        _("internal"),
        default=True,
        help_text=_(
            "Internal messages are not visible in the Requester activity log to avoid "
            "unnecessary noise, they must not be used for confidential exchanges "
            "between team members and could be requested by the user."
        ),
    )
    """Internal actions are not visible to the Requester"""

    objects = models.Manager()
    public_objects = EventManager()

    class Meta:
        app_label = APP_LABEL
        db_table = "event"
        ordering = ["-created_at"]

    def __repr__(self) -> str:
        return f"<Event: {self.category} [{self.author}] ({self.pk})>"

    def __str__(self) -> str:
        return f"{self.get_category_display()} by {self.author} for {self.alteration}"

    def get_admin_url(self):
        return reverse(
            "alteration-event-admin",
            kwargs={"pk": self.pk, "alteration_pk": self.alteration_id},
        )


TOKEN_TTL = 15 * 60
"""Token expiration delay in seconds"""

TOKEN_NBYTES = 20
"""Token length, must be less than ~1.3 x `Token.value` max length"""


def _default_token_expires_at():
    return timezone.now() + timedelta(seconds=TOKEN_TTL)


def _default_token_value():
    return get_random_string(TOKEN_NBYTES)


class Token(BaseModel):
    """Ephemeral auth tokens to access an `Alteration` or validate an email."""

    alteration = models.ForeignKey(
        "Alteration",
        related_name="tokens",
        on_delete=models.CASCADE,
        null=True,
    )
    """Alteration FK"""

    email = models.EmailField(_("email"), null=True)
    """An email address to validate"""

    value = models.CharField(_("value"), max_length=32, default=_default_token_value)
    """Token value"""

    expires_at = models.DateTimeField(
        _("expiration date"), null=False, default=_default_token_expires_at
    )
    """Token expiration date"""

    objects = models.Manager()

    class Meta:
        app_label = APP_LABEL
        db_table = "token"
        indexes = [models.Index(fields=["value"]), models.Index(fields=["email"])]
        constraints = [
            models.UniqueConstraint(fields=["value"], name="unique_token_value"),
        ]

    def __repr__(self) -> str:
        return f"<Token: {self.value}>"

    def __str__(self) -> str:
        item = self.alteration if self.alteration else self.email
        return f"{self.value} for {item}"

    def get_absolute_url(self) -> str:
        route = (
            "alteration-link" if self.alteration else "alteration-email-verification"
        )
        return reverse(route, kwargs={"value": self.value})

    @property
    def expired(self) -> bool:
        return self.expires_at < timezone.now()

    @classmethod
    def create_for(cls, obj: Union[Alteration, str]) -> Token:
        """Create a token for an `Alteration` request or an email verification.

        Args:
            obj: an `Alteration` instance or an email

        Returns:
            A `Token` instance

        Raises:
            ValueError: `obj` is neither an `Alteration` nor an email
            IntegrityError: if we're not able to create a token after 5 attempts
        """
        params: dict[str, Union[Alteration, str]]
        if isinstance(obj, Alteration):
            params = {"alteration": obj}
        elif isinstance(obj, str):
            params = {"email": obj}
        else:
            raise ValueError(
                _(
                    "Invalid parameter %(obj)s, a token can only be created for "
                    "an alteration request or an email address."
                )
                % {"obj": obj}
            )

        for attempt in range(1, 5):
            try:
                return cls.objects.create(**params)
            except IntegrityError as exc:
                last_exception = exc
        raise IntegrityError(
            f"Could not create a unique token after {attempt} attempts"
        ) from last_exception


def validate_email_or_domain(value: Any) -> None:
    """Check if value is a valid email or a domain name.

    Args:
        value: a string

    Raises:
        ValidationError: `value` is neither an email address nor a domain name

    Returns:
        True is `value` is an email or a domain
    """
    try:
        validate_email(value)
        return
    except ValidationError:
        pass
    try:
        validate_domain_name(value)
        return
    except ValidationError:
        pass

    raise ValidationError(
        _("%(value)s is neither an email address nor a domain name."),
        params={"value": value},
    )


class LowerCharField(models.CharField):
    """A lowercased `CharField`."""

    def pre_save(self, model_instance: models.Model, add: bool) -> Any:
        """Lower case value before saving the instance."""
        value = getattr(model_instance, self.attname)
        if isinstance(value, str):
            setattr(model_instance, self.attname, value.lower())
        return super().pre_save(model_instance, add)


class BlockList(BaseModel):
    """Email or domain block list.

    Email addresses or domains found in this table are not allowed to initiate an
    `Alteration` request.
    """

    email_or_domain = LowerCharField(
        _("email or domain"), max_length=254, validators=[validate_email_or_domain]
    )
    """An email address or a domain"""

    reason = models.TextField(_("reasons"), blank=True)
    """Reason for the ban (ie. added by an admin or requested by a user)"""

    class Meta:
        app_label = APP_LABEL
        db_table = "block_list"
        indexes = [models.Index(fields=["email_or_domain"])]
        constraints = [
            models.UniqueConstraint(
                fields=["email_or_domain"], name="unique_email_or_domain"
            ),
        ]

    @classmethod
    def is_blocked(cls, email: str) -> bool:
        """Check if `email` or its domain is blocked.

        We use email or domains stored in this table and optionally domains from
        https://github.com/disposable-email-domains/disposable-email-domains

        Args:
            value: an email address

        Returns:
            True if the address is blocked

        Raises:
            ValueError: `email` is an invalid email address
        """
        try:
            validate_email(email)
        except ValidationError as exc:
            raise ValueError(_("Invalid email value")) from exc
        email = email.lower()
        domain = email.split("@")[-1]

        if settings.ALTER_SETTINGS.get("block_disposable_email_domains"):
            from disposable_email_domains import blocklist

            disposable = domain in blocklist
        else:
            disposable = False

        return (
            disposable
            or cls.objects.filter(email_or_domain__in=[email, domain]).exists()
        )
