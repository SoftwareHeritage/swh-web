# Copyright (C) 2025  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import pytest

from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.utils import timezone

from swh.web.alter.models import (
    Alteration,
    AlterationCategory,
    AlterationStatus,
    BlockList,
    Event,
    EventCategory,
    Origin,
    Token,
    validate_email_or_domain,
)


def test_origin_str(alteration):
    origin = alteration.origins.first()
    assert str(origin) == origin.url


def test_origin_admin_url(alteration):
    origin = alteration.origins.first()
    assert (
        origin.get_admin_url()
        == f"/admin/alteration/{alteration.pk}/origin/{origin.pk}/"
    )


def test_unique_origin(alteration):
    origin = alteration.origins.first()
    with pytest.raises(IntegrityError, match="unique_url"):
        Origin.objects.create(url=origin.url, alteration=alteration)


def test_alteration_search(db):
    requesters = [
        ("dona@gmail.com", "http://github.com/centipede"),
        ("bug@mark.two", "http://gitlab.com/cobol"),
        ("switched@on.bach", "http://gitlab.com/moog"),
    ]
    for email, url in requesters:
        alteration = Alteration.objects.create(
            reasons="Reasons",
            expected_outcome="takedown everything",
            email=email,
        )
        Origin.objects.create(url=url, alteration=alteration)

    bailey = Alteration.objects.search("gmail")  # matches by email
    assert bailey.count() == 1
    assert bailey.first().email == "dona@gmail.com"

    gitlab = Alteration.objects.search("GitLab")  # matches by origin url
    assert gitlab.count() == 2

    outcome = Alteration.objects.search("takedown")  # matches by outcome
    assert outcome.count() == 3

    nothing = Alteration.objects.search("ZZZ")  # matches nothing
    assert nothing.count() == 0


def test_alteration_admin_url(alteration):
    assert alteration.get_admin_url() == f"/admin/alteration/{alteration.pk}/"


def test_alteration_absolute_url(alteration):
    assert alteration.get_absolute_url() == f"/alteration/{alteration.pk}/"


def test_alteration_create_from_assistant(client, db):
    session = client.session
    session["alteration_category"] = AlterationCategory.COPYRIGHT
    session["alteration_reasons"] = "My reasons"
    session["alteration_expected_outcome"] = "Expected outcome"
    session["alteration_email"] = "my@email.address"
    session["alteration_origins"] = ["https://xerox.com/vlsi"]

    alteration = Alteration.create_from_assistant(session)

    assert alteration.category == AlterationCategory.COPYRIGHT
    assert alteration.reasons == "My reasons"
    assert alteration.expected_outcome == "Expected outcome"
    assert alteration.email == "my@email.address"
    origins = [o.url for o in alteration.origins.all()]
    assert origins == ["https://xerox.com/vlsi"]

    assert alteration.events.count() == 1
    event = alteration.events.first()

    assert event.category == EventCategory.LOG
    assert event.author == "Requester"
    assert "created" in event.content
    assert not event.internal


def test_alteration_ro(alteration):
    for status in AlterationStatus:
        alteration.status = status
        if status == AlterationStatus.ARCHIVED:
            assert alteration.is_read_only
        else:
            assert not alteration.is_read_only


def test_alteration_str(alteration):
    assert alteration.get_category_display() in str(alteration)
    assert alteration.email in str(alteration)


def test_event_public_manager(alteration, message_event, admin_message_event):
    assert alteration.events.count() == 4  # 2 logs + 2 messages
    assert Event.public_objects.filter(alteration=alteration).count() == 2
    assert Event.public_objects.filter(alteration=alteration).first() == message_event


def test_event_str(admin_message_event):
    assert admin_message_event.get_category_display() in str(admin_message_event)
    assert admin_message_event.author in str(admin_message_event)
    assert str(admin_message_event.alteration) in str(admin_message_event)


def test_alteration_token_absolute_url(token):
    assert token.get_absolute_url() == f"/alteration/link/{token.value}/"


def test_token_unique(token):
    alteration = Alteration.objects.create(
        reasons="Other reasons",
        expected_outcome="takedown",
        email="jm@email.address",
    )
    with pytest.raises(IntegrityError, match="unique_token_value"):
        Token.objects.create(value=token.value, alteration=alteration)


def test_token_create_for_alteration(alteration):
    token = Token.create_for(alteration)
    assert token.alteration == alteration
    assert token.email is None


@pytest.mark.django_db
def test_token_create_for_email():
    token = Token.create_for("test@email.local")
    assert token.email == "test@email.local"
    assert token.alteration is None


@pytest.mark.django_db
def test_token_create_for_something_else():
    with pytest.raises(ValueError, match="Invalid parameter"):
        Token.create_for(123)


@pytest.mark.django_db
def test_email_token_absolute_url():
    token = Token.create_for("test@email.local")
    assert token.get_absolute_url() == f"/alteration/email/verification/{token.value}/"


def test_token_expired(token):
    assert not token.expired
    token.expires_at = timezone.now()
    assert token.expired


@pytest.mark.skip(
    reason="FIXME: can't find a way to patch Token.value's default method"
)
def test_token_create_for_exc(alteration, token, mocker):
    # side_effect = [token.value] * 5
    # mocker.patch(
    #     "swh.web.alter.models._default_token_value",
    #     side_effect=side_effect,
    # )
    # Token.value.field.default = mocker.Mock(side_effect=side_effect)
    # mocker.patch(
    #     "swh.web.alter.models.Token.value.field.default",
    #     side_effect=side_effect,
    # )
    with pytest.raises(IntegrityError, match="after 5 attempts"):
        Token.create_for_alteration(alteration)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "value,expected_failure",
    [
        ("email@domain.localhost", False),
        ("domain.localhost", False),
        ("email@", True),
        ("localhost.%", True),
    ],
)
def test_validate_email_or_domain(value, expected_failure):
    if expected_failure:
        with pytest.raises(ValidationError):
            validate_email_or_domain(value)
    else:
        try:
            validate_email_or_domain(value)
        except ValidationError:
            pytest.fail("Unexpected error")


@pytest.mark.django_db
def test_block_list_unique():
    BlockList.objects.create(email_or_domain="test.localhost")
    with pytest.raises(IntegrityError, match="unique_email_or_domain"):
        BlockList.objects.create(email_or_domain="test.localhost")


@pytest.mark.django_db
def test_block_list_is_blocked():
    BlockList.objects.create(email_or_domain="test.localhost")
    with pytest.raises(ValueError, match="Invalid"):
        BlockList.is_blocked("test.localhost")  # expects a valid email address
    assert BlockList.is_blocked("whatever@test.localhost")
    assert not BlockList.is_blocked("whatever@test.other")


@pytest.mark.django_db
def test_block_list_lowercased():
    block = BlockList.objects.create(email_or_domain="TEST.localhost")
    assert block.email_or_domain == "test.localhost"


@pytest.mark.django_db
def test_block_list_disposable(settings):
    from disposable_email_domains import blocklist

    disposable_domain = next(iter(blocklist))
    email = f"test@{disposable_domain}"
    settings.ALTER_SETTINGS["block_disposable_email_domains"] = False
    assert not BlockList.is_blocked(email)

    settings.ALTER_SETTINGS["block_disposable_email_domains"] = True
    assert BlockList.is_blocked(email)
