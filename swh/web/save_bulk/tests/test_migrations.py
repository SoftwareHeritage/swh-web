# Copyright (C) 2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import pytest

import django

APP_NAME = "swh_web_save_bulk"

MIGRATION_0001 = "0001_initial"
MIGRATION_0002 = "0002_alter_savebulkorigin_origin_url"


def test_migrations_02_alter_savebulkorigin_origin_url(migrator):
    old_state = migrator.apply_initial_migration((APP_NAME, MIGRATION_0001))
    old_model = old_state.apps.get_model(APP_NAME, "SaveBulkOrigin")

    short_url = "https://example.org"
    long_url = "https://example.org/" + "e" * 200

    old_model.objects.create(
        visit_type="git",
        origin_url=short_url,
    )

    with pytest.raises(
        django.db.utils.DataError,
        match="value too long for type character",
    ):
        old_model.objects.create(
            visit_type="git",
            origin_url=long_url,
        )

    new_state = migrator.apply_tested_migration((APP_NAME, MIGRATION_0002))
    new_model = new_state.apps.get_model(APP_NAME, "SaveBulkOrigin")

    new_model.objects.create(
        visit_type="git",
        origin_url=long_url,
    )

    assert {sor.origin_url for sor in new_model.objects.all()} == {short_url, long_url}
