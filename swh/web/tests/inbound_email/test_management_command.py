# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from contextlib import contextmanager
from dataclasses import dataclass
from email.message import EmailMessage
from io import BytesIO, StringIO
import re
import sys
from typing import Callable, Iterator
from unittest.mock import MagicMock

import pytest

from django.core.management import call_command
from django.dispatch import Signal

from swh.web.inbound_email.signals import EmailProcessingStatus, email_received


class MockedStdin:
    def __init__(self):
        self.buffer = BytesIO()


@dataclass
class CommandReturn:
    out: str
    err: str


@contextmanager
def signal_receiver(signal: Signal, name: str = "receiver_name") -> Iterator[Callable]:
    receiver = MagicMock()
    receiver.configure_mock(__name__=name, __qualname__=name)

    try:
        signal.connect(receiver)
        yield receiver
    finally:
        signal.disconnect(receiver)


def call_process_inbound_email(stdin_data: bytes) -> CommandReturn:
    orig_stdin = sys.stdin
    try:
        sys.stdin = MockedStdin()  # type: ignore
        sys.stdin.buffer.write(stdin_data)
        sys.stdin.buffer.seek(0)

        out = StringIO()
        err = StringIO()

        call_command("process_inbound_email", stdout=out, stderr=err)

        out.seek(0)
        err.seek(0)
        return CommandReturn(out=out.read(), err=err.read())
    finally:
        sys.stdin = orig_stdin


def test_empty_stdin(caplog):
    ret = call_process_inbound_email(b"")
    assert ret.out == ""
    assert ret.err == ""

    assert len(caplog.records) == 1
    log = caplog.records[0]
    assert log.levelname == "ERROR"
    assert "Unhandled message" in log.getMessage()


@pytest.mark.parametrize(
    "return_value,err_contents",
    [
        # When the email gets processed by one of the receivers, the management command
        # should not emit any output.
        (EmailProcessingStatus.PROCESSED, ""),
        # When a receiver fails, the management command outputs a message to this effect
        (EmailProcessingStatus.FAILED, "Failed receiver.*receiver_name"),
        # When all receivers ignore a message, this fact is printed too
        (EmailProcessingStatus.IGNORED, "Unhandled message"),
    ],
)
def test_signal_receiver(return_value, err_contents, caplog):
    """Check that signal receivers are properly called when running the management command.

    Check for output depending on its return value"""
    message = EmailMessage()
    message["to"] = "test@example.com"
    message["subject"] = "Test Subject"
    message.set_content("This is a test message.\n")

    with signal_receiver(email_received) as receiver:
        receiver.return_value = return_value

        ret = call_process_inbound_email(bytes(message))
        assert ret.out == ""
        assert ret.err == ""
        output = "\n".join(record.getMessage() for record in caplog.records)
        if err_contents:
            assert re.match(err_contents, output)
        else:
            assert output == ""

        calls = receiver.call_args_list

        assert len(calls) == 1
        assert bytes(calls[0][1]["message"]) == bytes(message)


def test_multiple_receivers(caplog):
    message = EmailMessage()
    message["to"] = "test@example.com"
    message["subject"] = "Test Subject"
    message.set_content("This is a test message.\n")

    with signal_receiver(email_received, name="ignored") as ignored, signal_receiver(
        email_received, name="processed"
    ) as processed:
        ignored.return_value = EmailProcessingStatus.IGNORED
        processed.return_value = EmailProcessingStatus.PROCESSED

        ret = call_process_inbound_email(bytes(message))
        assert ret.out == ""
        assert ret.err == ""

        assert not caplog.records

        for receiver in [ignored, processed]:
            calls = receiver.call_args_list

            assert len(calls) == 1
            assert bytes(calls[0][1]["message"]) == bytes(message)


def test_signal_receiver_exception(caplog):
    message = EmailMessage()
    message["to"] = "test@example.com"
    message["subject"] = "Test Subject"
    message.set_content("This is a test message.\n")

    with signal_receiver(email_received, name="exception_raised") as receiver:
        receiver.side_effect = ValueError("I'm broken!")

        ret = call_process_inbound_email(bytes(message))
        assert ret.out == ""
        assert ret.err == ""

        output = "\n".join(
            record.getMessage() + ("\n" + record.exc_text if record.exc_text else "")
            for record in caplog.records
        )

        assert re.match("Failed receiver.*exception_raised", output)
        assert "following exception" in output
        assert "ValueError" in output
        assert "I'm broken" in output
