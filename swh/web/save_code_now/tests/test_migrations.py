# Copyright (C) 2021 The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

APP_NAME = "swh_web_save_code_now"

MIGRATION_0008 = "0008_save-code-now_indexes_20210106_1327"
MIGRATION_0009 = "0009_saveoriginrequest_visit_status"
MIGRATION_0010 = "0010_saveoriginrequest_user_id"
MIGRATION_0011 = "0011_saveoriginrequest_user_ids"
MIGRATION_0012 = "0012_saveoriginrequest_note"


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
