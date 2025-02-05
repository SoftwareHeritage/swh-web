# Copyright (C) 2025  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from django_ratelimit.decorators import ratelimit

from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods

from swh.web.auth.utils import ALTER_ADMIN_PERMISSION
from swh.web.utils.archive import search_origin

from .emails import (
    send_alteration_confirmation,
    send_alteration_notification,
    send_message_notification,
)
from .forms import (
    INITIALS_REASONS,
    AlterationAccessForm,
    AlterationAdminForm,
    AlterationForm,
    AlterationSearchForm,
    CategoryForm,
    ConfirmationForm,
    EmailVerificationForm,
    EventAdminForm,
    MessageAdminForm,
    MessageForm,
    OriginAdminForm,
    OriginSearchForm,
    OriginSelectForm,
    ReasonsForm,
)
from .models import Alteration, Event, EventCategory, Origin, Token
from .utils import (
    cleanup_session,
    process_state,
    requestors_restricted,
    set_access,
    set_verified_email,
    tunnel_step,
    verified_email,
)

if TYPE_CHECKING:
    from uuid import UUID

    from django.http import HttpRequest, HttpResponse

    from swh.web.utils.typing import OriginInfo


@require_http_methods(["GET"])
def content_policies(request: HttpRequest) -> HttpResponse:
    """Display the archive content policies.

    If the user has already verified an email address the link to the alteration
    request assistant at the end of the page will lead to the `assistant_category`
    view and if not, to the `assistant_email_form` one.

    Args:
        request: an ``HttpRequest``

    Returns:
        Content policies
    """
    next_step = "alteration-category" if verified_email(request) else "alteration-email"
    return render(request, "content_policies.html", {"next_step": next_step})


@require_http_methods(["GET", "POST"])
@ratelimit(key="ip", rate="5/m")
def assistant_email(request: HttpRequest) -> HttpResponse:
    """Email verification.

    Step 0/4, before accessing the request assistant we need to make sure we're able to
    contact the Requester. This form will:
    1. verify the email has not been previously blocked
    2. send an email message containing a link to confirm the address is working

    Args:
        request: an ``HttpRequest``

    Returns:
        Email verification form or a redirect to `assistant_category`
    """
    if request.method == "POST":
        form = EmailVerificationForm(request.POST, request=request)
        if form.is_valid():
            email = form.cleaned_data["email"]
            messages.info(
                request,
                _(
                    "An email has been sent to %(email)s, please click the link it "
                    "contains to confirm your address."
                )
                % {"email": email},
            )
            return redirect("alteration-email")
    else:
        form = EmailVerificationForm(request=request)
    return render(
        request,
        "assistant_email.html",
        {"form": form, "process": process_state(request)},
    )


@require_http_methods(["GET"])
@ratelimit(key="ip", rate="20/m")
def assistant_email_verification(request: HttpRequest, value: str) -> HttpResponse:
    """Authorize access to the assistant through an access token.

    The ``assistant_email_form`` form sends a magic link to this view.
    If a token matching `value` exists and is still valid, a session value is set and
    the user is redirected to the ``assistant_category`` view.

    Args:
        request: an ``HttpRequest``
        value: an access ``Token`` value

    Returns:
        A redirection to the assistant if the token is still valid or to the
        ``assistant_email_form`` view if it has expired.
    """
    queryset = Token.objects.exclude(email__isnull=True)
    token: Token = get_object_or_404(queryset, value=value)
    if token.expired:
        messages.warning(
            request, _("This token has expired, please request a new one.")
        )
        return redirect("alteration-email")
    assert token.email is not None  # just to please mypy
    set_verified_email(request, token.email)
    messages.success(
        request,
        _(
            "Thanks, your email address %(email)s has been verified, you now have "
            "access to the alteration request form."
        )
        % {"email": token.email},
    )
    return redirect("alteration-category")


@require_http_methods(["GET", "POST"])
@tunnel_step("category")
def assistant_category(request: HttpRequest) -> HttpResponse:
    """Set the alteration category.

    Step 1/4.

    Args:
        request: an ``HttpRequest``

    Returns:
        A list of common alteration reasons to chose from.
    """
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            request.session["alteration_category"] = form.cleaned_data["category"]
            return redirect("alteration-origins")
    else:
        form = CategoryForm()

    return render(
        request,
        "assistant_category.html",
        {"form": form, "process": process_state(request)},
    )


