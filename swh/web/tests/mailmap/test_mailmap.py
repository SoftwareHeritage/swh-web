# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import datetime
from io import StringIO
import json
from typing import Dict

from psycopg2.extras import execute_values
import pytest

from django.core.management import call_command
from django.db import transaction

from swh.model.model import Person
from swh.web.mailmap.models import UserMailmap, UserMailmapEvent
from swh.web.tests.helpers import (
    check_api_post_response,
    check_http_get_response,
    check_http_post_response,
)
from swh.web.utils import reverse


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("view_name", ["profile-mailmap-add", "profile-mailmap-update"])
def test_mailmap_endpoints_anonymous_user(api_client, view_name):
    url = reverse(view_name)
    check_api_post_response(api_client, url, status_code=403)


@pytest.mark.django_db(transaction=True)
def test_mailmap_endpoints_user_with_permission(
    api_client, mailmap_user, mailmap_admin
):

    for user, name in ((mailmap_user, "bar"), (mailmap_admin, "baz")):

        UserMailmapEvent.objects.all().delete()

        api_client.force_login(user)

        request_data = {"from_email": f"{name}@example.org", "display_name": name}

        for view_name in ("profile-mailmap-add", "profile-mailmap-update"):
            url = reverse(view_name)
            check_api_post_response(
                api_client,
                url,
                data=request_data,
                status_code=200,
            )

        # FIXME: use check_api_get_responses; currently this crashes without
        # content_type="application/json"
        resp = check_http_get_response(
            api_client,
            reverse("profile-mailmap-list"),
            status_code=200,
            content_type="application/json",
        ).data
        assert len(resp) == 1
        assert resp[0]["from_email"] == f"{name}@example.org"
        assert resp[0]["display_name"] == name

        events = UserMailmapEvent.objects.order_by("timestamp").all()
        assert len(events) == 2
        assert events[0].request_type == "add"
        assert json.loads(events[0].request) == request_data
        assert events[1].request_type == "update"
        assert json.loads(events[1].request) == request_data


@pytest.mark.django_db(transaction=True)
def test_mailmap_add_duplicate(api_client, mailmap_user, mailmap_admin):

    for user, name in ((mailmap_user, "foo"), (mailmap_admin, "bar")):

        api_client.force_login(user)

        check_api_post_response(
            api_client,
            reverse("profile-mailmap-add"),
            data={"from_email": f"{name}@example.org", "display_name": name},
            status_code=200,
        )
        check_api_post_response(
            api_client,
            reverse("profile-mailmap-add"),
            data={"from_email": f"{name}@example.org", "display_name": name},
            status_code=400,
        )


@pytest.mark.django_db(transaction=True)
def test_mailmap_add_full(api_client, mailmap_user, mailmap_admin):

    for user, name in ((mailmap_user, "foo"), (mailmap_admin, "bar")):

        api_client.force_login(user)

        UserMailmapEvent.objects.all().delete()

        request_data = {
            "from_email": f"{name}@example.org",
            "from_email_verified": True,
            "from_email_verification_request_date": "2021-02-07T14:04:15Z",
            "display_name": name,
            "display_name_activated": True,
            "to_email": "baz@example.org",
            "to_email_verified": True,
            "to_email_verification_request_date": "2021-02-07T15:54:59Z",
        }

        check_api_post_response(
            api_client,
            reverse("profile-mailmap-add"),
            data=request_data,
            status_code=200,
        )

        resp = check_http_get_response(
            api_client,
            reverse("profile-mailmap-list"),
            status_code=200,
            content_type="application/json",
        ).data
        assert len(resp) == 1
        assert resp[0].items() >= request_data.items()

        events = UserMailmapEvent.objects.all()
        assert len(events) == 1
        assert events[0].request_type == "add"
        assert json.loads(events[0].request) == request_data
        assert events[0].successful


@pytest.mark.django_db(transaction=True)
def test_mailmap_endpoints_error_response(api_client, mailmap_user, mailmap_admin):

    for user in (mailmap_user, mailmap_admin):

        api_client.force_login(user)

        UserMailmapEvent.objects.all().delete()

        url = reverse("profile-mailmap-add")
        resp = check_api_post_response(api_client, url, status_code=400)
        assert b"from_email" in resp.content

        url = reverse("profile-mailmap-update")
        resp = check_api_post_response(api_client, url, status_code=400)
        assert b"from_email" in resp.content

        events = UserMailmapEvent.objects.order_by("timestamp").all()
        assert len(events) == 2

        assert events[0].request_type == "add"
        assert json.loads(events[0].request) == {}
        assert not events[0].successful

        assert events[1].request_type == "update"
        assert json.loads(events[1].request) == {}
        assert not events[1].successful


