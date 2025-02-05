# Copyright (C) 2025  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import pytest
from pytest_django.asserts import (
    assertContains,
    assertNotContains,
    assertRedirects,
    assertTemplateUsed,
)

from django.conf import settings
from django.core.paginator import Page
from django.forms.models import model_to_dict as dj_model_to_dict
from django.utils import timezone

from swh.web.alter.forms import (
    INITIALS_REASONS,
    AlterationAccessForm,
    AlterationAdminForm,
    AlterationForm,
    AlterationSearchForm,
    ConfirmationForm,
    EmailVerificationForm,
    MessageAdminForm,
    MessageForm,
    OriginAdminForm,
    OriginSearchForm,
    OriginSelectForm,
    ReasonsForm,
)
from swh.web.alter.models import (
    Alteration,
    AlterationCategory,
    AlterationStatus,
    EventRecipient,
    OriginOutcome,
    OriginOwnership,
    Token,
)
from swh.web.alter.utils import (
    SESSION_ALTERATION_IDS,
    SESSION_VERIFIED_EMAIL,
    has_access,
    verified_email,
)
from swh.web.tests.helpers import check_html_get_response, check_html_post_response
from swh.web.utils import reverse


@pytest.fixture
def _session_step0(client, db):
    session = client.session
    session[SESSION_VERIFIED_EMAIL] = "mh@m.it"
    session.save()


@pytest.fixture
def _session_step1(client, _session_step0):
    session = client.session
    session["alteration_category"] = AlterationCategory.COPYRIGHT
    session.save()


@pytest.fixture
def _session_step2(client, _session_step1):
    session = client.session
    session["alteration_origins"] = [
        "http://example.org/username/django",
        "http://example.org/username/flask",
    ]
    session.save()


@pytest.fixture
def _session_step3(client, _session_step2):
    session = client.session
    session["alteration_reasons"] = "My reasons"
    session["alteration_expected_outcome"] = "My expected outcome"
    session.save()


@pytest.fixture
def _session_access(client, alteration):
    session = client.session
    session[SESSION_ALTERATION_IDS] = [str(alteration.pk)]
    session.save()


@pytest.fixture
def admin_client(client, alter_admin):
    client.force_login(alter_admin)
    return client


def model_to_dict(instance, fields=None, exclude=None):
    """Return a dict containing the data in ``instance``

    This calls django's `model_to_dict` and then removes None values from the dict to
    avoid TypeError when POSTing data with the TestClient.
    """
    data = dj_model_to_dict(instance, fields, exclude)
    return {k: v for k, v in data.items() if v is not None}


def test_content_policies_unverified_email(client):
    response = check_html_get_response(
        client,
        reverse("content-policies"),
        status_code=200,
        template_used="content_policies.html",
    )
    assert response.context["next_step"] == "alteration-email"
    assertContains(response, reverse("alteration-email"))


@pytest.mark.django_db
def test_content_policies_verified_email(client):
    session = client.session
    session[SESSION_VERIFIED_EMAIL] = "test@mail.local"
    session.save()
    response = check_html_get_response(
        client,
        reverse("content-policies"),
        status_code=200,
        template_used="content_policies.html",
    )
    assert response.context["next_step"] == "alteration-category"
    assertContains(response, reverse("alteration-category"))


def test_email(client):
    response = check_html_get_response(
        client,
        reverse("alteration-email"),
        status_code=200,
        template_used="assistant_email.html",
    )
    assert isinstance(response.context["form"], EmailVerificationForm)
    assert response.context["process"]["email"].active
    assertTemplateUsed(response, "includes/steps.html")


@pytest.mark.django_db
def test_email_post(client, mailoutbox):
    data = {"email": "test@mail.local"}
    response = check_html_post_response(
        client,
        reverse("alteration-email"),
        status_code=302,
        data=data,
    )
    assertRedirects(response, reverse("alteration-email"))
    assert len(mailoutbox) == 1
    message = mailoutbox[0]
    assert message.subject == "Please confirm your email address"


@pytest.mark.django_db
def test_email_verification(client):
    token = Token.create_for("test@mail.local")
    response = check_html_get_response(
        client,
        token.get_absolute_url(),
        status_code=302,
    )
    assertRedirects(response, reverse("alteration-category"))
    assert verified_email(response.wsgi_request) == "test@mail.local"


@pytest.mark.django_db
def test_email_verification_expired(client):
    token = Token.create_for("test@mail.local")
    token.expires_at = timezone.now()
    token.save()
    response = check_html_get_response(
        client,
        token.get_absolute_url(),
        status_code=302,
    )
    assertRedirects(response, reverse("alteration-email"))
    assert not verified_email(response.wsgi_request)


def test_category_missing_email(client):
    response = client.get(reverse("alteration-category"))
    assertRedirects(response, reverse("alteration-email"))


