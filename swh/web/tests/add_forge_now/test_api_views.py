# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import copy
import datetime
import threading
import time
from typing import Dict
from urllib.parse import urlencode, urlparse

import iso8601
import pytest

from swh.web.add_forge_now.models import Request, RequestHistory
from swh.web.config import get_config
from swh.web.inbound_email.utils import get_address_for_pk
from swh.web.tests.helpers import (
    check_api_get_responses,
    check_api_post_response,
    check_http_get_response,
    check_http_post_response,
)
from swh.web.utils import reverse


@pytest.mark.django_db
def test_add_forge_request_create_anonymous_user(api_client):
    url = reverse("api-1-add-forge-request-create")
    check_api_post_response(api_client, url, status_code=403)


@pytest.mark.django_db
def test_add_forge_request_create_empty(api_client, regular_user):
    api_client.force_login(regular_user)
    url = reverse("api-1-add-forge-request-create")
    resp = check_api_post_response(api_client, url, status_code=400)
    assert '"forge_type"' in resp.data["reason"]


ADD_FORGE_DATA_FORGE1: Dict = {
    "forge_type": "gitlab",
    "forge_url": "https://gitlab.example.org",
    "forge_contact_email": "admin@gitlab.example.org",
    "forge_contact_name": "gitlab.example.org admin",
    "forge_contact_comment": "user marked as owner in forge members",
    "submitter_forward_username": True,
}

ADD_FORGE_DATA_FORGE2: Dict = {
    "forge_type": "gitea",
    "forge_url": "https://gitea.example.org",
    "forge_contact_email": "admin@gitea.example.org",
    "forge_contact_name": "gitea.example.org admin",
    "forge_contact_comment": "user marked as owner in forge members",
    "submitter_forward_username": True,
}

ADD_FORGE_DATA_FORGE3: Dict = {
    "forge_type": "heptapod",
    "forge_url": "https://heptapod.host/",
    "forge_contact_email": "admin@example.org",
    "forge_contact_name": "heptapod admin",
    "forge_contact_comment": "",  # authorized empty or null comment
    "submitter_forward_username": False,
}

ADD_FORGE_DATA_FORGE4: Dict = {
    **ADD_FORGE_DATA_FORGE3,
    "forge_url": "https://heptapod2.host/",
    "submitter_forward_username": "on",
}

ADD_FORGE_DATA_FORGE5: Dict = {
    **ADD_FORGE_DATA_FORGE3,
    "forge_url": "https://heptapod3.host/",
    "submitter_forward_username": "off",
}


def inbound_email_for_pk(pk: int) -> str:
    """Check that the inbound email matches the one expected for the given pk"""

    base_address = get_config()["add_forge_now"]["email_address"]
    return get_address_for_pk(
        salt="swh_web_add_forge_now", base_address=base_address, pk=pk
    )


