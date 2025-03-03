# Copyright (C) 2025 The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information
import rfc3987

from rest_framework import serializers

from swh.model.exceptions import ValidationError
from swh.model.swhids import QualifiedSWHID


class SoftLimitsIntegerField(serializers.IntegerField):
    """An IntegerField that soft-enforce min/max values."""

    def to_internal_value(self, data) -> int:
        """Before returning `data` limit its value to min_value & max_value.

        Args:
            data: a string representation of a value

        Returns:
            An integer between min_value & max_value
        """
        data = super().to_internal_value(data)
        if self.min_value:
            data = max(data, self.min_value)
        if self.max_value:
            data = min(data, self.max_value)
        return data


class SWHIDField(serializers.CharField):
    """A SWHID field."""

    def to_internal_value(self, data: str) -> str:
        """Validate a SWHID.

        Args:
            value: a string

        Raises:
            serializers.ValidationError: invalid SWHID

        Returns:
            a string
        """
        data = super().to_internal_value(data)
        try:
            QualifiedSWHID.from_string(data)
        except ValidationError as e:
            raise serializers.ValidationError(
                f"Invalid target SWHID {data}: {e.message}."
            )
        return data


class IRIField(serializers.CharField):
    """An Internationalized Resource Identifier field.

    Requires a valid IRI value and limits its length to 4096, can be used to handle
    origin URLS.
    """

    def __init__(self, **kwargs):
        """Defaults max_length to 4096."""
        if "max_length" not in kwargs:
            kwargs["max_length"] = 4096
        super().__init__(**kwargs)

    def to_internal_value(self, data: str) -> str:
        """Validate the IRI.

        Args:
            data: a string

        Raises:
            serializers.ValidationError: invalid IRI

        Returns:
            an URI
        """
        data = super().to_internal_value(data)
        try:
            rfc3987.parse(data, rule="IRI")
        except ValueError as e:
            raise serializers.ValidationError(str(e))
        return data
