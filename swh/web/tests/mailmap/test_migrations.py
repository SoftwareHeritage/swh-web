# Copyright (C) 2022 The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information


APP_NAME = "swh_web_mailmap"

MIGRATION_0001 = "0001_initial"


def test_mailmap_django_app(migrator):
    state = migrator.apply_tested_migration((APP_NAME, MIGRATION_0001))
    UserMailmap = state.apps.get_model(APP_NAME, "UserMailmap")
    assert UserMailmap