@pytest.mark.django_db(transaction=True, reset_sequences=True)
@pytest.mark.parametrize(
    "add_forge_data",
    [
        ADD_FORGE_DATA_FORGE1,
        ADD_FORGE_DATA_FORGE2,
        ADD_FORGE_DATA_FORGE3,
        ADD_FORGE_DATA_FORGE4,
    ],
)
def test_add_forge_request_create_success_post(
    api_client, regular_user, add_forge_data
):
    api_client.force_login(regular_user)
    url = reverse("api-1-add-forge-request-create")

    date_before = datetime.datetime.now(tz=datetime.timezone.utc)

    resp = check_api_post_response(
        api_client,
        url,
        data=add_forge_data,
        status_code=201,
    )

    date_after = datetime.datetime.now(tz=datetime.timezone.utc)

    consent = add_forge_data["submitter_forward_username"]
    # map the expected result with what's expectedly read from the db to ease comparison
    expected_consent_bool = consent == "on" if isinstance(consent, str) else consent

    assert resp.data == {
        **add_forge_data,
        "id": resp.data["id"],
        "status": "PENDING",
        "submission_date": resp.data["submission_date"],
        "submitter_name": regular_user.username,
        "submitter_email": regular_user.email,
        "submitter_forward_username": expected_consent_bool,
        "last_moderator": resp.data["last_moderator"],
        "last_modified_date": resp.data["last_modified_date"],
        "inbound_email_address": inbound_email_for_pk(resp.data["id"]),
        "forge_domain": urlparse(add_forge_data["forge_url"]).netloc,
    }

    assert date_before < iso8601.parse_date(resp.data["submission_date"]) < date_after

    request = Request.objects.all().last()

    assert request.forge_url == add_forge_data["forge_url"]
    assert request.submitter_name == regular_user.username


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_add_forge_request_create_success_form_encoded(client, regular_user):
    client.force_login(regular_user)
    url = reverse("api-1-add-forge-request-create")

    date_before = datetime.datetime.now(tz=datetime.timezone.utc)

    resp = check_http_post_response(
        client,
        url,
        request_content_type="application/x-www-form-urlencoded",
        data=urlencode(ADD_FORGE_DATA_FORGE1),
        status_code=201,
    )

    date_after = datetime.datetime.now(tz=datetime.timezone.utc)

    assert resp.data == {
        **ADD_FORGE_DATA_FORGE1,
        "id": resp.data["id"],
        "status": "PENDING",
        "submission_date": resp.data["submission_date"],
        "submitter_name": regular_user.username,
        "submitter_email": regular_user.email,
        "last_moderator": resp.data["last_moderator"],
        "last_modified_date": resp.data["last_modified_date"],
        "inbound_email_address": inbound_email_for_pk(1),
        "forge_domain": urlparse(ADD_FORGE_DATA_FORGE1["forge_url"]).netloc,
    }

    assert date_before < iso8601.parse_date(resp.data["submission_date"]) < date_after

    request = Request.objects.all()[0]

    assert request.forge_url == ADD_FORGE_DATA_FORGE1["forge_url"]
    assert request.submitter_name == regular_user.username


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_add_forge_request_create_duplicate(api_client, regular_user):
    api_client.force_login(regular_user)
    url = reverse("api-1-add-forge-request-create")
    check_api_post_response(
        api_client,
        url,
        data=ADD_FORGE_DATA_FORGE1,
        status_code=201,
    )
    check_api_post_response(
        api_client,
        url,
        data=ADD_FORGE_DATA_FORGE1,
        status_code=409,
    )

    requests = Request.objects.all()
    assert len(requests) == 1


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_add_forge_request_create_invalid_forge_url(api_client, regular_user):
    api_client.force_login(regular_user)
    url = reverse("api-1-add-forge-request-create")

    forge_data = copy.deepcopy(ADD_FORGE_DATA_FORGE1)
    forge_data["forge_url"] = "foo"

    resp = check_api_post_response(
        api_client,
        url,
        data=forge_data,
        status_code=400,
    )

    assert resp.data == {
        "exception": "BadInputExc",
        "reason": '{"forge_url": ["Enter a valid URL."]}',
    }


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_add_forge_request_update_anonymous_user(api_client):
    url = reverse("api-1-add-forge-request-update", url_args={"id": 1})
    check_api_post_response(api_client, url, status_code=403)


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_add_forge_request_update_regular_user(api_client, regular_user):
    api_client.force_login(regular_user)
    url = reverse("api-1-add-forge-request-update", url_args={"id": 1})
    check_api_post_response(api_client, url, status_code=403)


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_add_forge_request_update_non_existent(api_client, add_forge_moderator):
    api_client.force_login(add_forge_moderator)
    url = reverse("api-1-add-forge-request-update", url_args={"id": 1})
    check_api_post_response(api_client, url, status_code=400)


