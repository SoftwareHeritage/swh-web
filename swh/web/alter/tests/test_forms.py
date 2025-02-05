# Copyright (C) 2025  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import pytest
from pytest_django.asserts import assertNumQueries

from django.forms.models import model_to_dict

from swh.web.alter.forms import (
    AlterationAccessForm,
    AlterationAdminForm,
    AlterationForm,
    AlterationSearchForm,
    EmailVerificationForm,
    EventAdminForm,
    MessageAdminForm,
    MessageForm,
    OriginAdminForm,
    OriginSelectForm,
)
from swh.web.alter.models import (
    AlterationStatus,
    BlockList,
    EventCategory,
    EventRecipient,
    Token,
)


def test_origin_select_form_ko(origin):
    data = {"urls": ["http://an.unknown.origin", origin["url"]]}
    form = OriginSelectForm(data)
    assert not form.is_valid()
    errors = form["urls"].errors
    assert len(errors) == 1
    assert "http://an.unknown.origin" in errors[0]


def test_origin_select_form_ok(origin):
    data = {"urls": [origin["url"]]}
    form = OriginSelectForm(data)
    assert form.is_valid()


def test_alteration_access_form_ok(alteration, mailoutbox, rf):
    assert alteration.tokens.count() == 0
    data = {"email": alteration.email}
    form = AlterationAccessForm(data, alteration=alteration, request=rf.get("/"))
    assert form.is_valid()
    assert len(mailoutbox) == 1
    message = mailoutbox[0]
    assert alteration.tokens.count() == 1
    token = alteration.tokens.first()
    assert token.get_absolute_url() in message.body


def test_alteration_access_form_ko(alteration, mailoutbox, rf):
    assert alteration.tokens.count() == 0
    data = {"email": "wrong@email.address"}
    form = AlterationAccessForm(data, alteration=alteration, request=rf.get("/"))
    assert form.is_valid()  # the form is still valid even if the email doesn't match
    assert len(mailoutbox) == 0
    assert alteration.tokens.count() == 0


def test_alteration_search_form(alteration):
    form = AlterationSearchForm({})
    assert form.is_valid()
    page = form.search()
    with assertNumQueries(1):  # related origins are fetched in a single query
        first_result = page.object_list.first()
        assert first_result == alteration
        assert first_result.origins == alteration.origins


@pytest.mark.parametrize(
    "query,status,expected_count",
    [
        ("ZZZ", AlterationStatus.VALIDATING, 0),
        ("requester", AlterationStatus.VALIDATING, 1),
        ("requester", AlterationStatus.CLOSED, 0),
        (None, AlterationStatus.VALIDATING, 1),
        (None, AlterationStatus.CLOSED, 0),
        ("requester", None, 1),
    ],
)
def test_alteration_search_form_filters(alteration, query, status, expected_count):
    data = {"query": query, "status": status}
    form = AlterationSearchForm(data)
    assert form.is_valid()
    page = form.search()
    assert page.object_list.count() == expected_count


def test_message_form_ok(alteration):
    previous_count = alteration.events.count()
    data = {"content": "My message", "internal": True}  # internal will be ignored
    form = MessageForm(data, alteration=alteration)
    assert form.is_valid()
    event = form.save()
    assert alteration.events.count() == previous_count + 1
    assert alteration.events.first() == event
    assert event.author == "Requester"
    assert event.category == EventCategory.MESSAGE
    assert event.recipient == EventRecipient.SUPPORT
    assert not event.internal
    assert event.content == "My message"


def test_message_form_ko(alteration):
    data = {"content": ""}
    form = MessageForm(data, alteration=alteration)
    assert not form.is_valid()


def test_message_admin_form_ok(alteration):
    previous_count = alteration.events.count()
    data = {
        "content": "My admin message",
        "internal": True,
        "recipient": EventRecipient.MANAGER,
    }
    form = MessageAdminForm(data, alteration=alteration, author="Admin")
    assert form.is_valid()
    event = form.save()
    assert alteration.events.count() == previous_count + 1
    assert alteration.events.first() == event
    assert event.author == "Admin"
    assert event.category == EventCategory.MESSAGE
    assert event.recipient == EventRecipient.MANAGER
    assert event.internal
    assert event.content == "My admin message"


