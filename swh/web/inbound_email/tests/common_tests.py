# Copyright (C) 2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


from contextlib import contextmanager
from email.message import EmailMessage
import re
from typing import Iterator
from unittest.mock import MagicMock

import pytest

from django.dispatch import Signal

from swh.web.inbound_email import signals


@contextmanager
def mock_signal_receiver(
    signal: Signal,
    name: str = "receiver_name",
    disconnect_old_receivers: bool = True,
) -> Iterator[MagicMock]:
    receiver = MagicMock()
    receiver.configure_mock(__name__=name, __qualname__=name)

    try:
        if disconnect_old_receivers:
            old_receivers = signal.receivers
            signal.receivers = []
        signal.connect(receiver)
        yield receiver
    finally:
        signal.disconnect(receiver)
        if disconnect_old_receivers:
            signal.receivers = old_receivers


@pytest.fixture
def inbound_message(request) -> bytes:
    marker = request.node.get_closest_marker("inbound_message")
    if marker is None:
        raise ValueError("Missing inbound_message data")
    return marker.args[0]


def _test_message() -> bytes:
    message = EmailMessage()
    message["to"] = "test@example.com"
    message["subject"] = "Test Subject"
    message.set_content("This is a test message.\n")

    return bytes(message)


TEST_MESSAGE = _test_message()


@pytest.mark.inbound_message(TEST_MESSAGE)
@pytest.mark.parametrize(
    "return_value,err_contents",
    [
        # When the email gets processed by one of the receivers, the management command
        # should not emit any output.
        (signals.EmailProcessingStatus.PROCESSED, ""),
        # When a receiver fails, the management command outputs a message to this effect
        (signals.EmailProcessingStatus.FAILED, "Failed receiver.*receiver_name"),
        # When all receivers ignore a message, this fact is printed too
        (signals.EmailProcessingStatus.IGNORED, "Unhandled message"),
    ],
)
def test_signal_receiver(return_value, err_contents, caplog, receive_inbound_message):
    """Check that signal receivers are properly called when running the management command.

    Check for output depending on its return value"""

    with mock_signal_receiver(signals.email_received) as receiver:
        receiver.return_value = return_value

        message = receive_inbound_message(
            expect_failure=return_value != signals.EmailProcessingStatus.PROCESSED
        )

        output = "\n".join(record.getMessage() for record in caplog.records)

        if err_contents:
            assert re.match(err_contents, output)
        else:
            assert output == ""

        calls = receiver.call_args_list

        assert len(calls) == 1
        assert bytes(calls[0][1]["message"]) == message


@pytest.mark.inbound_message(TEST_MESSAGE)
def test_multiple_receivers(caplog, receive_inbound_message):
    with (
        mock_signal_receiver(signals.email_received, name="ignored") as ignored,
        mock_signal_receiver(
            signals.email_received, name="processed", disconnect_old_receivers=False
        ) as processed,
    ):
        ignored.return_value = signals.EmailProcessingStatus.IGNORED
        processed.return_value = signals.EmailProcessingStatus.PROCESSED

        message = receive_inbound_message()

        assert not caplog.records

        for receiver in [ignored, processed]:
            calls = receiver.call_args_list

            assert len(calls) == 1
            assert bytes(calls[0][1]["message"]) == message


@pytest.mark.inbound_message(TEST_MESSAGE)
def test_signal_receiver_exception(caplog, receive_inbound_message):
    with mock_signal_receiver(
        signals.email_received, name="exception_raised"
    ) as receiver:
        receiver.side_effect = ValueError("I'm broken!")

        receive_inbound_message(expect_failure=True)

        output = "\n".join(
            record.getMessage() + ("\n" + record.exc_text if record.exc_text else "")
            for record in caplog.records
        )

        assert re.match("Failed receiver.*exception_raised", output)
        assert "following exception" in output
        assert "ValueError" in output
        assert "I'm broken" in output