def test_category(client, _session_step0):
    response = check_html_get_response(
        client,
        reverse("alteration-category"),
        status_code=200,
        template_used="assistant_category.html",
    )
    assert response.context["process"]["category"].active
    assertTemplateUsed(response, "includes/steps.html")


def test_category_post(client, _session_step0):
    response = check_html_post_response(
        client,
        reverse("alteration-category"),
        status_code=302,
        data={"category": AlterationCategory.COPYRIGHT},
    )
    assert response["location"] == reverse("alteration-origins")
    assert client.session["alteration_category"] == AlterationCategory.COPYRIGHT


def test_origins_missing_category(client, _session_step0):
    response = check_html_get_response(
        client, reverse("alteration-origins"), status_code=302
    )
    assert response["location"] == reverse("alteration-category")


def test_origins_context(client, _session_step1):
    context = check_html_get_response(
        client, reverse("alteration-origins"), status_code=200
    ).context
    assert isinstance(context["search_form"], OriginSearchForm)
    assert isinstance(context["origins_form"], OriginSelectForm)
    assert context["process"]["origins"].active
    assert not context["results"]
    assert not context["query"]


def test_origins_search(client, mocker, _session_step1):
    url = reverse("alteration-origins", query_params={"query": "username"})
    mocker.patch(
        "swh.web.alter.views.search_origin",
        return_value=(["http://example.org/username/repo"], None),
    )
    response = check_html_get_response(
        client,
        url,
        status_code=200,
        template_used="assistant_origins.html",
    )
    assert response.context["results"] == ["http://example.org/username/repo"]


def test_origins_post(client, origin, _session_step1):
    response = check_html_post_response(
        client,
        reverse("alteration-origins"),
        status_code=302,
        data={"urls": [origin["url"]]},
    )
    assertRedirects(response, reverse("alteration-reasons"))
    assert client.session["alteration_origins"] == [origin["url"]]


def test_reasons_without_origins(client, _session_step1):
    response = check_html_get_response(
        client, reverse("alteration-reasons"), status_code=302
    )
    assert response["location"] == reverse("alteration-origins")


def test_reasons(client, _session_step2):
    response = check_html_get_response(
        client,
        reverse("alteration-reasons"),
        status_code=200,
        template_used="assistant_reasons.html",
    )
    form = response.context["form"]
    assert isinstance(form, ReasonsForm)
    # form fields are pre-filed with text depending on the Alteration category
    assert (
        form.initial["reasons"]
        == INITIALS_REASONS[AlterationCategory.COPYRIGHT]["reasons"]
    )
    assert (
        form.initial["expected_outcome"]
        == INITIALS_REASONS[AlterationCategory.COPYRIGHT]["expected_outcome"]
    )
    assert response.context["process"]["reasons"].active
    assertTemplateUsed(response, "includes/steps.html")


def test_reasons_post(client, _session_step2):
    response = check_html_post_response(
        client,
        reverse("alteration-reasons"),
        status_code=302,
        data={"reasons": "My reasons", "expected_outcome": "My expected outcome"},
    )
    assertRedirects(response, reverse("alteration-summary"))
    assert client.session["alteration_reasons"] == "My reasons"
    assert client.session["alteration_expected_outcome"] == "My expected outcome"


def test_summary(client, _session_step3):
    response = check_html_get_response(
        client,
        reverse("alteration-summary"),
        status_code=200,
        template_used="assistant_summary.html",
    )
    form = response.context["form"]
    assert isinstance(form, ConfirmationForm)
    # all session values must be found in the summary
    values = [v for v in client.session.values() if not isinstance(v, list)]
    values += client.session["alteration_origins"]
    for value in values:
        assertContains(response, value)
    assert response.context["process"]["summary"].active
    assertTemplateUsed(response, "includes/steps.html")


def test_summary_without_reasons(client, _session_step2):
    response = client.get(reverse("alteration-summary"))
    assertRedirects(response, reverse("alteration-reasons"))


@pytest.mark.django_db
def test_summary_post(client, _session_step3):
    response = check_html_post_response(
        client,
        reverse("alteration-summary"),
        status_code=302,
        data={"confirm": True},
    )
    # An Alteration request has been created
    alteration = Alteration.objects.get(email="mh@m.it")
    assertRedirects(response, alteration.get_absolute_url())
    # a session var has been added to authorize current browser
    has_access(response.wsgi_request, alteration.pk)
    # Other session vars have been deleted
    remaining_keys = [
        k
        for k in client.session.keys()
        if k.startswith("alteration_")
        and k != SESSION_ALTERATION_IDS
        and k != SESSION_VERIFIED_EMAIL
    ]
    assert not remaining_keys


