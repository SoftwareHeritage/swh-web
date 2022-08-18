# Copyright (C) 2022 The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from datetime import datetime, timezone

import pytest

from django.core.exceptions import ValidationError

from swh.web.add_forge_now.apps import APP_LABEL

MIGRATION_0001 = "0001_initial"
MIGRATION_0002 = "0002_authorized_null_comment"
MIGRATION_0003 = "0003_request_submitter_forward_username"
MIGRATION_0005 = "0005_prepare_inbound_email"
MIGRATION_0006 = "0006_request_add_new_fields"
MIGRATION_0007 = "0007_rename_denied_request_status"
MIGRATION_0008 = "0008_turn_request_forge_url_into_url_field"


def now() -> datetime:
    return datetime.now(tz=timezone.utc)


def test_add_forge_now_initial_migration(migrator):
    """Basic migration test to check the model is fine"""

    state = migrator.apply_tested_migration((APP_LABEL, MIGRATION_0001))
    request = state.apps.get_model(APP_LABEL, "Request")
    request_history = state.apps.get_model(APP_LABEL, "RequestHistory")

    from swh.web.add_forge_now.models import RequestActorRole, RequestStatus

    date_now = now()

    req = request(
        status=RequestStatus.PENDING,
        submitter_name="dudess",
        submitter_email="dudess@orga.org",
        forge_type="cgit",
        forge_url="https://example.org/forge",
        forge_contact_email="forge@//example.org",
        forge_contact_name="forge",
        forge_contact_comment=(
            "Discovered on the main forge homepag, following contact link."
        ),
    )
    req.save()

    assert req.submission_date > date_now

    req_history = request_history(
        request=req,
        text="some comment from the moderator",
        actor="moderator",
        actor_role=RequestActorRole.MODERATOR,
        new_status=None,
    )
    req_history.save()
    assert req_history.date > req.submission_date

    req_history2 = request_history(
        request=req,
        text="some answer from the user",
        actor="user",
        actor_role=RequestActorRole.SUBMITTER,
        new_status=None,
    )
    req_history2.save()
    assert req_history2.date > req_history.date


def test_add_forge_now_allow_no_comment(migrator):
    """Basic migration test to check new model authorized empty comment"""

    from django.db.utils import IntegrityError

    state = migrator.apply_tested_migration((APP_LABEL, MIGRATION_0001))

    def make_request_with_empty_comment(requestModel):
        return requestModel(
            status="PENDING",
            submitter_name="dudess",
            submitter_email="dudess@orga.org",
            forge_type="cgit",
            forge_url="https://example.org/forge",
            forge_contact_email="forge@//example.org",
            forge_contact_name="forge",
            forge_contact_comment=None,
        )

    requestModel = state.apps.get_model(APP_LABEL, "Request")

    req = make_request_with_empty_comment(requestModel)
    with pytest.raises(IntegrityError, match="violates not-null constraint"):
        req.save()

    state = migrator.apply_tested_migration((APP_LABEL, MIGRATION_0002))
    requestModel2 = state.apps.get_model(APP_LABEL, "Request")

    req2 = make_request_with_empty_comment(requestModel2)
    req2.save()


def test_add_forge_now_store_submitter_forward_username(migrator):

    state = migrator.apply_tested_migration((APP_LABEL, MIGRATION_0002))
    requestModel = state.apps.get_model(APP_LABEL, "Request")
    assert not hasattr(requestModel, "submitter_forward_username")

    state = migrator.apply_tested_migration((APP_LABEL, MIGRATION_0003))
    requestModel2 = state.apps.get_model(APP_LABEL, "Request")

    assert hasattr(requestModel2, "submitter_forward_username")


