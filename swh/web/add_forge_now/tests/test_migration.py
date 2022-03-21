# Copyright (C) 2022 The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from datetime import datetime, timezone

import pytest

APP_NAME = "add_forge_now"

MIGRATION_0001 = "0001_initial"
MIGRATION_0002 = "0002_authorized_null_comment"


def now() -> datetime:
    return datetime.now(tz=timezone.utc)


def test_add_forge_now_initial_migration(migrator):
    """Basic migration test to check the model is fine"""

    state = migrator.apply_tested_migration((APP_NAME, MIGRATION_0001))
    request = state.apps.get_model(APP_NAME, "Request")
    request_history = state.apps.get_model(APP_NAME, "RequestHistory")

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

    state = migrator.apply_tested_migration((APP_NAME, MIGRATION_0001))

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

    requestModel = state.apps.get_model(APP_NAME, "Request")

    req = make_request_with_empty_comment(requestModel)
    with pytest.raises(IntegrityError, match="violates not-null constraint"):
        req.save()

    state = migrator.apply_tested_migration((APP_NAME, MIGRATION_0002))
    requestModel2 = state.apps.get_model(APP_NAME, "Request")

    req2 = make_request_with_empty_comment(requestModel2)
    req2.save()
