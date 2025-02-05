# Copyright (C) 2025  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from __future__ import annotations

from collections import namedtuple
from functools import wraps
import itertools
from typing import TYPE_CHECKING, Any, Optional

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext as _

from .models import Alteration, Origin

if TYPE_CHECKING:
    from uuid import UUID

    from django.http import HttpRequest, HttpResponse

Step = namedtuple("Step", ["url", "active", "disabled"])

ProcessState = dict[str, Step]
STEPS_NAMES = ["email", "category", "origins", "reasons", "summary"]


def get_django_group_emails(group_name: str) -> list[str]:
    """Get `group_name` members email addresses from django auth system.

    Args:
        group_name: the name of the Group

    Returns:
        a list of email addresses
    """
    User = get_user_model()
    return [user.email for user in User.objects.filter(groups__name=group_name)]


def get_keycloak_group_emails(group_name: str) -> list[str]:
    """Get the mail alias for `group_name`.

    For now we use email aliases defined in the config file.

    Args:
        group_name: the name of the Group

    Returns:
        a list containing a single email alias for `group_name`
    """
    return [settings.ALTER_SETTINGS[f"{group_name}_mail_alias"]]


def get_group_emails(group_name: str) -> list[str]:
    """Get a list of recipients for `group_name`.

    The method used to fetch the emails depends on the auth backend.

    Args:
        group_name: the name of the Group

    Returns:
        a list of email addresses
    """
    if settings.SWH_AUTH_SERVER_URL:
        return get_keycloak_group_emails(group_name)
    else:
        return get_django_group_emails(group_name)


SESSION_ALTERATION_IDS = "alteration_ids"
"""Session key to store the alteration ids current user has access to."""

SESSION_VERIFIED_EMAIL = "alteration_email"
"""Session key to store an email address validated by the current user."""


def has_access(request: HttpRequest, pk: UUID) -> bool:
    """Check if the current user has access to an `Alteration`.

    Args:
        request: an HttpRequest
        pk: an `Alteration` id

    Returns:
        True if the user is allowed.
    """
    return str(pk) in request.session.get(SESSION_ALTERATION_IDS, [])


def set_access(request: HttpRequest, pk: UUID) -> None:
    """Store `pk` in the user's session.

    Args:
        request: an HttpRequest
        pk: an `Alteration` id
    """
    if SESSION_ALTERATION_IDS not in request.session:
        request.session[SESSION_ALTERATION_IDS] = [str(pk)]
    else:
        request.session[SESSION_ALTERATION_IDS].append(str(pk))
        request.session.modified = True


def set_verified_email(request: HttpRequest, email: str) -> None:
    """Store a verified email in the user's session.

    Args:
        request: an HttpRequest
        email: an email address
    """
    request.session[SESSION_VERIFIED_EMAIL] = email


def verified_email(request: HttpRequest) -> str:
    """A validated email for the current user.

    Value is set by the `assistant_email_verification` view.

    Args:
        request: an HttpRequest

    Returns:
        A verified email address or an empty string if no email has been verified or if
        the verified email has been blocked meanwhile
    """
    from .models import BlockList

    email = request.session.get(SESSION_VERIFIED_EMAIL)
    if not email or BlockList.is_blocked(email):
        return ""
    return email


def requestors_restricted(view_func):
    """A decorator to protect views from unauthorized access.

    Requires a view with a `pk` keyword argument matching an `Alteration` id.
    The wrapper checks if the current user has access it or send a redirect to the
    `alteration_access` view.
    """

    @wraps(view_func)
    def wrap(request: HttpRequest, *args, **kwargs):
        pk = kwargs["pk"]
        if has_access(request, pk):
            return view_func(request, *args, **kwargs)
        else:
            messages.warning(request, _("Access to this page is restricted."))
            return redirect("alteration-access", pk=pk)

    return wrap


