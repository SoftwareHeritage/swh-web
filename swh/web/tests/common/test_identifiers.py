# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import pytest

from swh.web.common.exc import BadInputExc
from swh.web.common.identifiers import get_swh_persistent_id


def test_get_swh_persistent_id():
    swh_object_type = 'content'
    sha1_git = 'aafb16d69fd30ff58afdd69036a26047f3aebdc6'

    expected_swh_id = 'swh:1:cnt:' + sha1_git

    assert get_swh_persistent_id(
        swh_object_type, sha1_git) == expected_swh_id

    with pytest.raises(BadInputExc) as e:
        get_swh_persistent_id('foo', sha1_git)
    assert e.match('Invalid object')

    with pytest.raises(BadInputExc) as e:
        get_swh_persistent_id(swh_object_type, 'not a valid id')
    assert e.match('Invalid object')
