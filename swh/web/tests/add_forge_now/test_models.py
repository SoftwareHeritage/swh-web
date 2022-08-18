# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import pytest

from swh.web.add_forge_now.models import Request, RequestStatus


@pytest.mark.parametrize(
    "current_status, allowed_next_statuses",
    [
        (
            RequestStatus.PENDING,
            [
                RequestStatus.WAITING_FOR_FEEDBACK,
                RequestStatus.REJECTED,
                RequestStatus.SUSPENDED,
            ],
        ),
        (RequestStatus.WAITING_FOR_FEEDBACK, [RequestStatus.FEEDBACK_TO_HANDLE]),
        (
            RequestStatus.FEEDBACK_TO_HANDLE,
            [
                RequestStatus.WAITING_FOR_FEEDBACK,
                RequestStatus.ACCEPTED,
                RequestStatus.REJECTED,
                RequestStatus.SUSPENDED,
                RequestStatus.UNSUCCESSFUL,
            ],
        ),
    ],
)
def test_allowed_next_statuses(current_status, allowed_next_statuses):
    assert current_status.allowed_next_statuses() == allowed_next_statuses


@pytest.mark.parametrize(
    "forge_url, expected_domain",
    [
        ("https://gitlab.example.com/foo/bar", "gitlab.example.com"),
        ("gitlab.example.com", "gitlab.example.com"),
        ("gitlab.example.com/foo/bar", "gitlab.example.com"),
    ],
)
def test_request_forge_domain(forge_url, expected_domain):
    assert Request(forge_url=forge_url).forge_domain == expected_domain