@require_http_methods(["GET", "POST"])
@ratelimit(key="ip", rate="20/m")
@tunnel_step("origins")
def assistant_origins(request: HttpRequest) -> HttpResponse:
    """Origins selection.

    Step 2/4. A view used to build the list of Origins related to the user's alteration.
    Chosen Origins are then stored in the user's session.

    A `category` parameter set by the link clicked in the `alteration_category` view is
    needed to access this view, it is then stored in the session.

    This is a **really basic** "origin shopping cart" implementation, that only handles
    origins coming from a single search query.

    Args:
        request: an ``HttpRequest``

    Returns:
        The origins selection form or a redirect to ``alteration_category`` if no type
        is provided.
    """
    if request.method == "POST":
        origins_form = OriginSelectForm(request.POST)
        if origins_form.is_valid():
            request.session["alteration_origins"] = [
                url for url in origins_form.cleaned_data["urls"]
            ]
            return redirect("alteration-reasons")
        else:
            messages.error(request, _("One or more invalid origins were submitted."))
    else:
        origins_form = OriginSelectForm(
            initial={
                "urls": request.session.get("alteration_origins", []),
            }
        )

    # handle origin search query
    results: list[OriginInfo] = []
    if query := request.GET.get("query"):
        search_form = OriginSearchForm(request.GET)
        if search_form.is_valid():
            # TODO handle pagination w/ page_token or set the limit parameter to
            # something higher than 50 ?
            results, __ = search_origin(
                search_form.cleaned_data["query"], with_visit=True
            )
        else:
            messages.error(request, _("Please fix the errors indicated in the form."))
    else:
        search_form = OriginSearchForm()

    return render(
        request,
        "assistant_origins.html",
        {
            "search_form": search_form,
            "origins_form": origins_form,
            "results": results,
            "query": query,
            "process": process_state(request),
        },
    )


@require_http_methods(["GET", "POST"])
@ratelimit(key="ip", rate="30/m")
@tunnel_step("reasons")
def assistant_reasons(request: HttpRequest) -> HttpResponse:
    """Alteration reasons and expected outcome.

    Step 3/4.

    Args:
        request: an ``HttpRequest``

    Returns:
        The reasons/outcome form.
    """
    if request.method == "POST":
        form = ReasonsForm(request.POST)
        if form.is_valid():
            request.session["alteration_reasons"] = form.cleaned_data["reasons"]
            request.session["alteration_expected_outcome"] = form.cleaned_data[
                "expected_outcome"
            ]
            return redirect("alteration-summary")
    else:
        # provide a template for reasons & outcome depending on the request category
        initials = INITIALS_REASONS[request.session["alteration_category"]]
        form = ReasonsForm(
            initial={
                "reasons": request.session.get(
                    "alteration_reasons", initials["reasons"]
                ),
                "expected_outcome": request.session.get(
                    "alteration_expected_outcome", initials["expected_outcome"]
                ),
            }
        )
    return render(
        request,
        "assistant_reasons.html",
        {"form": form, "process": process_state(request)},
    )


@require_http_methods(["GET", "POST"])
@ratelimit(key="ip", rate="10/m")
@tunnel_step("summary")
def assistant_summary(request: HttpRequest) -> HttpResponse:
    """Alteration request summary.

    Step 4/4.

    Args:
        request: an ``HttpRequest``

    Returns:
        A summary of previous steps and a confirmation form.
    """
    if request.method == "POST":
        form = ConfirmationForm(request.POST)
        if form.is_valid():
            # TODO catch exceptions
            alteration = Alteration.create_from_assistant(request.session)
            send_alteration_confirmation(alteration, request)
            send_alteration_notification(alteration, request)
            Event.objects.create(
                alteration=alteration,
                category=EventCategory.LOG,
                content=_("Email notifications sent."),
                internal=False,
            )
            # confirmation message
            messages.success(
                request,
                _(
                    "Your alteration request has been received and will be processed "
                    "as soon as possible. You will also receive a confirmation "
                    "message in your mailbox containing a link to this page."
                ),
            )
            cleanup_session(request)
            # Authorize current browser & redirect to the alteration_details view
            set_access(request, alteration.pk)
            return redirect(alteration)
    else:
        form = ConfirmationForm()

    return render(
        request,
        "assistant_summary.html",
        {"form": form, "process": process_state(request)},
    )


