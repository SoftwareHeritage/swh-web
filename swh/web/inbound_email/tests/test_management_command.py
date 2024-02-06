# Copyright (C) 2022-2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from dataclasses import dataclass
from io import BytesIO, StringIO
import sys

import pytest

from django.core.management import call_command

from .common_tests import *  # noqa


class MockedStdin:
    def __init__(self):
        self.buffer = BytesIO()


@dataclass
class CommandReturn:
    out: str
    err: str


@pytest.fixture
def receive_inbound_message(inbound_message):
    def do_it(expect_failure=False):
        orig_stdin = sys.stdin
        try:
            sys.stdin = MockedStdin()
            sys.stdin.buffer.write(inbound_message)
            sys.stdin.buffer.seek(0)

            out = StringIO()
            err = StringIO()

            call_command("process_inbound_email", stdout=out, stderr=err)

            out.seek(0)
            err.seek(0)

            assert out.read() == ""
            assert err.read() == ""
        finally:
            sys.stdin = orig_stdin

        return inbound_message

    return do_it


@pytest.mark.inbound_message(b"")
def test_empty_stdin(caplog, receive_inbound_message):
    receive_inbound_message()

    assert len(caplog.records) == 1
    log = caplog.records[0]
    assert log.levelname == "ERROR"
    assert "Unhandled message" in log.getMessage()
