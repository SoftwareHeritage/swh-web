# Copyright (C) 2022 The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from datetime import datetime

import pytest

APP_NAME = "swh_web_auth"

MIGRATION_0005 = "0005_usermailmapevent"
MIGRATION_0006 = "0006_fix_mailmap_admin_user_id"
MIGRATION_0007 = "0007_mailmap_django_app"


def test_fix_mailmap_admin_user_id(migrator):
    state = migrator.apply_tested_migration((APP_NAME, MIGRATION_0005))
    UserMailmap = state.apps.get_model(APP_NAME, "UserMailmap")

    user_id = "45"

    UserMailmap.objects.create(
        user_id=user_id,
        from_email="user@example.org",
        from_email_verified=True,
        display_name="New display name",
    )

    UserMailmap.objects.filter(user_id=user_id).update(
        last_update_date=datetime(2022, 2, 11, 14, 16, 13, 614000)
    )

    assert UserMailmap.objects.filter(user_id=user_id).count() == 1
    assert UserMailmap.objects.filter(user_id=None).count() == 0

    state = migrator.apply_tested_migration((APP_NAME, MIGRATION_0006))
    UserMailmap = state.apps.get_model(APP_NAME, "UserMailmap")

    assert UserMailmap.objects.filter(user_id=user_id).count() == 0
    assert UserMailmap.objects.filter(user_id=None).count() == 1


def test_mailmap_django_app(migrator):
    state = migrator.apply_tested_migration((APP_NAME, MIGRATION_0006))
    UserMailmap = state.apps.get_model(APP_NAME, "UserMailmap")
    assert UserMailmap

    # UserMailmap model moved to swh_web_mailmap django application
    state = migrator.apply_tested_migration((APP_NAME, MIGRATION_0007))
    with pytest.raises(
        LookupError, match="App 'swh_web_auth' doesn't have a 'UserMailmap' model."
    ):
        state.apps.get_model(APP_NAME, "UserMailmap")
