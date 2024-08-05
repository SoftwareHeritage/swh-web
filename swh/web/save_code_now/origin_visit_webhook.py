# Copyright (C) 2023  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from swh.web.config import get_config
from swh.web.save_code_now.origin_save import (
    get_save_origin_requests_to_update,
    schedule_origins_recurrent_visits,
    update_save_origin_requests_from_queryset,
)
from swh.web.utils.exc import BadInputExc

try:
    from swh.webhooks.utils import get_verified_webhook_payload

    webhooks_available = True
except ImportError:
    webhooks_available = False


@require_POST
@csrf_exempt
def save_origin_visit_webhook(request):
    """Endpoint that receives webhook messages about origin visits.
    Its purpose is to update the status of a save code now request."""
    if not request.headers.get("X-Swh-Event", "") == "origin.visit":
        raise BadInputExc("POST request is not a Software Heritage webhook")

    try:
        payload = get_verified_webhook_payload(
            request_data=request.body,
            request_headers=request.headers,
            secret=get_config().get("save_code_now_webhook_secret", ""),
        )
    except ValueError:
        raise BadInputExc("Webhook body verification failed")

    origin_url = payload["origin_url"]
    save_requests = get_save_origin_requests_to_update(origin_url=origin_url)

    if save_requests.count() > 0:
        save_requests_info = update_save_origin_requests_from_queryset(save_requests)
        scheduled = schedule_origins_recurrent_visits(save_requests_info)
        message = f"Status of Save Code Now request updated for origin {origin_url}."
        if scheduled:
            message += "\nOrigin was also scheduled for recurrent visits."
    else:
        message = f"No Save Code Now request to update for origin {origin_url}"

    return HttpResponse(message)