def test_add_forge_now_add_new_fields_to_request(migrator):

    state = migrator.apply_tested_migration((APP_LABEL, MIGRATION_0005))
    Request = state.apps.get_model(APP_LABEL, "Request")
    RequestHistory = state.apps.get_model(APP_LABEL, "RequestHistory")
    assert not hasattr(Request, "last_moderator")
    assert not hasattr(Request, "last_modified_date")

    from swh.web.add_forge_now.models import RequestActorRole, RequestStatus

    req = Request(
        status=RequestStatus.PENDING,
        submitter_name="dudess",
        submitter_email="dudess@orga.org",
        forge_type="cgit",
        forge_url="https://example.org/forge",
        forge_contact_email="forge@//example.org",
        forge_contact_name="forge",
        forge_contact_comment=(
            "Discovered on the main forge homepag, following contact link."
        ),
    )
    req.save()

    req_history = RequestHistory(
        request=req,
        text="some comment from the submitter",
        actor="submitter",
        actor_role=RequestActorRole.SUBMITTER.name,
        new_status=None,
    )
    req_history.save()

    req_history = RequestHistory(
        request=req,
        text="some comment from the moderator",
        actor="moderator",
        actor_role=RequestActorRole.MODERATOR.name,
        new_status=None,
    )
    req_history.save()

    state = migrator.apply_tested_migration((APP_LABEL, MIGRATION_0006))
    Request = state.apps.get_model(APP_LABEL, "Request")
    RequestHistory = state.apps.get_model(APP_LABEL, "RequestHistory")

    assert hasattr(Request, "last_moderator")
    assert hasattr(Request, "last_modified_date")

    for request in Request.objects.all():
        history = RequestHistory.objects.filter(request=request)
        history = history.order_by("id")
        assert request.last_modified_date == history.last().date
        assert request.last_moderator == history.last().actor


def test_add_forge_now_denied_status_renamed_to_unsuccesful(migrator):

    state = migrator.apply_tested_migration((APP_LABEL, MIGRATION_0006))
    Request = state.apps.get_model(APP_LABEL, "Request")

    from swh.web.add_forge_now.models import RequestStatus

    req = Request(
        status=RequestStatus.UNSUCCESSFUL.name,
        submitter_name="dudess",
        submitter_email="dudess@orga.org",
        forge_type="cgit",
        forge_url="https://example.org/forge",
        forge_contact_email="forge@example.org",
        forge_contact_name="forge",
        forge_contact_comment=(
            "Discovered on the main forge homepag, following contact link."
        ),
        last_modified_date=datetime.now(timezone.utc),
    )
    with pytest.raises(ValidationError):
        req.clean_fields()

    state = migrator.apply_tested_migration((APP_LABEL, MIGRATION_0007))
    Request = state.apps.get_model(APP_LABEL, "Request")

    req = Request(
        status=RequestStatus.UNSUCCESSFUL.name,
        submitter_name="dudess",
        submitter_email="dudess@orga.org",
        forge_type="cgit",
        forge_url="https://example.org/forge",
        forge_contact_email="forge@example.org",
        forge_contact_name="forge",
        forge_contact_comment=(
            "Discovered on the main forge homepag, following contact link."
        ),
        last_modified_date=datetime.now(timezone.utc),
    )
    req.clean_fields()


def test_add_forge_now_url_validation(migrator):

    state = migrator.apply_tested_migration((APP_LABEL, MIGRATION_0007))
    Request = state.apps.get_model(APP_LABEL, "Request")

    from swh.web.add_forge_now.models import RequestStatus

    request = Request(
        status=RequestStatus.PENDING.name,
        submitter_name="dudess",
        submitter_email="dudess@orga.org",
        forge_type="cgit",
        forge_url="foo",
        forge_contact_email="forge@example.org",
        forge_contact_name="forge",
        forge_contact_comment="bar",
        last_modified_date=datetime.now(timezone.utc),
    )
    request.clean_fields()

    state = migrator.apply_tested_migration((APP_LABEL, MIGRATION_0008))
    Request = state.apps.get_model(APP_LABEL, "Request")

    request = Request(
        status=RequestStatus.PENDING.name,
        submitter_name="johndoe",
        submitter_email="johndoe@example.org",
        forge_type="cgit",
        forge_url="foobar",
        forge_contact_email="forge@example.org",
        forge_contact_name="forge",
        forge_contact_comment="bar",
        last_modified_date=datetime.now(timezone.utc),
    )
    with pytest.raises(ValidationError, match="Enter a valid URL."):
        request.clean_fields()
