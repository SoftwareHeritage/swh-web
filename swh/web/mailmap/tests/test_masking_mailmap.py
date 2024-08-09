# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from io import StringIO
from typing import Dict

import pytest

from django.core.management import call_command
from django.db import transaction

from swh.web.mailmap.models import UserMailmap

from .test_mailmap import populate_mailmap

pytest_plugins = [
    "swh.storage.tests.masking.conftest",
]


def call_sync_mailmaps(*args) -> str:
    out = StringIO()
    err = StringIO()

    call_command("sync_masking_mailmaps", *args, stdout=out, stderr=err)

    out.seek(0)
    err.seek(0)
    assert err.read() == ""
    return out.read()


def get_displaynames(masking_db) -> Dict[str, str]:
    with masking_db.cursor() as cur:
        cur.execute("SELECT original_email, display_name FROM display_name")

        return {bytes(f).decode("utf-8"): bytes(d).decode("utf-8") for (f, d) in cur}


@pytest.mark.django_db(transaction=True)
def test_sync_mailmaps_dry_run(masking_db_postgresql):
    with transaction.atomic():
        populate_mailmap()

    dsn = masking_db_postgresql.info.dsn

    out = call_sync_mailmaps(dsn)

    assert "(dry run)" in out
    assert "Synced 1 mailmaps to the masking proxy database" in out

    assert get_displaynames(masking_db_postgresql) == {}

    assert (
        UserMailmap.objects.filter(
            from_email_verified=True,
            display_name_activated=True,
            mailmap_last_processing_date__isnull=False,
        ).count()
        == 0
    )


@pytest.mark.django_db(transaction=True)
def test_sync_mailmaps_perform(masking_db_postgresql):
    with transaction.atomic():
        populate_mailmap()

    dsn = masking_db_postgresql.info.dsn

    out = call_sync_mailmaps("--perform", dsn)

    assert "(dry run)" not in out
    assert "Synced 1 mailmaps to the masking proxy database" in out

    expected_displaynames = {
        "from_emailVA@example.com": "Display Name V A",
    }

    assert get_displaynames(masking_db_postgresql) == expected_displaynames

    assert (
        UserMailmap.objects.filter(
            from_email_verified=True,
            display_name_activated=True,
            mailmap_last_processing_date__isnull=False,
        ).count()
        == 1
    )

    # do it again: nothing should be done
    out = call_sync_mailmaps("--perform", dsn)
    assert "No mailmap to update" in out
    assert get_displaynames(masking_db_postgresql) == expected_displaynames

    # do it again with --force
    out = call_sync_mailmaps("--perform", "--force", dsn)
    assert "No mailmap to update" not in out
    assert "(dry run)" not in out
    assert "Synced 1 mailmaps to the masking proxy database" in out
    assert get_displaynames(masking_db_postgresql) == expected_displaynames


@pytest.mark.django_db(transaction=True)
def test_sync_mailmaps_with_to_email(masking_db_postgresql):
    with transaction.atomic():
        populate_mailmap()

    dsn = masking_db_postgresql.info.dsn

    call_sync_mailmaps("--perform", dsn)

    expected_displaynames = {
        "from_emailVA@example.com": "Display Name V A",
    }

    assert get_displaynames(masking_db_postgresql) == expected_displaynames
    # Add a non-valid to_email
    with transaction.atomic():
        for mailmap in UserMailmap.objects.filter(
            from_email_verified=True, display_name_activated=True
        ):
            mailmap.to_email = "to_email@example.com"
            mailmap.save()

    call_sync_mailmaps("--perform", dsn)

    assert get_displaynames(masking_db_postgresql) == expected_displaynames

    # Verify the relevant to_email
    with transaction.atomic():
        for mailmap in UserMailmap.objects.filter(
            from_email_verified=True, display_name_activated=True
        ):
            mailmap.to_email_verified = True
            mailmap.save()

    call_sync_mailmaps("--perform", dsn)

    new_displayname = "Display Name V A <to_email@example.com>"
    expected_displaynames = {
        "from_emailVA@example.com": new_displayname,
    }

    assert get_displaynames(masking_db_postgresql) == expected_displaynames


@pytest.mark.django_db(transaction=True)
def test_sync_mailmaps_disable(masking_db_postgresql):
    with transaction.atomic():
        populate_mailmap()

    dsn = masking_db_postgresql.info.dsn

    # Do the initial mailmap sync
    call_sync_mailmaps("--perform", dsn)

    assert len(get_displaynames(masking_db_postgresql)) == 1

    updated = 0
    # Disable a display name
    with transaction.atomic():
        # Cannot use update() because `last_update_date` would not be updated
        for mailmap in UserMailmap.objects.filter(
            from_email_verified=True, display_name_activated=True
        ):
            mailmap.display_name_activated = False
            mailmap.save()
            updated += 1

    assert updated == 1

    # Sync mailmaps again
    out = call_sync_mailmaps("--perform", dsn)
    assert "1 mailmaps to disable" in out

    assert get_displaynames(masking_db_postgresql) == {}