@require_http_methods(["GET", "POST"])
@requestors_restricted
@ratelimit(key="ip", rate="60/m")
def alteration_details(request: HttpRequest, pk: UUID) -> HttpResponse:
    """Alteration request details.

    This is the primary interface for the Requester to track and manage its alteration
    request.

    This view is protected by a session variable which is set when the user passes the
    ``alteration_access`` check.

    Args:
        request: an ``HttpRequest``
        pk: an ``Alteration`` identifier

    Returns:
        Alteration detail
    """
    alteration = get_object_or_404(Alteration, pk=pk)
    message_form = MessageForm(alteration=alteration)
    if request.method == "POST" and not alteration.is_read_only:
        alteration_form = AlterationForm(
            request.POST, author="Requester", instance=alteration
        )
        if alteration_form.is_valid():
            alteration_form.save()
            messages.success(request, _("Your alteration request has been updated."))
            return redirect(alteration)
    else:
        alteration_form = AlterationForm(instance=alteration)
    return render(
        request,
        "alteration_details.html",
        {
            "alteration": alteration,
            "message_form": message_form,
            "alteration_form": alteration_form,
            "events": alteration.events(manager="public_objects").all(),
        },
    )


@require_http_methods(["POST"])
@requestors_restricted
@ratelimit(key="ip", rate="20/m")
def alteration_message(request: HttpRequest, pk: UUID) -> HttpResponse:
    """Send a message for a ``Alteration``.

    Args:
        request: an ``HttpRequest``
        pk: an ``Alteration`` identifier

    Returns:
        A redirection to the alteration detail view
    """
    alteration = get_object_or_404(Alteration, pk=pk)

    form = MessageForm(request.POST, alteration=alteration)
    if form.is_valid():
        event = form.save()
        send_message_notification(event, request)
        messages.success(request, _("Message sent"))
    return redirect(alteration)


@require_http_methods(["GET", "POST"])
@ratelimit(key="ip", rate="20/m")
def alteration_access(request: HttpRequest, pk: UUID) -> HttpResponse:
    """Alteration security check.

    Security check before accessing a ``Alteration``.

    Args:
        request: an ``HttpRequest``
        pk: an ``Alteration`` identifier

    Returns:
        A alteration security form
    """
    alteration = get_object_or_404(Alteration, pk=pk)

    if request.method == "POST":
        form = AlterationAccessForm(
            request.POST, alteration=alteration, request=request
        )
        if form.is_valid():
            messages.info(
                request,
                _(
                    "If your email address matches the one found in this alteration "
                    "request you will soon receive a message containing a magic link "
                    "to access it."
                ),
            )
            return redirect("alteration-access", pk=pk)
    else:
        form = AlterationAccessForm(alteration=alteration, request=request)

    return render(
        request,
        "alteration_access.html",
        {"form": form},
    )


@require_http_methods(["GET"])
@ratelimit(key="ip", rate="20/m")
def alteration_link(request: HttpRequest, value: str) -> HttpResponse:
    """Authorize access to an alteration request through an access token.

    The ``alteration_access`` form sends a magic link to this view. If a token matching
    `value` exists and is still valid, a session value is set and the user is
    redirected to its alteration request.

    Args:
        request: an ``HttpRequest``
        value: an access ``Token`` value

    Returns:
        A redirection to an alteration request if the token is still valid or
        to the ``alteration_access`` view if it has expired.
    """
    queryset = Token.objects.exclude(alteration__isnull=True)
    token: Token = get_object_or_404(queryset, value=value)

    alteration = token.alteration
    assert alteration is not None  # just to please mypy

    if token.expired:
        messages.warning(
            request, _("This token has expired, please request a new link.")
        )
        return redirect("alteration-access", pk=alteration.pk)

    set_access(request, alteration.pk)
    messages.info(
        request, _("You now have access to this alteration request with this browser.")
    )
    return redirect(alteration)


@require_http_methods(["GET"])
@permission_required(ALTER_ADMIN_PERMISSION)
def admin_dashboard(request: HttpRequest) -> HttpResponse:
    """Alteration admin dashboard.

    List and search alteration requests.

    Args:
        request: an ``HttpRequest``

    Returns:
        A list of alterations
    """
    form = AlterationSearchForm(request.GET, initial={"query": "", "page": 1})
    form.full_clean()
    page = form.search()
    return render(
        request,
        "admin_dashboard.html",
        {
            "page": page,
            "form": form,
        },
    )