def test_details_is_protected(client, alteration):
    response = check_html_get_response(
        client,
        alteration.get_absolute_url(),
        status_code=302,
    )
    assertRedirects(response, reverse("alteration-access", {"pk": alteration.pk}))


def test_details(client, alteration, _session_access):
    response = check_html_get_response(
        client,
        alteration.get_absolute_url(),
        status_code=200,
        template_used="alteration_details.html",
    )
    context = response.context
    assert context["alteration"] == alteration
    assert len(context["events"]) == 1  # only one public event
    assert isinstance(context["message_form"], MessageForm)
    assert isinstance(context["alteration_form"], AlterationForm)
    for event in alteration.events.all():
        if event.internal:
            assertNotContains(response, event.content)
        else:
            assertContains(response, event.content)


def test_details_post(client, alteration, _session_access):
    data = model_to_dict(alteration)
    data["reasons"] = "My updated reasons"
    response = check_html_post_response(
        client,
        alteration.get_absolute_url(),
        status_code=302,
        data=data,
    )
    assertRedirects(response, alteration.get_absolute_url())
    alteration.refresh_from_db()
    assert alteration.reasons == "My updated reasons"
    event = alteration.events.first()
    assert event.author == "Requester"
    assert "reasons" in event.content


def test_message_protected(client, alteration):
    data = {"content": "Please block my whole namespace"}
    response = check_html_post_response(
        client,
        reverse("alteration-message", {"pk": alteration.pk}),
        status_code=302,
        data=data,
    )
    assertRedirects(response, reverse("alteration-access", {"pk": alteration.pk}))


def test_message_post(client, alteration, _session_access, mailoutbox):
    data = {"content": "Please block my whole namespace"}
    response = check_html_post_response(
        client,
        reverse("alteration-message", {"pk": alteration.pk}),
        status_code=302,
        data=data,
    )
    assertRedirects(response, alteration.get_absolute_url())
    event = alteration.events.first()
    assert event.content == "Please block my whole namespace"
    assert len(mailoutbox) == 1
    message = mailoutbox[0]
    assert message.subject == f"New message on {alteration}"


def test_access(client, alteration):
    response = check_html_get_response(
        client,
        reverse("alteration-access", {"pk": alteration.pk}),
        status_code=200,
        template_used="alteration_access.html",
    )
    assert isinstance(response.context["form"], AlterationAccessForm)


def test_access_post(client, alteration, mailoutbox):
    url = reverse("alteration-access", {"pk": alteration.pk})
    response = check_html_post_response(
        client, url, status_code=302, data={"email": alteration.email}
    )
    assertRedirects(response, url)
    assert len(mailoutbox) == 1
    message = mailoutbox[0]
    assert message.subject == "Access to your alteration request"


def test_access_post_wrong_email(client, alteration, mailoutbox):
    url = reverse("alteration-access", {"pk": alteration.pk})
    response = check_html_post_response(
        client, url, status_code=302, data={"email": f"wrong.{alteration.email}"}
    )
    assertRedirects(response, url)
    assert len(mailoutbox) == 0


def test_access_link(client, token):
    alteration = token.alteration
    response = check_html_get_response(
        client,
        token.get_absolute_url(),
        status_code=302,
    )
    assertRedirects(response, alteration.get_absolute_url())
    assert has_access(response.wsgi_request, alteration.pk)


def test_access_link_expired(client, alteration, token):
    token.expires_at = timezone.now()
    token.save()
    response = check_html_get_response(
        client,
        token.get_absolute_url(),
        status_code=302,
    )
    assertRedirects(response, reverse("alteration-access", {"pk": alteration.pk}))


def test_admin_dashboard_protected(client):
    response = check_html_get_response(
        client,
        reverse("alteration-dashboard"),
        status_code=302,
    )
    assert reverse(settings.LOGIN_URL) in response.headers["Location"]


@pytest.mark.django_db
def test_admin_dashboard(admin_client, alteration):
    response = check_html_get_response(
        admin_client,
        reverse("alteration-dashboard"),
        status_code=200,
        template_used="admin_dashboard.html",
    )
    context = response.context
    assert isinstance(context["form"], AlterationSearchForm)
    assert isinstance(context["page"], Page)
    assert alteration in context["page"]
    assertContains(response, str(alteration))


@pytest.mark.django_db
@pytest.mark.parametrize(
    "query,status,expected",
    [
        ("ZZZ", None, False),
        ("example.com", None, True),
        (None, AlterationStatus.VALIDATING, True),
    ],
)
def test_admin_dashboard_search(admin_client, alteration, query, status, expected):
    response = check_html_get_response(
        admin_client,
        reverse(
            "alteration-dashboard", query_params={"query": query, "status": status}
        ),
        status_code=200,
        template_used="admin_dashboard.html",
    )
    page = response.context["page"]
    if expected:
        assert alteration in page
    else:
        assert alteration not in page