def test_message_admin_form_internal_to_requestor(alteration):
    data = {
        "content": "Internal message to requester",
        "internal": True,
        "recipient": EventRecipient.REQUESTER,
    }
    form = MessageAdminForm(data, alteration=alteration, author="Admin")
    assert not form.is_valid()
    assert form["internal"].errors


def test_origin_admin_form(rf, alteration, staff_user):
    previous_count = alteration.events.count()
    request = rf.get("/admin/alteration")
    request.user = staff_user
    origin = alteration.origins.first()
    data = model_to_dict(origin)
    data["code_license"] = "to confuse"
    form = OriginAdminForm(data, instance=origin, request=request)
    assert form.is_valid()
    origin = form.save()
    assert origin.code_license == "to confuse"
    assert alteration.events.count() == previous_count + 1
    event = alteration.events.first()
    assert event.author == staff_user.username
    assert event.category == EventCategory.LOG
    assert not event.internal
    assert str(origin) in event.content
    assert "- license found in code: to confuse" in event.content


def test_origin_admin_form_no_change(alteration):
    previous_count = alteration.events.count()
    origin = alteration.origins.first()
    data = model_to_dict(origin)
    form = OriginAdminForm(data, instance=origin)
    assert form.is_valid()
    origin = form.save()
    assert alteration.events.count() == previous_count


def test_alteration_form(alteration):
    previous_count = alteration.events.count()
    data = model_to_dict(alteration)
    data["email"] = "new@email.address"  # will be ignored
    data["reasons"] = "new reasons"
    form = AlterationForm(data, author="Requester", instance=alteration)
    assert form.is_valid()
    alteration = form.save()
    assert alteration.email != "new@email.address"
    assert alteration.events.count() == previous_count + 1
    event = alteration.events.first()
    assert event.author == "Requester"
    assert event.category == EventCategory.LOG
    assert not event.internal
    assert "reasons: new reasons" in event.content
    assert "email" not in event.content


def test_alteration_form_no_change(alteration):
    previous_count = alteration.events.count()
    data = model_to_dict(alteration)
    form = AlterationForm(data, author="Requester", instance=alteration)
    assert form.is_valid()
    alteration = form.save()
    assert alteration.events.count() == previous_count


def test_admin_alteration_form(alteration):
    previous_count = alteration.events.count()
    data = model_to_dict(alteration)
    data["email"] = "new@email.address"
    form = AlterationAdminForm(data, author="Admin", instance=alteration)
    assert form.is_valid()
    alteration = form.save()
    assert alteration.email == "new@email.address"
    assert alteration.events.count() == previous_count + 1
    event = alteration.events.first()
    assert event.author == "Admin"
    assert event.category == EventCategory.LOG
    assert not event.internal
    assert "email" in event.content


@pytest.mark.django_db
def test_email_verification_form_ok(mailoutbox, rf):
    email = "test@email.address"
    assert not Token.objects.filter(email=email).exists()
    data = {"email": email}
    form = EmailVerificationForm(data, request=rf.get("/"))
    assert form.is_valid()

    assert Token.objects.filter(email=email).exists()
    assert len(mailoutbox) == 1
    message = mailoutbox[0]
    assert message.subject == "Please confirm your email address"


@pytest.mark.django_db
def test_email_verification_form_blocked(mailoutbox, rf):
    email = "test@email.address"
    BlockList.objects.create(email_or_domain=email)
    data = {"email": email}
    form = EmailVerificationForm(data, request=rf.get("/"))
    assert not form.is_valid()

    errors = form["email"].errors
    assert len(errors) == 1
    assert "has been blocked" in errors[0]

    assert len(mailoutbox) == 0
    assert not Token.objects.filter(email=email).exists()


def test_event_admin_form(alteration):
    event = alteration.events.first()
    data = model_to_dict(event)
    data["content"] = "new content"
    form = EventAdminForm(data, instance=event)
    assert form.is_valid()
    event = form.save()
    assert event.content == "new content"
