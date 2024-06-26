# Copyright (C) 2015-2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.web.utils.metadata import get_bibtex_from_origin, get_bibtex_from_swhid


def test_get_bibtex_from_origin(origin_with_metadata_file):
    bibtex = get_bibtex_from_origin(origin_with_metadata_file["url"])

    assert "@software" in bibtex
    assert 'title = "Test Software"' in bibtex


def test_get_bibtex_from_swhid(objects_with_metadata_file):
    bibtex = get_bibtex_from_swhid(str(objects_with_metadata_file[0]))

    assert "@software" in bibtex
    assert 'title = "Test Software"' in bibtex
