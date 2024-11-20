# Copyright (C) 2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.urls.converters import REGISTERED_CONVERTERS, register_converter

from swh.model.swhids import CoreSWHID, ExtendedSWHID, QualifiedSWHID


class SWHIDConverter:
    """Simple SWHID django url path converter to simplify view URLs registration.

    When parsing URL, this simply wraps the SWHID regexp and pass the matched
    string as django view parameter, it is up to the view to verify the SWHID
    validity and returns a 400 status code if it is not.

    When reversing to an URL, only SWHID objects and str are allowed.
    """

    regex = "(swh|SWH):[0-9]+:[A-Za-z]+:[0-9A-Fa-f]+(;.*)?"

    def to_python(self, value):
        value_split = value.split(";", maxsplit=1)
        if len(value_split) > 1:
            return f"{value_split[0].lower()};{value_split[1]}"
        else:
            return value.lower()

    def to_url(self, value):
        if isinstance(value, (CoreSWHID, ExtendedSWHID, QualifiedSWHID, str)):
            return str(value)
        raise ValueError()


def register_url_path_converters() -> None:
    """Adds :class:`.SWHIDConverter` to django's url path converters.

    This method is called by the root `URLconf` but also in every app's `URLconf` that
    needs it to ease testing, that's why we need to check if it is already registered
    before adding it.
    """
    if "swhid" not in REGISTERED_CONVERTERS:
        register_converter(SWHIDConverter, "swhid")


register_url_path_converters()