def generate_origin_changelog(old_url: str, old_values: dict[str, Any]) -> str:
    """Generate a short changelog after updating an Origin.

    Args:
        old_url: the original origin url
        old_values: the list of changed fields (e.g. Form.changed_data)

    Returns:
        A text describing the changes
    """
    return (
        generate_changelog(
            Origin(**old_values),
            _("Origin %(url)s was modified, changes:" % {"url": old_url}),
            old_values,
        )
        if old_values
        else ""
    )


def generate_alteration_changelog(old_values: dict[str, Any]) -> str:
    """Generate a short changelog after updating an Alteration.

    Args:
        old_values: the list of changed fields (e.g. Form.changed_data)

    Returns:
        A text describing the changes
    """
    return (
        generate_changelog(
            Alteration(**old_values),
            _("Alteration request was modified, changes:"),
            old_values,
        )
        if old_values
        else ""
    )


def generate_changelog(
    instance: Alteration | Origin, introduction: str, old_values: dict[str, Any]
) -> str:
    """Generic changelog generator.

    Args:
        instance: a model instance
        introduction: a sentence introducing the changes
        old_values: a dict of changed values (field: old value)

    Returns:
        A text listing the fields impacted and their previous values
    """
    parts = [introduction]
    for fieldname, value in old_values.items():
        label = getattr(type(instance), fieldname).field.verbose_name
        display_method = f"get_{fieldname}_display"  # available on choice fields
        if hasattr(instance, display_method):
            value = getattr(instance, display_method)()

        parts.append(f"- {label}: {value}")
    return "\n".join(parts)


def process_state(request) -> ProcessState:
    """Describe the alteration request process state.

    The alteration request assistant is a multi-step form, where the user is able to
    go back and forward in the process as long as required data has been filled.

    This method builds a dict of each steps as keys (email verification, category
    chooser, etc.) and step state as values (url, current active step or not, available
    step or not) using session vars & `request` path.

    Args:
        request: an ``HttpRequest``

    Returns:
        The alteration request process state
    """

    steps: ProcessState = {}

    for name in STEPS_NAMES:
        url = reverse(f"alteration-{name}")
        active = True if url == request.path else False
        disabled = False if f"alteration_{name}" in request.session else True
        steps[name] = Step(url, active, disabled)
    return steps


def redirect_to_step(request, current_step: str) -> Optional[HttpResponse]:
    """Redirect the user to the proper step.

    Prevent a user skipping steps in the process. It redirects the user to the first
    missing step of the form (ie. you try to access /reasons before choosing a category
    you are redirected to /category) and displays a message to explain why.

    Args:
        request: an ``HttpRequest``
        current_step: the name of current step

    Returns:
        A redirect to a previous step if some data is missing
    """
    warnings = {
        "email": _(
            "Please confirm your email address before accessing the alteration "
            "request form."
        ),
        "category": _("Please choose a category for your alteration request."),
        "origins": _("Please select origins for your alteration request."),
        "reasons": _("Please fill the reasons for your alteration request."),
    }
    previous_steps = list(itertools.takewhile(lambda s: s != current_step, STEPS_NAMES))
    steps = process_state(request)
    for name in previous_steps:
        if steps[name].disabled:  # a disabled step has not been filled
            messages.warning(request, warnings[name])
            return redirect(steps[name].url)
    return None


def cleanup_session(request: HttpRequest) -> None:
    """Remove alteration request details from the session.

    Called after creating the Alteration request in the db, all sessions keys starting
    with `alteration_` are deleted, except `alteration_email`.

    Args:
        request: an ``HttpRequest``
    """
    to_remove = [
        key
        for key in request.session.keys()
        if key.startswith("alteration_") and key != "alteration_email"
    ]
    for key in to_remove:
        request.session.pop(key)


def tunnel_step(current_step: str):
    """A decorator to forbid skipping steps in the alteration request tunnel.

    The user will be redirect to the first missing step before `current_step`.

    Args:
        current_step: the name of the current step
    """

    def factory(view_func):
        @wraps(view_func)
        def wrap(request: HttpRequest, *args, **kwargs):
            if redirect_ := redirect_to_step(request, current_step):
                return redirect_
            return view_func(request, *args, **kwargs)

        return wrap

    return factory
