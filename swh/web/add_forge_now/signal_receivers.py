# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from email.message import EmailMessage
from typing import Type

from ..config import get_config
from ..inbound_email.signals import EmailProcessingStatus
from ..inbound_email.utils import get_message_plaintext, get_pks_from_message
from .apps import APP_LABEL
from .models import Request, RequestActorRole, RequestHistory, RequestStatus


def handle_inbound_message(sender: Type, **kwargs) -> EmailProcessingStatus:
    """Handle inbound email messages for add forge now.

    This uses the from field in the message to set the actor for the new entry in the
    request history. We also unconditionally advance the status of requests in the
    ``PENDING`` or ``WAITING_FOR_FEEDBACK`` states.

    The message source is saved in the request history as an escape hatch if something
    goes wrong during processing.

    """

    message = kwargs["message"]
    assert isinstance(message, EmailMessage)

    base_address = get_config()["add_forge_now"]["email_address"]

    pks = get_pks_from_message(
        salt=APP_LABEL, base_address=base_address, message=message
    )

    if not pks:
        return EmailProcessingStatus.IGNORED

    for pk in pks:
        try:
            request = Request.objects.get(pk=pk)
        except Request.DoesNotExist:
            continue

        request_updated = False

        message_plaintext = get_message_plaintext(message)
        if message_plaintext:
            history_text = message_plaintext.decode("utf-8", errors="replace")
        else:
            history_text = (
                "Could not parse the message contents, see the original message."
            )

        history_entry = RequestHistory(
            request=request,
            actor=str(message["from"]),
            actor_role=RequestActorRole.EMAIL.name,
            text=history_text,
            message_source=bytes(message),
        )

        new_status = {
            RequestStatus.PENDING: RequestStatus.WAITING_FOR_FEEDBACK,
            RequestStatus.WAITING_FOR_FEEDBACK: RequestStatus.FEEDBACK_TO_HANDLE,
        }.get(RequestStatus[request.status])

        if new_status:
            request.status = history_entry.new_status = new_status.name
            request_updated = True

        history_entry.save()
        if request_updated:
            request.save()

    return EmailProcessingStatus.PROCESSED
