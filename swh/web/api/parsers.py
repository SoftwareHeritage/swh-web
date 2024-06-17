# Copyright (C) 2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import yaml

from django.conf import settings
from django.utils.encoding import force_str
from rest_framework.exceptions import ParseError
from rest_framework.parsers import BaseParser


class YAMLParser(BaseParser):
    """
    Parses YAML-serialized data (more robust version than djangorestframork-yaml).
    """

    media_type = "application/yaml"

    def parse(self, stream, media_type=None, parser_context=None):
        """
        Parses the incoming bytestream as YAML and returns the resulting data.
        """
        assert yaml, "YAMLParser requires pyyaml to be installed"

        parser_context = parser_context or {}
        encoding = parser_context.get("encoding", settings.DEFAULT_CHARSET)

        try:
            data = stream.read().decode(encoding)
            return yaml.safe_load(data)
        except (ValueError, yaml.parser.ParserError) as exc:
            raise ParseError("YAML parse error - %s" % force_str(exc))
        except yaml.scanner.ScannerError as e:
            raise ParseError(f"YAML scan error - {force_str(e)}")
