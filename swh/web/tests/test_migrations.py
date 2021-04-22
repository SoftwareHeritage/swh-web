# Copyright (C) 2021 The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

APP_NAME = "swh_web_common"

MIGRATION_0008 = "0008_save-code-now_indexes_20210106_1327"
MIGRATION_0009 = "0009_saveoriginrequest_visit_status"


def test_migrations_09_add_visit_status_to_sor_model(migrator):
    """Ensures the migration adds the visit_status field to SaveOriginRequest table"""

    old_state = migrator.apply_initial_migration((APP_NAME, MIGRATION_0008),)
    old_webapp = old_state.apps.get_model(APP_NAME, "SaveOriginRequest")

    assert hasattr(old_webapp, "visit_status") is False

    new_state = migrator.apply_tested_migration((APP_NAME, MIGRATION_0009))
    new_webapp = new_state.apps.get_model(APP_NAME, "SaveOriginRequest")

    assert hasattr(new_webapp, "visit_status") is True
