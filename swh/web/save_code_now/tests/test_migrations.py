# Copyright (C) 2021-2024 The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from datetime import datetime, timezone

import pytest

import django

from swh.web.save_code_now.models import (
    SAVE_REQUEST_ACCEPTED,
    SAVE_TASK_NOT_YET_SCHEDULED,
    SAVE_TASK_PENDING,
)

APP_NAME = "swh_web_save_code_now"

MIGRATION_0008 = "0008_save-code-now_indexes_20210106_1327"
MIGRATION_0009 = "0009_saveoriginrequest_visit_status"
MIGRATION_0010 = "0010_saveoriginrequest_user_id"
MIGRATION_0011 = "0011_saveoriginrequest_user_ids"
MIGRATION_0012 = "0012_saveoriginrequest_note"
MIGRATION_0013 = "0013_saveoriginrequest_webhook_info"
MIGRATION_0014 = "0014_saveoriginrequest_snapshot_swhid"
MIGRATION_0015 = "0015_alter_saveoriginrequest_loading_task_status"
MIGRATION_0016 = "0016_alter_saveoriginrequest_origin_url"


def test_migrations_09_add_visit_status_to_sor_model(migrator):
    """Ensures the migration adds the visit_status field to SaveOriginRequest table"""

    old_state = migrator.apply_initial_migration(
        (APP_NAME, MIGRATION_0008),
    )
    old_model = old_state.apps.get_model(APP_NAME, "SaveOriginRequest")

    assert hasattr(old_model, "visit_status") is False

    new_state = migrator.apply_tested_migration((APP_NAME, MIGRATION_0009))
    new_model = new_state.apps.get_model(APP_NAME, "SaveOriginRequest")

    assert hasattr(new_model, "visit_status") is True


def test_migrations_10_add_user_id_to_sor_model(migrator):
    """Ensures the migration adds the user_id field to SaveOriginRequest table"""

    old_state = migrator.apply_initial_migration(
        (APP_NAME, MIGRATION_0009),
    )
    old_model = old_state.apps.get_model(APP_NAME, "SaveOriginRequest")

    assert hasattr(old_model, "user_id") is False

    new_state = migrator.apply_tested_migration((APP_NAME, MIGRATION_0010))
    new_model = new_state.apps.get_model(APP_NAME, "SaveOriginRequest")

    assert hasattr(new_model, "user_id") is True


def test_migrations_12_add_note_to_sor_model(migrator):
    """Ensures the migration adds the user_id field to SaveOriginRequest table"""

    old_state = migrator.apply_initial_migration(
        (APP_NAME, MIGRATION_0011),
    )
    old_model = old_state.apps.get_model(APP_NAME, "SaveOriginRequest")

    assert hasattr(old_model, "note") is False

    new_state = migrator.apply_tested_migration((APP_NAME, MIGRATION_0012))
    new_model = new_state.apps.get_model(APP_NAME, "SaveOriginRequest")

    assert hasattr(new_model, "note") is True


def test_migrations_13_add_webhook_info_to_sor_model(migrator):
    """Ensures the migration adds the from_webhook field to SaveOriginRequest table"""

    old_state = migrator.apply_initial_migration(
        (APP_NAME, MIGRATION_0012),
    )
    old_model = old_state.apps.get_model(APP_NAME, "SaveOriginRequest")

    assert hasattr(old_model, "from_webhook") is False
    assert hasattr(old_model, "webhook_origin") is False

    new_state = migrator.apply_tested_migration((APP_NAME, MIGRATION_0013))
    new_model = new_state.apps.get_model(APP_NAME, "SaveOriginRequest")

    assert hasattr(new_model, "from_webhook") is True
    assert hasattr(new_model, "webhook_origin") is True


def test_migrations_14_add_snapshot_info_to_sor_model(migrator):
    """Ensures the migration adds the snapshot_swhid field to SaveOriginRequest table"""

    old_state = migrator.apply_initial_migration(
        (APP_NAME, MIGRATION_0013),
    )
    old_model = old_state.apps.get_model(APP_NAME, "SaveOriginRequest")

    assert hasattr(old_model, "snapshot_swhid") is False

    new_state = migrator.apply_tested_migration((APP_NAME, MIGRATION_0014))
    new_model = new_state.apps.get_model(APP_NAME, "SaveOriginRequest")

    assert hasattr(new_model, "snapshot_swhid") is True


def test_migrations_15_add_pending_status_for_loading_task(migrator):
    """Ensures the migration adds the pending status as possible value for
    the loading_task_status filed of SaveOriginRequest model"""

    new_pending_status = ("pending", "pending")

    old_state = migrator.apply_initial_migration((APP_NAME, MIGRATION_0014))
    old_model = old_state.apps.get_model(APP_NAME, "SaveOriginRequest")
    assert new_pending_status not in old_model.loading_task_status.field.choices

    old_model.objects.create(
        request_date=datetime.now(tz=timezone.utc),
        visit_type="git",
        origin_url="https://example.org",
        status=SAVE_REQUEST_ACCEPTED,
        loading_task_status=SAVE_TASK_NOT_YET_SCHEDULED,
    )

    assert old_model.objects.first().loading_task_status == SAVE_TASK_NOT_YET_SCHEDULED

    new_state = migrator.apply_tested_migration((APP_NAME, MIGRATION_0015))
    new_model = new_state.apps.get_model(APP_NAME, "SaveOriginRequest")
    assert new_pending_status in new_model.loading_task_status.field.choices

    assert new_model.objects.first().loading_task_status == SAVE_TASK_PENDING


def test_migrations_16_alter_saveoriginrequest_origin_url(migrator):
    old_state = migrator.apply_initial_migration((APP_NAME, MIGRATION_0015))
    old_model = old_state.apps.get_model(APP_NAME, "SaveOriginRequest")

    short_url = "https://example.org"
    long_url = "https://example.org/" + "e" * 200

    old_model.objects.create(
        request_date=datetime.now(tz=timezone.utc),
        visit_type="git",
        origin_url=short_url,
        status=SAVE_REQUEST_ACCEPTED,
        loading_task_status=SAVE_TASK_NOT_YET_SCHEDULED,
    )

    with pytest.raises(
        django.db.utils.DataError,
        match="value too long for type character",
    ):
        old_model.objects.create(
            request_date=datetime.now(tz=timezone.utc),
            visit_type="git",
            origin_url=long_url,
            status=SAVE_REQUEST_ACCEPTED,
            loading_task_status=SAVE_TASK_NOT_YET_SCHEDULED,
        )

    new_state = migrator.apply_tested_migration((APP_NAME, MIGRATION_0016))
    new_model = new_state.apps.get_model(APP_NAME, "SaveOriginRequest")

    new_model.objects.create(
        request_date=datetime.now(tz=timezone.utc),
        visit_type="git",
        origin_url=long_url,
        status=SAVE_REQUEST_ACCEPTED,
        loading_task_status=SAVE_TASK_NOT_YET_SCHEDULED,
    )

    assert {sor.origin_url for sor in new_model.objects.all()} == {short_url, long_url}