@require_http_methods(["GET", "POST"])
@permission_required(ALTER_ADMIN_PERMISSION)
def admin_alteration(request: HttpRequest, pk: UUID) -> HttpResponse:
    """Manage an alteration.

    Args:
        request: an ``HttpRequest``
        pk: an ``Alteration`` identifier

    Returns:
        A alteration administration form.
    """
    alteration = get_object_or_404(Alteration, pk=pk)
    author = request.user.get_username()
    origin_forms = [
        OriginAdminForm(instance=origin) for origin in alteration.origins.all()
    ]
    message_form = MessageAdminForm(alteration=alteration, author=author)
    event_forms = [EventAdminForm(instance=event) for event in alteration.events.all()]
    if request.method == "POST":
        alteration_form = AlterationAdminForm(
            request.POST, author=author, instance=alteration
        )
        if alteration_form.is_valid():
            alteration_form.save()
            messages.success(
                request,
                _("Request %(alteration)s has been updated")
                % {"alteration": alteration},
            )
            return redirect(alteration.get_admin_url())
        else:
            messages.error(
                request,
                _("Request %(alteration)s has not been updated due to %(errors)s")
                % {"alteration": alteration, "errors": alteration_form.errors},
            )
    else:
        alteration_form = AlterationAdminForm(instance=alteration)

    return render(
        request,
        "admin_alteration.html",
        {
            "alteration": alteration,
            "origin_forms": origin_forms,
            "event_forms": event_forms,
            "alteration_form": alteration_form,
            "message_form": message_form,
            "origin_create_form": OriginAdminForm(),
        },
    )


@require_http_methods(["POST"])
@permission_required(ALTER_ADMIN_PERMISSION)
def admin_origin(
    request: HttpRequest, alteration_pk: UUID, pk: Optional[UUID] = None
) -> HttpResponse:
    """Origin admin.

    Only admins are allowed to create or modify an origin.

    Args:
        request: an ``HttpRequest``
        alteration_pk: a ``Alteration`` identifier
        pk: an ``Origin`` identifier, if set this is an update request

    Returns:
        A redirection to the alteration admin view
    """
    if pk:
        origin = get_object_or_404(Origin, pk=pk, alteration_id=alteration_pk)
    else:
        origin = Origin(alteration_id=alteration_pk)
    form = OriginAdminForm(request.POST, request=request, instance=origin)
    if form.is_valid():
        form.save()
        msg = (
            _("Origin %(origin)s has been updated") % {"origin": origin}
            if pk
            else _("Origin %(origin)s has been created") % {"origin": origin}
        )
        messages.success(request, msg)
    else:
        messages.error(
            request,
            _("Origin %(origin)s has not been updated due to %(errors)s")
            % {"origin": origin, "errors": form.errors},
        )
    return redirect(origin.alteration.get_admin_url())


@require_http_methods(["POST"])
@permission_required(ALTER_ADMIN_PERMISSION)
def admin_message(request: HttpRequest, pk: UUID) -> HttpResponse:
    """Send a message for an ``Alteration``.

    Args:
        request: an ``HttpRequest``
        pk: an ``Alteration`` identifier

    Returns:
        A redirection to the alteration admin view
    """
    alteration = get_object_or_404(Alteration, pk=pk)

    form = MessageAdminForm(
        request.POST, alteration=alteration, author=request.user.get_username()
    )
    if form.is_valid():
        event = form.save()
        send_message_notification(event, request)
        messages.success(request, _("Message sent"))
    else:
        for field, error_list in form.errors.items():
            errors = [str(error) for error in error_list]
            messages.error(
                request,
                _(
                    "Errors in field %(fieldname)s: %(errors)s"
                    % {"fieldname": field, "errors": ", ".join(errors)}
                ),
            )
    return redirect(alteration.get_admin_url())


@require_http_methods(["POST"])
@permission_required(ALTER_ADMIN_PERMISSION)
def admin_event(request: HttpRequest, alteration_pk: UUID, pk: UUID) -> HttpResponse:
    """Edit an event for an ``Alteration``.

    Args:
        request: an ``HttpRequest``
        pk: an ``Event`` identifier

    Returns:
        A redirection to the alteration admin view
    """
    event = get_object_or_404(Event, alteration_id=alteration_pk, pk=pk)

    form = EventAdminForm(request.POST, instance=event)
    if form.is_valid():
        event = form.save()
        messages.success(request, _("Event updated"))
    else:
        for field, error_list in form.errors.items():
            errors = [str(error) for error in error_list]
            messages.error(
                request,
                _(
                    "Errors in field %(fieldname)s: %(errors)s"
                    % {"fieldname": field, "errors": ", ".join(errors)}
                ),
            )
    return redirect(event.alteration.get_admin_url())
