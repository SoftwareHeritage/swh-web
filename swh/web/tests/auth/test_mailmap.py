# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from io import StringIO
from typing import Dict

from psycopg2.extras import execute_values
import pytest

from django.core.management import call_command
from django.db import transaction

from swh.model.model import Person
from swh.web.auth.models import UserMailmap
from swh.web.auth.utils import MAILMAP_PERMISSION
from swh.web.common.utils import reverse
from swh.web.tests.utils import check_api_post_response, create_django_permission


@pytest.fixture
def mailmap_user(regular_user):
    regular_user.user_permissions.add(create_django_permission(MAILMAP_PERMISSION))
    return regular_user


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("view_name", ["profile-mailmap-add", "profile-mailmap-update"])
def test_mailmap_endpoints_anonymous_user(api_client, view_name):
    url = reverse(view_name)
    check_api_post_response(api_client, url, status_code=403)


@pytest.mark.django_db(transaction=True)
def test_mailmap_endpoints_user_with_permission(api_client, mailmap_user):
    api_client.force_login(mailmap_user)
    for view_name in ("profile-mailmap-add", "profile-mailmap-update"):
        url = reverse(view_name)
        check_api_post_response(
            api_client,
            url,
            data={"from_email": "bar@example.org", "display_name": "bar"},
            status_code=200,
        )


@pytest.mark.django_db(transaction=True)
def test_mailmap_endpoints_error_response(api_client, mailmap_user):
    api_client.force_login(mailmap_user)
    for view_name in ("profile-mailmap-add", "profile-mailmap-update"):
        url = reverse(view_name)
        resp = check_api_post_response(api_client, url, status_code=500)
        assert "exception" in resp.data


def populate_mailmap():
    for (verified, activated) in (
        (False, False),
        (False, True),
        (True, False),
        (True, True),
    ):
        verified_str = "V" if verified else ""
        activated_str = "A" if activated else ""
        UserMailmap.objects.create(
            from_email=f"from_email{verified_str}{activated_str}@example.com",
            display_name=f"Display Name {verified_str} {activated_str}".strip(),
            from_email_verified=verified,
            display_name_activated=activated,
        )


def call_sync_mailmaps(*args) -> str:
    out = StringIO()
    err = StringIO()

    call_command("sync_mailmaps", *args, stdout=out, stderr=err)

    out.seek(0)
    err.seek(0)
    assert err.read() == ""
    return out.read()


MAILMAP_KNOWN_FULLNAMES = (
    "Original Name <from_email@example.com>",
    "Original Name V <from_emailV@example.com>",
    "Original Name A <from_emailA@example.com>",
    "Original Name V A <from_emailVA@example.com>",
    "Original Name V A 2 <from_emailVA@example.com>",
    "Original Name V A 3 <from_emailVA@example.com>",
)


MAILMAP_KNOWN_PEOPLE = tuple(
    Person.from_fullname(f.encode()) for f in MAILMAP_KNOWN_FULLNAMES
)


def init_stub_storage_db(postgresql):
    cur = postgresql.cursor()
    cur.execute(
        """
        CREATE TABLE person (
          fullname bytea PRIMARY KEY,
          name bytea,
          email bytea,
          displayname bytea
        )
        """
    )
    execute_values(
        cur,
        "INSERT INTO person (fullname, name, email) VALUES %s",
        (p.to_dict() for p in MAILMAP_KNOWN_PEOPLE),
        template="(%(fullname)s, %(name)s, %(email)s)",
    )
    cur.execute("CREATE INDEX ON person (email)")
    postgresql.commit()
    cur.close()

    return postgresql.dsn


def get_displaynames(postgresql) -> Dict[str, str]:
    with postgresql.cursor() as cur:
        cur.execute(
            "SELECT fullname, displayname FROM person WHERE displayname IS NOT NULL"
        )

        return {bytes(f).decode("utf-8"): bytes(d).decode("utf-8") for (f, d) in cur}