def test_admin_alteration_protected(client, alteration):
    response = check_html_get_response(
        client,
        alteration.get_admin_url(),
        status_code=302,
    )
    assert reverse(settings.LOGIN_URL) in response.headers["Location"]


@pytest.mark.django_db
def test_admin_alteration(admin_client, alteration):
    response = check_html_get_response(
        admin_client,
        alteration.get_admin_url(),
        status_code=200,
        template_used="admin_alteration.html",
    )
    context = response.context
    assert context["alteration"] == alteration
    assert isinstance(context["alteration_form"], AlterationAdminForm)
    assert isinstance(context["message_form"], MessageAdminForm)
    assert isinstance(context["origin_create_form"], OriginAdminForm)
    assert len(context["origin_forms"]) == alteration.origins.count()
    origins = set()
    for form in context["origin_forms"]:
        origins.add(form.instance)
        assert isinstance(form, OriginAdminForm)
    assert origins == set(alteration.origins.all())
    for event in alteration.events.all():
        assertContains(response, event.content)


@pytest.mark.django_db
def test_admin_alteration_post(admin_client, alteration):
    data = model_to_dict(alteration)
    data["expected_outcome"] = "Takedown, block + mailmap"
    response = check_html_post_response(
        admin_client, alteration.get_admin_url(), status_code=302, data=data
    )
    assertRedirects(response, alteration.get_admin_url())
    alteration.refresh_from_db()
    assert alteration.expected_outcome == "Takedown, block + mailmap"


def test_admin_origin_protected(client, alteration):
    origin = alteration.origins.first()
    url = reverse(
        "alteration-origin-admin", {"alteration_pk": alteration.pk, "pk": origin.pk}
    )
    response = check_html_post_response(
        client, url, status_code=302, data=model_to_dict(origin)
    )
    assert reverse(settings.LOGIN_URL) in response.headers["Location"]


@pytest.mark.django_db
def test_admin_origin_post(admin_client, alteration):
    origin = alteration.origins.first()
    url = reverse(
        "alteration-origin-admin", {"alteration_pk": alteration.pk, "pk": origin.pk}
    )
    data = model_to_dict(origin)
    data["code_license"] = "CeCILL"
    response = check_html_post_response(admin_client, url, status_code=302, data=data)
    assertRedirects(response, alteration.get_admin_url())
    origin.refresh_from_db()
    assert origin.code_license == "CeCILL"


@pytest.mark.django_db
def test_admin_origin_create_post(admin_client, alteration, origin):
    url = reverse("alteration-origin-admin-create", {"alteration_pk": alteration.pk})
    data = {
        "url": origin["url"],
        "available": True,
        "outcome": OriginOutcome.VALIDATING,
        "ownership": OriginOwnership.UNKNOWN,
    }
    response = check_html_post_response(admin_client, url, status_code=302, data=data)
    assertRedirects(response, alteration.get_admin_url())
    assert alteration.origins.get(url=origin["url"]).available


def test_admin_message_protected(client, alteration):
    url = reverse("alteration-message-admin", {"pk": alteration.pk})
    data = {
        "recipient": EventRecipient.MANAGER,
        "internal": True,
        "content": "Please check this alteration request",
    }
    response = check_html_post_response(client, url, status_code=302, data=data)
    assert reverse(settings.LOGIN_URL) in response.headers["Location"]


@pytest.mark.django_db
def test_admin_message_post(admin_client, alter_admin, alteration):
    url = reverse("alteration-message-admin", {"pk": alteration.pk})
    data = {
        "recipient": EventRecipient.MANAGER,
        "internal": True,
        "content": "Please check this alteration request",
    }
    response = check_html_post_response(admin_client, url, status_code=302, data=data)
    assertRedirects(response, alteration.get_admin_url())
    event = alteration.events.first()
    assert event.author == alter_admin.username
    assert event.content == "Please check this alteration request"


def test_event_admin_protected(client, alteration):
    url = reverse(
        "alteration-event-admin",
        {"alteration_pk": alteration.pk, "pk": alteration.events.first().pk},
    )
    data = {"content": "Updated content"}
    response = check_html_post_response(client, url, status_code=302, data=data)
    assert reverse(settings.LOGIN_URL) in response.headers["Location"]


@pytest.mark.django_db
def test_event_admin_post(admin_client, alter_admin, alteration):
    url = reverse(
        "alteration-event-admin",
        {"alteration_pk": alteration.pk, "pk": alteration.events.first().pk},
    )
    data = {"content": "Updated content"}
    response = check_html_post_response(admin_client, url, status_code=302, data=data)
    assertRedirects(response, alteration.get_admin_url())
    event = alteration.events.first()
    assert event.content == "Updated content"