@pytest.mark.django_db(transaction=True)
def test_mailmap_update(api_client, mailmap_user, mailmap_admin):

    for user, name in ((mailmap_user, "foo"), (mailmap_admin, "bar")):

        api_client.force_login(user)

        UserMailmapEvent.objects.all().delete()

        before_add = datetime.datetime.now(tz=datetime.timezone.utc)

        check_api_post_response(
            api_client,
            reverse("profile-mailmap-add"),
            data={
                "from_email": f"{name}1@example.org",
                "display_name": "Display Name 1",
            },
            status_code=200,
        )
        check_api_post_response(
            api_client,
            reverse("profile-mailmap-add"),
            data={
                "from_email": f"{name}2@example.org",
                "display_name": "Display Name 2",
            },
            status_code=200,
        )
        after_add = datetime.datetime.now(tz=datetime.timezone.utc)

        user_id = None if user == mailmap_admin else str(user.id)

        mailmaps = list(
            UserMailmap.objects.filter(user_id=user_id).order_by("from_email").all()
        )
        assert len(mailmaps) == 2, mailmaps

        assert mailmaps[0].from_email == f"{name}1@example.org", mailmaps
        assert mailmaps[0].display_name == "Display Name 1", mailmaps
        assert before_add <= mailmaps[0].last_update_date <= after_add

        assert mailmaps[1].from_email == f"{name}2@example.org", mailmaps
        assert mailmaps[1].display_name == "Display Name 2", mailmaps
        assert before_add <= mailmaps[0].last_update_date <= after_add

        before_update = datetime.datetime.now(tz=datetime.timezone.utc)

        check_api_post_response(
            api_client,
            reverse("profile-mailmap-update"),
            data={
                "from_email": f"{name}1@example.org",
                "display_name": "Display Name 1b",
            },
            status_code=200,
        )

        after_update = datetime.datetime.now(tz=datetime.timezone.utc)

        mailmaps = list(
            UserMailmap.objects.filter(user_id=user_id).order_by("from_email").all()
        )
        assert len(mailmaps) == 2, mailmaps

        assert mailmaps[0].from_email == f"{name}1@example.org", mailmaps
        assert mailmaps[0].display_name == "Display Name 1b", mailmaps
        assert before_update <= mailmaps[0].last_update_date <= after_update

        assert mailmaps[1].from_email == f"{name}2@example.org", mailmaps
        assert mailmaps[1].display_name == "Display Name 2", mailmaps
        assert before_add <= mailmaps[1].last_update_date <= after_add

        events = UserMailmapEvent.objects.order_by("timestamp").all()
        assert len(events) == 3
        assert events[0].request_type == "add"
        assert events[1].request_type == "add"
        assert events[2].request_type == "update"


@pytest.mark.django_db(transaction=True)
def test_mailmap_update_from_email_not_found(api_client, mailmap_admin):
    api_client.force_login(mailmap_admin)
    check_api_post_response(
        api_client,
        reverse("profile-mailmap-update"),
        data={
            "from_email": "invalid@example.org",
            "display_name": "Display Name",
        },
        status_code=404,
    )


NB_MAILMAPS = 20
MM_PER_PAGE = 10


def _create_mailmaps(client):
    mailmaps = []
    for i in range(NB_MAILMAPS):
        resp = check_http_post_response(
            client,
            reverse("profile-mailmap-add"),
            data={
                "from_email": f"user{i:02d}@example.org",
                "display_name": f"User {i:02d}",
            },
            status_code=200,
        )
        mailmaps.append(json.loads(resp.content))
    return mailmaps


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_mailmap_list_datatables_no_parameters(client, mailmap_admin):
    client.force_login(mailmap_admin)
    mailmaps = _create_mailmaps(client)

    url = reverse("profile-mailmap-list-datatables")

    resp = check_http_get_response(client, url, status_code=200)
    mailmap_data = json.loads(resp.content)

    assert mailmap_data["recordsTotal"] == NB_MAILMAPS
    assert mailmap_data["recordsFiltered"] == NB_MAILMAPS

    # mailmaps sorted by ascending from_email by default
    for i in range(10):
        assert mailmap_data["data"][i]["from_email"] == mailmaps[i]["from_email"]


@pytest.mark.django_db(transaction=True, reset_sequences=True)
@pytest.mark.parametrize("sort_direction", ["asc", "desc"])
def test_mailmap_list_datatables_ordering(client, mailmap_admin, sort_direction):
    client.force_login(mailmap_admin)
    mailmaps = _create_mailmaps(client)
    mailmaps_sorted = list(sorted(mailmaps, key=lambda d: d["display_name"]))
    all_display_names = [mm["display_name"] for mm in mailmaps_sorted]
    if sort_direction == "desc":
        all_display_names = list(reversed(all_display_names))

    for i in range(NB_MAILMAPS // MM_PER_PAGE):
        url = reverse(
            "profile-mailmap-list-datatables",
            query_params={
                "draw": i,
                "length": MM_PER_PAGE,
                "start": i * MM_PER_PAGE,
                "order[0][column]": 2,
                "order[0][dir]": sort_direction,
                "columns[2][name]": "display_name",
            },
        )

        resp = check_http_get_response(client, url, status_code=200)
        data = json.loads(resp.content)

        assert data["draw"] == i
        assert data["recordsFiltered"] == NB_MAILMAPS
        assert data["recordsTotal"] == NB_MAILMAPS
        assert len(data["data"]) == MM_PER_PAGE

        display_names = [mm["display_name"] for mm in data["data"]]

        expected_display_names = all_display_names[
            i * MM_PER_PAGE : (i + 1) * MM_PER_PAGE
        ]
        assert display_names == expected_display_names


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_mailmap_list_datatables_search(client, mailmap_admin):
    client.force_login(mailmap_admin)
    _create_mailmaps(client)

    search_value = "user1"

    url = reverse(
        "profile-mailmap-list-datatables",
        query_params={
            "draw": 1,
            "length": MM_PER_PAGE,
            "start": 0,
            "search[value]": search_value,
        },
    )

    resp = check_http_get_response(client, url, status_code=200)
    data = json.loads(resp.content)

    assert data["draw"] == 1
    assert data["recordsFiltered"] == MM_PER_PAGE
    assert data["recordsTotal"] == NB_MAILMAPS
    assert len(data["data"]) == MM_PER_PAGE

    for mailmap in data["data"]:
        assert search_value in mailmap["from_email"]


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