@pytest.mark.django_db(transaction=True)
def test_sync_mailmaps_dry_run(postgresql):
    with transaction.atomic():
        populate_mailmap()

    dsn = init_stub_storage_db(postgresql)

    out = call_sync_mailmaps(dsn)

    assert "(dry run)" in out
    assert "Synced 1 mailmaps to swh.storage database" in out

    assert get_displaynames(postgresql) == {}

    assert (
        UserMailmap.objects.filter(
            from_email_verified=True,
            display_name_activated=True,
            mailmap_last_processing_date__isnull=False,
        ).count()
        == 0
    )


@pytest.mark.django_db(transaction=True)
def test_sync_mailmaps_perform(postgresql):
    with transaction.atomic():
        populate_mailmap()

    dsn = init_stub_storage_db(postgresql)

    out = call_sync_mailmaps("--perform", dsn)

    assert "(dry run)" not in out
    assert "Synced 1 mailmaps to swh.storage database" in out

    expected_displaynames = {
        "Original Name V A <from_emailVA@example.com>": "Display Name V A",
        "Original Name V A 2 <from_emailVA@example.com>": "Display Name V A",
        "Original Name V A 3 <from_emailVA@example.com>": "Display Name V A",
    }

    assert get_displaynames(postgresql) == expected_displaynames

    assert (
        UserMailmap.objects.filter(
            from_email_verified=True,
            display_name_activated=True,
            mailmap_last_processing_date__isnull=False,
        ).count()
        == 1
    )


@pytest.mark.django_db(transaction=True)
def test_sync_mailmaps_with_to_email(postgresql):
    with transaction.atomic():
        populate_mailmap()

    dsn = init_stub_storage_db(postgresql)

    call_sync_mailmaps("--perform", dsn)

    expected_displaynames = {
        "Original Name V A <from_emailVA@example.com>": "Display Name V A",
        "Original Name V A 2 <from_emailVA@example.com>": "Display Name V A",
        "Original Name V A 3 <from_emailVA@example.com>": "Display Name V A",
    }

    assert get_displaynames(postgresql) == expected_displaynames

    # Add a non-valid to_email
    with transaction.atomic():
        for mailmap in UserMailmap.objects.filter(
            from_email_verified=True, display_name_activated=True
        ):
            mailmap.to_email = "to_email@example.com"
            mailmap.save()

    call_sync_mailmaps("--perform", dsn)

    assert get_displaynames(postgresql) == expected_displaynames

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
        "Original Name V A <from_emailVA@example.com>": new_displayname,
        "Original Name V A 2 <from_emailVA@example.com>": new_displayname,
        "Original Name V A 3 <from_emailVA@example.com>": new_displayname,
    }

    assert get_displaynames(postgresql) == expected_displaynames


@pytest.mark.django_db(transaction=True)
def test_sync_mailmaps_disable(postgresql):
    """Check that disabling a mailmap only happens once"""
    with transaction.atomic():
        populate_mailmap()

    dsn = init_stub_storage_db(postgresql)

    # Do the initial mailmap sync
    call_sync_mailmaps("--perform", dsn)

    assert len(get_displaynames(postgresql)) == 3

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

    assert get_displaynames(postgresql) == {}

    # Update a displayname by hand
    with postgresql.cursor() as cur:
        cur.execute(
            "UPDATE person SET displayname='Manual Display Name' "
            "WHERE fullname='Original Name V A <from_emailVA@example.com>'"
        )

    expected_displaynames = {
        "Original Name V A <from_emailVA@example.com>": "Manual Display Name"
    }

    assert get_displaynames(postgresql) == expected_displaynames

    # Sync mailmaps one last time. No mailmaps should be disabled
    out = call_sync_mailmaps("--perform", dsn)
    assert "0 mailmaps to disable" in out

    assert get_displaynames(postgresql) == expected_displaynames
