# Copyright (C) 2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import pytest


@pytest.fixture
def make_masked_object_exception():
    def _masked_object_exception(swhid_str: str):
        from uuid import UUID

        from swh.model.swhids import ExtendedSWHID
        from swh.storage.exc import MaskedObjectException
        from swh.storage.proxies.masking.db import MaskedState, MaskedStatus

        swhid = ExtendedSWHID.from_string(swhid_str)
        status = MaskedStatus(
            state=MaskedState.DECISION_PENDING,
            request=UUID("da785a27-7e59-4a35-b82a-a5ae3714407c"),
        )
        return MaskedObjectException({swhid: [status]})

    return _masked_object_exception
