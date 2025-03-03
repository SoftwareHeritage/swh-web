# Copyright (C) 2025  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information
import pytest

from rest_framework import serializers

from swh.web.api.serializers import IRIField, SoftLimitsIntegerField, SWHIDField


def test_swhid_field():
    field = SWHIDField()

    with pytest.raises(serializers.ValidationError, match="abc"):
        field.to_internal_value("abc")
    swhid = "swh:1:cnt:8ff44f081d43176474b267de5451f2c2e88089d0;lines=5-10"
    assert (
        field.to_internal_value(
            "swh:1:cnt:8ff44f081d43176474b267de5451f2c2e88089d0;lines=5-10"
        )
        == swhid
    )


def test_soft_limits_integer_field():
    field = SoftLimitsIntegerField(min_value=50, max_value=100)

    with pytest.raises(serializers.ValidationError, match="integer is required"):
        field.to_internal_value("abc")

    assert field.to_internal_value(1) == 50
    assert field.to_internal_value(1000) == 100


def test_origin_url_field():
    field = IRIField()

    assert field.max_length == 4096

    with pytest.raises(serializers.ValidationError, match="'abc' is not a valid 'IRI'"):
        field.to_internal_value("abc")

    assert (
        field.to_internal_value("http://swh/a/b.html#test")
        == "http://swh/a/b.html#test"
    )
    assert field.to_internal_value("urn:issn:1382-3256") == "urn:issn:1382-3256"
    assert (
        field.to_internal_value("ftp://ソフトウェア遺産.org")
        == "ftp://ソフトウェア遺産.org"
    )
