# Copyright (C) 2025  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from django import forms
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.paginator import Paginator
from django.forms.models import model_to_dict
from django.utils.translation import gettext as _

from .emails import send_alteration_magic_link, send_email_magic_link
from .models import (
    Alteration,
    AlterationCategory,
    BlockList,
    Event,
    EventCategory,
    EventRecipient,
    Origin,
    Token,
)
from .utils import generate_alteration_changelog, generate_origin_changelog

if TYPE_CHECKING:
    from django.core.paginator import Page
    from django.http import HttpRequest


class MultipleOriginField(forms.MultipleChoiceField):
    def validate(self, value):
        """Validate a list of origin."""
        from swh.web.utils.archive import lookup_origin

        if self.required and not value:
            raise ValidationError(self.error_messages["required"], code="required")
        # Validate that each value in the value list is a swh origin
        for origin in value:
            try:
                lookup_origin(origin)
            except ObjectDoesNotExist:  # Should be a utils.exc.NotFoundExc
                raise ValidationError(
                    _("%(origin)s is not archived by Software Heritage")
                    % {"origin": origin}
                )


class EmailVerificationForm(forms.Form):
    """Email verification form."""

    email = forms.EmailField(label=_("Email"), required=True)

    def __init__(self, *args, request: HttpRequest, **kwargs):
        """Store the extra ``request`` parameters.

        Args:
            request: an HttpRequest
        """
        super().__init__(*args, **kwargs)
        self.request = request

    def clean_email(self) -> str:
        """Check that `email` has not been blocked.

        Returns:
            the cleaned email

        Raised:
            ValidationError: `email` or its domain is blocked.
        """
        email = self.cleaned_data["email"]
        if BlockList.is_blocked(email):
            raise ValidationError(
                _(
                    "%(email)s has been blocked by Software Heritage and can't be "
                    "used to request an archive alteration. Please contact us if you "
                    "need to unblock this address."
                )
                % {"email": email}
            )
        return email

    def clean(self) -> Optional[dict[str, Any]]:
        """Send the verification email.

        Returns:
            Form's cleaned data.
        """
        cleaned_data = super().clean()
        if cleaned_data:
            email = cleaned_data["email"]
            token = Token.create_for(email)
            send_email_magic_link(token, self.request)
        return cleaned_data


class OriginSearchForm(forms.Form):
    """Search Origins."""

    query = forms.CharField(label=_("Search"), required=True)


class OriginSelectForm(forms.Form):
    """Select Origins."""

    urls = MultipleOriginField(widget=forms.CheckboxSelectMultiple)


# TODO: proper templates
INITIALS_REASONS = {
    "copyright": {
        "reasons": _(
            "The code available in the repos in under the xxx license which does "
            "not allow..."
        ),
        "expected_outcome": _(
            "Please remove archived content for repos ... and block them from being "
            "archived again"
        ),
    },
    "pii": {
        "reasons": _(
            "I've rewritten the history of my repo due to ... your archive still "
            "shows the old content and I need you to delete it."
        ),
        "expected_outcome": _(
            "Please remove archived content for repos ... and re-archive the current "
            "version."
        ),
    },
    "legal": {
        "reasons": _(
            "malicious content is available on the specified origins [explain what "
            "kind of content]"
        ),
        "expected_outcome": _(
            "I've submitted a takedown request to the legal authorities but meanwhile"
            "please mask the origins so the content is not publicly available on SWH "
            "anymore"
        ),
    },
}


class ReasonsForm(forms.Form):
    """Alteration request's reasons and expected outcome."""

    reasons = forms.CharField(
        label=_("Reasons why the archive content should be altered"),
        help_text=_(
            "Please describe as clearly as possible the reasons for your request"
        ),
        widget=forms.Textarea,
        required=True,
    )
    expected_outcome = forms.CharField(
        label=_("Expected outcome of your request"),
        help_text=_(
            "You can specify your expectations regarding the archive alteration "
            "mechanisms described in the content policies page."
        ),
        widget=forms.Textarea,
        required=True,
    )


class ConfirmationForm(forms.Form):
    """Confirm the alteration request."""

    confirm = forms.BooleanField(
        label=_(
            "I hereby confirm that the information provided in this summary "
            "is accurate, correct and complete; I am not making this request "
            "with any unethical or fraudulent intent"
        ),
        required=True,
    )


class CategoryForm(forms.Form):
    """Choose an alteration category.

    This form is solely used for data validation, the assistant_category template will
    display each choices as a submit button.
    """

    category = forms.ChoiceField(
        label=_("Category"),
        choices=AlterationCategory,
        required=True,
    )


