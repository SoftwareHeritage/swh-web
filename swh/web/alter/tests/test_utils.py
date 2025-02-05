# Copyright (C) 2025  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import uuid

import pytest

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.messages import get_messages
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.urls import reverse

from swh.web.alter.models import AlterationStatus, BlockList
from swh.web.alter.utils import (
    generate_alteration_changelog,
    generate_origin_changelog,
    get_django_group_emails,
    get_group_emails,
    get_keycloak_group_emails,
    has_access,
    process_state,
    redirect_to_step,
    set_access,
    set_verified_email,
    verified_email,
)


def attach_middlewares(request):
    """Pass the request through the session & messages middlewares."""
    for middleware in SessionMiddleware, MessageMiddleware:
        m = middleware(lambda x: None)
        m.process_request(request)


@pytest.mark.parametrize("uses_keycloak", [True, False])
def test_get_group_emails(settings, mocker, uses_keycloak):
    settings.SWH_AUTH_SERVER_URL = uses_keycloak
    mocker.patch("swh.web.alter.utils.get_django_group_emails", return_value=False)
    mocker.patch("swh.web.alter.utils.get_keycloak_group_emails", return_value=True)
    assert get_group_emails("test") == uses_keycloak


@pytest.mark.django_db
def test_get_django_group_emails():
    group = Group.objects.create(name="Baroque")
    for name in ["michael", "steve"]:
        user = get_user_model().objects.create_user(name, f"{name}@left.banke")
        group.user_set.add(user)
    user = get_user_model().objects.create_user("paul", "paul@beatl.es")
    assert get_django_group_emails(group.name) == [
        "michael@left.banke",
        "steve@left.banke",
    ]


def test_get_keycloak_group_emails(settings):
    settings.ALTER_SETTINGS = {"test_mail_alias": "alter-test@instance"}
    assert get_keycloak_group_emails("test") == ["alter-test@instance"]


def test_has_and_set_access(rf):
    request = rf.get("/alteration")
    middleware = SessionMiddleware(lambda x: None)
    middleware.process_request(request)
    pk = uuid.uuid4()
    assert not has_access(request, pk)
    set_access(request, pk)
    assert has_access(request, pk)


def test_generate_origin_changelog():
    old_values = {
        "code_license": "MIT",
        "outcome": "previous outcome",
        "reason": "previous reason",
    }
    changelog = generate_origin_changelog("http://test.url", old_values)
    assert "- outcome: previous outcome\n" in changelog
    assert "- license found in code: MIT\n" in changelog
    assert "- reason for this outcome: previous reason" in changelog
    assert "http://test.url" in changelog


def test_generate_alteration_changelog():
    old_values = {
        "status": AlterationStatus.CLOSED,
        "email": "test@mail.localhost",
        "expected_outcome": "previous outcome",
    }
    changelog = generate_alteration_changelog(old_values)
    assert "- status: Closed\n" in changelog
    assert "- requester's email: test@mail.localhost\n" in changelog
    assert "- expected outcome: previous outcome" in changelog


@pytest.mark.django_db
def test_set_verified_email(rf):
    request = rf.get("/alteration")
    attach_middlewares(request)
    assert not verified_email(request)
    set_verified_email(request, "test@mail.localhost")
    assert verified_email(request) == "test@mail.localhost"


@pytest.mark.django_db
def test_verified_email_blocked(rf):
    request = rf.get("/alteration")
    attach_middlewares(request)
    set_verified_email(request, "test@mail.localhost")
    BlockList.objects.create(email_or_domain="test@mail.localhost")
    assert not verified_email(request)


@pytest.mark.parametrize(
    "path,expected_active_step",
    [
        ("/alteration/email/", "email"),
        ("/alteration/category/", "category"),
        ("/alteration/origins/", "origins"),
        ("/alteration/reasons/", "reasons"),
        ("/alteration/summary/", "summary"),
    ],
)
def test_process_state_active(rf, path, expected_active_step):
    request = rf.get(path)
    attach_middlewares(request)
    state = process_state(request)
    for step, step_state in state.items():
        assert step_state.active == (step == expected_active_step)


@pytest.mark.parametrize(
    "session_steps,expected_disabled_steps",
    [
        ([], ["email", "category", "origins", "reasons", "summary"]),
        (["email", "category", "origins"], ["reasons", "summary"]),
    ],
)
def test_process_state_disabled(rf, session_steps, expected_disabled_steps):
    request = rf.get("/")
    attach_middlewares(request)
    for name in session_steps:
        request.session[f"alteration_{name}"] = "test"
    state = process_state(request)
    disabled_steps = [step for step, step_state in state.items() if step_state.disabled]
    assert disabled_steps == expected_disabled_steps


@pytest.mark.parametrize(
    "session_steps,current_step,expected_redirection",
    [
        ([], "reasons", "email"),
        ([], "email", None),
        (["email", "category"], "summary", "origins"),
        (["email", "category", "origins", "reasons"], "summary", None),
    ],
)
def test_redirect_to_step(rf, session_steps, current_step, expected_redirection):
    request = rf.get("/")
    attach_middlewares(request)
    for name in session_steps:
        request.session[f"alteration_{name}"] = "test"
    result = redirect_to_step(request, current_step)
    if expected_redirection:
        message = list(get_messages(request))[0]
        assert message.tags == "warning"
        assert result.url == reverse(f"alteration-{expected_redirection}")
    else:
        assert result is None