def create_add_forge_request(api_client, regular_user, data=ADD_FORGE_DATA_FORGE1):
    api_client.force_login(regular_user)
    url = reverse("api-1-add-forge-request-create")
    return check_api_post_response(
        api_client,
        url,
        data=data,
        status_code=201,
    )


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_add_forge_request_update_empty(api_client, regular_user, add_forge_moderator):
    create_add_forge_request(api_client, regular_user)

    api_client.force_login(add_forge_moderator)
    url = reverse("api-1-add-forge-request-update", url_args={"id": 1})
    check_api_post_response(api_client, url, status_code=400)


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_add_forge_request_update_missing_field(
    api_client, regular_user, add_forge_moderator
):
    create_add_forge_request(api_client, regular_user)

    api_client.force_login(add_forge_moderator)
    url = reverse("api-1-add-forge-request-update", url_args={"id": 1})
    check_api_post_response(api_client, url, data={}, status_code=400)
    check_api_post_response(
        api_client, url, data={"new_status": "REJECTED"}, status_code=400
    )


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_add_forge_request_update(api_client, regular_user, add_forge_moderator):
    create_add_forge_request(api_client, regular_user)

    api_client.force_login(add_forge_moderator)
    url = reverse("api-1-add-forge-request-update", url_args={"id": 1})

    check_api_post_response(
        api_client, url, data={"text": "updating request"}, status_code=200
    )

    check_api_post_response(
        api_client,
        url,
        data={"new_status": "REJECTED", "text": "request rejected"},
        status_code=200,
    )


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_add_forge_request_update_invalid_new_status(
    api_client, regular_user, add_forge_moderator
):
    create_add_forge_request(api_client, regular_user)

    api_client.force_login(add_forge_moderator)
    url = reverse("api-1-add-forge-request-update", url_args={"id": 1})
    check_api_post_response(
        api_client,
        url,
        data={"new_status": "ACCEPTED", "text": "request accepted"},
        status_code=400,
    )


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_add_forge_request_update_status_concurrent(
    api_client, regular_user, add_forge_moderator, mocker
):

    _block_while_testing = mocker.patch(
        "swh.web.add_forge_now.api_views._block_while_testing"
    )
    _block_while_testing.side_effect = lambda: time.sleep(1)

    create_add_forge_request(api_client, regular_user)

    api_client.force_login(add_forge_moderator)
    url = reverse("api-1-add-forge-request-update", url_args={"id": 1})

    worker_ended = False

    def worker():
        nonlocal worker_ended
        check_api_post_response(
            api_client,
            url,
            data={"new_status": "WAITING_FOR_FEEDBACK", "text": "waiting for message"},
            status_code=200,
        )
        worker_ended = True

    # this thread will first modify the request status to WAITING_FOR_FEEDBACK
    thread = threading.Thread(target=worker)
    thread.start()

    # the other thread (slower) will attempt to modify the request status to REJECTED
    # but it will not be allowed as the first faster thread already modified it
    # and REJECTED state can not be reached from WAITING_FOR_FEEDBACK one
    time.sleep(0.5)
    check_api_post_response(
        api_client,
        url,
        data={"new_status": "REJECTED", "text": "request accepted"},
        status_code=400,
    )
    thread.join()
    assert worker_ended


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_add_forge_request_list_anonymous(api_client, regular_user):
    url = reverse("api-1-add-forge-request-list")

    resp = check_api_get_responses(api_client, url, status_code=200)

    assert resp.data == []

    create_add_forge_request(api_client, regular_user)

    resp = check_api_get_responses(api_client, url, status_code=200)

    add_forge_request = {
        "forge_url": ADD_FORGE_DATA_FORGE1["forge_url"],
        "forge_type": ADD_FORGE_DATA_FORGE1["forge_type"],
        "status": "PENDING",
        "submission_date": resp.data[0]["submission_date"],
        "id": resp.data[0]["id"],
    }

    assert resp.data == [add_forge_request]

    create_add_forge_request(api_client, regular_user, data=ADD_FORGE_DATA_FORGE2)

    resp = check_api_get_responses(api_client, url, status_code=200)

    other_forge_request = {
        "forge_url": ADD_FORGE_DATA_FORGE2["forge_url"],
        "forge_type": ADD_FORGE_DATA_FORGE2["forge_type"],
        "status": "PENDING",
        "submission_date": resp.data[0]["submission_date"],
        "id": resp.data[0]["id"],
    }

    assert resp.data == [other_forge_request, add_forge_request]


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_add_forge_request_list_moderator(
    api_client, regular_user, add_forge_moderator
):
    url = reverse("api-1-add-forge-request-list")

    create_add_forge_request(api_client, regular_user)
    create_add_forge_request(api_client, regular_user, data=ADD_FORGE_DATA_FORGE2)

    api_client.force_login(add_forge_moderator)
    resp = check_api_get_responses(api_client, url, status_code=200)

    add_forge_request = {
        **ADD_FORGE_DATA_FORGE1,
        "status": "PENDING",
        "submission_date": resp.data[1]["submission_date"],
        "submitter_name": regular_user.username,
        "submitter_email": regular_user.email,
        "last_moderator": resp.data[1]["last_moderator"],
        "last_modified_date": resp.data[1]["last_modified_date"],
        "id": resp.data[1]["id"],
        "inbound_email_address": inbound_email_for_pk(resp.data[1]["id"]),
        "forge_domain": urlparse(ADD_FORGE_DATA_FORGE1["forge_url"]).netloc,
    }

    other_forge_request = {
        **ADD_FORGE_DATA_FORGE2,
        "status": "PENDING",
        "submission_date": resp.data[0]["submission_date"],
        "submitter_name": regular_user.username,
        "submitter_email": regular_user.email,
        "last_moderator": resp.data[0]["last_moderator"],
        "last_modified_date": resp.data[0]["last_modified_date"],
        "id": resp.data[0]["id"],
        "inbound_email_address": inbound_email_for_pk(resp.data[0]["id"]),
        "forge_domain": urlparse(ADD_FORGE_DATA_FORGE2["forge_url"]).netloc,
    }

    assert resp.data == [other_forge_request, add_forge_request]


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_add_forge_request_list_pagination(
    api_client, regular_user, api_request_factory
):
    create_add_forge_request(api_client, regular_user)
    create_add_forge_request(api_client, regular_user, data=ADD_FORGE_DATA_FORGE2)

    url = reverse("api-1-add-forge-request-list", query_params={"per_page": 1})

    resp = check_api_get_responses(api_client, url, 200)

    assert len(resp.data) == 1

    request = api_request_factory.get(url)

    next_url = reverse(
        "api-1-add-forge-request-list",
        query_params={"page": 2, "per_page": 1},
        request=request,
    )

    assert resp["Link"] == f'<{next_url}>; rel="next"'

    resp = check_api_get_responses(api_client, next_url, 200)

    assert len(resp.data) == 1

    prev_url = reverse(
        "api-1-add-forge-request-list",
        query_params={"page": 1, "per_page": 1},
        request=request,
    )

    assert resp["Link"] == f'<{prev_url}>; rel="previous"'


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_add_forge_request_list_submitter_filtering(
    api_client, regular_user, regular_user2
):
    create_add_forge_request(api_client, regular_user)
    create_add_forge_request(api_client, regular_user2, data=ADD_FORGE_DATA_FORGE2)

    api_client.force_login(regular_user)
    url = reverse(
        "api-1-add-forge-request-list", query_params={"user_requests_only": 1}
    )
    resp = check_api_get_responses(api_client, url, status_code=200)

    assert len(resp.data) == 1


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_add_forge_request_get(api_client, regular_user, add_forge_moderator):
    resp = create_add_forge_request(api_client, regular_user)

    submission_date = resp.data["submission_date"]

    url = reverse("api-1-add-forge-request-update", url_args={"id": 1})

    api_client.force_login(add_forge_moderator)
    check_api_post_response(
        api_client,
        url,
        data={"new_status": "WAITING_FOR_FEEDBACK", "text": "waiting for message"},
        status_code=200,
    )
    api_client.logout()

    url = reverse("api-1-add-forge-request-get", url_args={"id": 1})

    resp = check_api_get_responses(api_client, url, status_code=200)

    assert resp.data == {
        "request": {
            "forge_url": ADD_FORGE_DATA_FORGE1["forge_url"],
            "forge_type": ADD_FORGE_DATA_FORGE1["forge_type"],
            "id": 1,
            "status": "WAITING_FOR_FEEDBACK",
            "submission_date": submission_date,
        },
        "history": [
            {
                "id": 1,
                "actor_role": "SUBMITTER",
                "date": resp.data["history"][0]["date"],
                "new_status": "PENDING",
            },
            {
                "id": 2,
                "actor_role": "MODERATOR",
                "date": resp.data["history"][1]["date"],
                "new_status": "WAITING_FOR_FEEDBACK",
            },
        ],
    }


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_add_forge_request_get_moderator(api_client, regular_user, add_forge_moderator):
    resp = create_add_forge_request(api_client, regular_user)

    submission_date = resp.data["submission_date"]

    url = reverse("api-1-add-forge-request-update", url_args={"id": 1})

    api_client.force_login(add_forge_moderator)
    check_api_post_response(
        api_client,
        url,
        data={"new_status": "WAITING_FOR_FEEDBACK", "text": "waiting for message"},
        status_code=200,
    )

    url = reverse("api-1-add-forge-request-get", url_args={"id": 1})

    resp = check_api_get_responses(api_client, url, status_code=200)
    resp.data["history"] = [dict(history_item) for history_item in resp.data["history"]]

    assert resp.data == {
        "request": {
            **ADD_FORGE_DATA_FORGE1,
            "id": 1,
            "status": "WAITING_FOR_FEEDBACK",
            "submission_date": submission_date,
            "submitter_name": regular_user.username,
            "submitter_email": regular_user.email,
            "last_moderator": add_forge_moderator.username,
            "last_modified_date": resp.data["history"][1]["date"],
            "inbound_email_address": inbound_email_for_pk(1),
            "forge_domain": urlparse(ADD_FORGE_DATA_FORGE1["forge_url"]).netloc,
        },
        "history": [
            {
                "id": 1,
                "text": "",
                "actor": regular_user.username,
                "actor_role": "SUBMITTER",
                "date": resp.data["history"][0]["date"],
                "new_status": "PENDING",
                "message_source_url": None,
            },
            {
                "id": 2,
                "text": "waiting for message",
                "actor": add_forge_moderator.username,
                "actor_role": "MODERATOR",
                "date": resp.data["history"][1]["date"],
                "new_status": "WAITING_FOR_FEEDBACK",
                "message_source_url": None,
            },
        ],
    }


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_add_forge_request_get_moderator_message_source(
    api_client, regular_user, add_forge_moderator
):
    resp = create_add_forge_request(api_client, regular_user)

    rh = RequestHistory(
        request=Request.objects.get(pk=resp.data["id"]),
        new_status="WAITING_FOR_FEEDBACK",
        text="waiting for message",
        actor=add_forge_moderator.username,
        actor_role="MODERATOR",
        message_source=b"test with a message source",
    )
    rh.save()

    api_client.force_login(add_forge_moderator)
    url = reverse("api-1-add-forge-request-get", url_args={"id": resp.data["id"]})
    resp = check_api_get_responses(api_client, url, status_code=200)
    resp.data["history"] = [dict(history_item) for history_item in resp.data["history"]]

    # Check that the authentified moderator can't urlhack non-existent message sources
    assert resp.data["history"][0]["message_source_url"] is None
    empty_message_url = reverse(
        "forge-add-message-source", url_args={"id": resp.data["history"][0]["id"]}
    )
    check_http_get_response(api_client, empty_message_url, status_code=404)

    # Check that the authentified moderator can't urlhack non-existent message sources
    non_existent_message_url = reverse(
        "forge-add-message-source", url_args={"id": 9001}
    )
    check_http_get_response(api_client, non_existent_message_url, status_code=404)

    # Check that the authentified moderator can access the message source when the url is
    # given

    message_source_url = resp.data["history"][-1]["message_source_url"]
    assert message_source_url is not None

    message_source_resp = check_http_get_response(
        api_client, message_source_url, status_code=200, content_type="text/email"
    )

    # Check that the message source shows up as an attachment
    assert message_source_resp.content == rh.message_source
    disposition = message_source_resp["Content-Disposition"]
    assert disposition.startswith("attachment; filename=")
    assert disposition.endswith('.eml"')

    # Check that a regular user can't access message sources
    api_client.force_login(regular_user)
    check_http_get_response(api_client, message_source_url, status_code=302)

    api_client.force_login(add_forge_moderator)


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_add_forge_request_get_invalid(api_client):
    url = reverse("api-1-add-forge-request-get", url_args={"id": 3})
    check_api_get_responses(api_client, url, status_code=400)