class AlterationAccessForm(forms.Form):
    """Security check before accessing an ``Alteration``."""

    email = forms.EmailField(label=_("Your email address"), required=True)

    def __init__(self, *args, alteration: Alteration, request: HttpRequest, **kwargs):
        """Store the extra ``alteration`` & ``request`` parameters.

        Args:
            alteration: an Alteration instance
            request: an HttpRequest
        """
        super().__init__(*args, **kwargs)
        self.alteration = alteration
        self.request = request

    def clean(self) -> Optional[dict[str, Any]]:
        """Check that `email` matches the requested `Alteration`.

        If it matches, send an email containing a magic link to auth the requester, if
        or else do nothing.

        Returns:
            Form's cleaned data.
        """
        cleaned_data = super().clean()
        if cleaned_data and cleaned_data["email"] == self.alteration.email:
            token = Token.create_for(self.alteration)
            send_alteration_magic_link(token, self.request)
        return cleaned_data


class AlterationSearchForm(forms.ModelForm):
    """Search alterations."""

    class Meta:
        model = Alteration
        fields = ["status"]

    query = forms.CharField(label=_("Search"), required=False)
    page = forms.IntegerField(label=_("Page"), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["status"].required = False

    def search(self) -> Page:
        """Search/filter results and handle pagination.

        Returns:
            A paginated list of `Alteration`.
        """
        if self.cleaned_data.get("query"):
            qs = Alteration.objects.search(self.cleaned_data["query"]).select_related()
        else:
            qs = Alteration.objects.select_related()
        if self.cleaned_data.get("status"):
            qs = qs.filter(status=self.cleaned_data["status"])
        paginator = Paginator(qs, 20)
        return paginator.get_page(self.cleaned_data.get("page", 1))


class OriginAdminForm(forms.ModelForm):
    """Update an ``Origin``."""

    class Meta:
        model = Origin
        exclude = ["id", "alteration"]
        widgets = {
            "code_license": forms.TextInput(),
            "reason": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, request: Optional[HttpRequest] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

    def save(self, commit=True) -> Origin:
        """Save and generate a changelog if needed."""
        old_values = model_to_dict(self.instance)
        old_url = self.instance.url
        origin = super().save(commit)
        if self.has_changed():
            previous_values = {key: old_values[key] for key in self.changed_data}
            Event.objects.create(
                alteration=self.instance.alteration,
                author=self.request.user.get_username() if self.request else "",
                category=EventCategory.LOG,
                content=generate_origin_changelog(old_url, previous_values),
                internal=False,
            )
        return origin


class AlterationForm(forms.ModelForm):
    """Update an ``Alteration``."""

    class Meta:
        model = Alteration
        exclude = ["id", "origins", "events", "status", "category", "email"]

    def __init__(self, *args, author: str = "", **kwargs):
        super().__init__(*args, **kwargs)
        self.author = author

    def save(self, commit=True) -> Alteration:
        """Save and generate a changelog if needed."""
        old_values = model_to_dict(self.instance)
        alteration = super().save(commit)
        if self.has_changed():
            previous_values = {key: old_values[key] for key in self.changed_data}
            Event.objects.create(
                alteration=alteration,
                author=self.author,
                category=EventCategory.LOG,
                content=generate_alteration_changelog(previous_values),
                internal=False,
            )
        return alteration


class AlterationAdminForm(AlterationForm):
    """Update an ``Alteration``."""

    class Meta:
        model = Alteration
        exclude = ["id", "origins", "events"]


class MessageForm(forms.ModelForm):
    """Message form for requesters."""

    class Meta:
        model = Event
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 4}),
        }
        labels = {"content": _("Your message")}

    def __init__(self, *args, alteration: Alteration, **kwargs):
        super().__init__(*args, **kwargs)
        self.alteration = alteration
        self.fields["content"].required = True

    def save(self, commit=True) -> Event:
        event = super().save(commit=False)
        event.alteration = self.alteration
        event.author = "Requester"
        event.category = EventCategory.MESSAGE
        event.recipient = EventRecipient.SUPPORT
        event.internal = False
        event.save()
        return event


class MessageAdminForm(forms.ModelForm):
    """Message form for admins."""

    class Meta:
        model = Event
        fields = ["recipient", "internal", "content"]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, alteration: Alteration, author: str, **kwargs):
        super().__init__(*args, **kwargs)
        self.alteration = alteration
        self.author = author
        self.fields["recipient"].required = True
        self.fields["content"].required = True

    def clean(self):
        cleaned_data = super().clean()
        recipient = cleaned_data.get("recipient")
        internal = cleaned_data.get("internal")

        if recipient == EventRecipient.REQUESTER and internal:
            self.add_error(
                "internal", _("Can't send an `internal` message to the Requester")
            )
        return cleaned_data

    def save(self, commit=True) -> Event:
        event = super().save(commit=False)
        event.alteration = self.alteration
        event.author = self.author
        event.category = EventCategory.MESSAGE
        event.save()
        return event


class EventAdminForm(forms.ModelForm):
    """Update an ``Event``."""

    class Meta:
        model = Event
        exclude = ["id", "alteration", "category"]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 4}),
        }
