# Copyright (C) 2025  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information
from __future__ import annotations

from typing import TYPE_CHECKING

from django_bootstrap5.templatetags.django_bootstrap5 import (
    bootstrap_button,
    bootstrap_field,
)

from django import template
from django.urls import reverse
from django.utils.html import conditional_escape
from django.utils.safestring import SafeString, mark_safe

from swh.web.alter.models import AlterationStatus, OriginOutcome

if TYPE_CHECKING:
    from django.forms import Field


register = template.Library()


@register.filter
def status_badge(category: str, label: str) -> SafeString:
    tags = {
        AlterationStatus.VALIDATING.value: "info",
        AlterationStatus.REJECTED.value: "warning",
        AlterationStatus.PROCESSED.value: "success",
        AlterationStatus.CLOSED.value: "secondary",
        AlterationStatus.EXECUTING.value: "primary",
        AlterationStatus.PLANNING.value: "light",
        AlterationStatus.ARCHIVED.value: "dark",
    }
    return mark_safe(
        '<span class="badge text-bg-%s">%s</span>'
        % (tags.get(category, "secondary"), conditional_escape(label))
    )


@register.filter
def outcome_badge(outcome: str, label: str) -> SafeString:
    tags = {
        OriginOutcome.VALIDATING.value: "info",
        OriginOutcome.REJECTED.value: "warning",
        OriginOutcome.MAILMAP.value: "light",
        OriginOutcome.MASK.value: "secondary",
        OriginOutcome.TAKEDOWN.value: "primary",
        OriginOutcome.BLOCK.value: "dark",
    }
    return mark_safe(
        '<span class="badge text-bg-%s">%s</span>'
        % (tags.get(outcome, "secondary"), conditional_escape(label))
    )


@register.simple_tag(takes_context=True)
def absolute_url(context: dict, location: str, *args, **kwargs) -> str:
    """Build a _real_ absolute url to `location` (including host & port).

    Location could be a relative url or a view name (as in urls.py) which would then be
    `reverse` with args & kwargs.

    Usage:
        ```
        {% absolute_url 'my-route' pk=12345 %}
        {% absolute_url obj.get_absolute_url %}
        ```

    Args:
        context: a django template context
        location: a view name

        *args: args passed to `reverse`
        **kwargs: keyword args passed to `reverse`

    Returns:
        an absolute url to `location`
    """
    if not isinstance(location, str) or "/" not in location:
        location = reverse(location, args=args, kwargs=kwargs)
    if "request" in context:
        return context["request"].build_absolute_uri(location)
    return location


@register.simple_tag
def bootstrap_field_submit(
    field: Field,
    button_label: str,
) -> str:
    """A wrapper around django_bs5.bootstrap_field to make a field + submit addon.

    Args:
        field: a Form field
        button_label: submit button label

    Returns:
        A form input group with a field and an appended submit button
    """
    return bootstrap_field(
        field=field,
        addon_after=bootstrap_button(button_label, button_type="submit"),
        show_label=False,
        addon_after_class=None,
        success_css_class="",
    )
