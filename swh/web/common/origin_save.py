# Copyright (C) 2018-2021  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from bisect import bisect_right
from datetime import datetime, timedelta, timezone
from itertools import product
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from prometheus_client import Gauge
import requests
import sentry_sdk

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import URLValidator
from django.db.models import QuerySet
from django.utils.html import escape

from swh.scheduler.utils import create_oneshot_task_dict
from swh.web import config
from swh.web.common import archive
from swh.web.common.exc import BadInputExc, ForbiddenExc, NotFoundExc
from swh.web.common.models import (
    SAVE_REQUEST_ACCEPTED,
    SAVE_REQUEST_PENDING,
    SAVE_REQUEST_REJECTED,
    SAVE_TASK_FAILED,
    SAVE_TASK_NOT_CREATED,
    SAVE_TASK_NOT_YET_SCHEDULED,
    SAVE_TASK_RUNNING,
    SAVE_TASK_SCHEDULED,
    SAVE_TASK_SUCCEEDED,
    SaveAuthorizedOrigin,
    SaveOriginRequest,
    SaveUnauthorizedOrigin,
)
from swh.web.common.origin_visits import get_origin_visits
from swh.web.common.typing import (
    OriginExistenceCheckInfo,
    OriginInfo,
    SaveOriginRequestInfo,
)
from swh.web.common.utils import SWH_WEB_METRICS_REGISTRY, parse_iso8601_date_to_utc

scheduler = config.scheduler()

logger = logging.getLogger(__name__)


def get_origin_save_authorized_urls() -> List[str]:
    """
    Get the list of origin url prefixes authorized to be
    immediately loaded into the archive (whitelist).

    Returns:
        list: The list of authorized origin url prefix
    """
    return [origin.url for origin in SaveAuthorizedOrigin.objects.all()]


def get_origin_save_unauthorized_urls() -> List[str]:
    """
    Get the list of origin url prefixes forbidden to be
    loaded into the archive (blacklist).

    Returns:
        list: the list of unauthorized origin url prefix
    """
    return [origin.url for origin in SaveUnauthorizedOrigin.objects.all()]


def can_save_origin(origin_url: str, bypass_pending_review: bool = False) -> str:
    """
    Check if a software origin can be saved into the archive.

    Based on the origin url, the save request will be either:

      * immediately accepted if the url is whitelisted
      * rejected if the url is blacklisted
      * put in pending state for manual review otherwise

    Args:
        origin_url (str): the software origin url to check

    Returns:
        str: the origin save request status, either **accepted**,
        **rejected** or **pending**
    """
    # origin url may be blacklisted
    for url_prefix in get_origin_save_unauthorized_urls():
        if origin_url.startswith(url_prefix):
            return SAVE_REQUEST_REJECTED

    # if the origin url is in the white list, it can be immediately saved
    for url_prefix in get_origin_save_authorized_urls():
        if origin_url.startswith(url_prefix):
            return SAVE_REQUEST_ACCEPTED

    # otherwise, the origin url needs to be manually verified if the user
    # that submitted it does not have special permission
    if bypass_pending_review:
        # mark the origin URL as trusted in that case
        SaveAuthorizedOrigin.objects.get_or_create(url=origin_url)
        return SAVE_REQUEST_ACCEPTED
    else:
        return SAVE_REQUEST_PENDING


# map visit type to scheduler task
# TODO: do not hardcode the task name here (T1157)
_visit_type_task = {"git": "load-git", "hg": "load-hg", "svn": "load-svn"}


# map scheduler task status to origin save status
_save_task_status = {
    "next_run_not_scheduled": SAVE_TASK_NOT_YET_SCHEDULED,
    "next_run_scheduled": SAVE_TASK_SCHEDULED,
    "completed": SAVE_TASK_SUCCEEDED,
    "disabled": SAVE_TASK_FAILED,
}

# map scheduler task_run status to origin save status
_save_task_run_status = {
    "scheduled": SAVE_TASK_SCHEDULED,
    "started": SAVE_TASK_RUNNING,
    "eventful": SAVE_TASK_SUCCEEDED,
    "uneventful": SAVE_TASK_SUCCEEDED,
    "failed": SAVE_TASK_FAILED,
    "permfailed": SAVE_TASK_FAILED,
    "lost": SAVE_TASK_FAILED,
}


def get_savable_visit_types() -> List[str]:
    """
    Get the list of visit types that can be performed
    through a save request.

    Returns:
        list: the list of saveable visit types
    """
    return sorted(list(_visit_type_task.keys()))


def _check_visit_type_savable(visit_type: str) -> None:
    allowed_visit_types = ", ".join(get_savable_visit_types())
    if visit_type not in _visit_type_task:
        raise BadInputExc(
            "Visit of type %s can not be saved! "
            "Allowed types are the following: %s" % (visit_type, allowed_visit_types)
        )


_validate_url = URLValidator(schemes=["http", "https", "svn", "git"])


def _check_origin_url_valid(origin_url: str) -> None:
    try:
        _validate_url(origin_url)
    except ValidationError:
        raise BadInputExc(
            "The provided origin url (%s) is not valid!" % escape(origin_url)
        )


def origin_exists(origin_url: str) -> OriginExistenceCheckInfo:
    """Check the origin url for existence. If it exists, extract some more useful
    information on the origin.

    """
    resp = requests.head(origin_url)
    exists = resp.ok
    content_length: Optional[int] = None
    last_modified: Optional[str] = None
    if exists:
        size_ = resp.headers.get("Content-Length")
        content_length = int(size_) if size_ else None
        last_modified = resp.headers.get("Last-Modified")

    return OriginExistenceCheckInfo(
        origin_url=origin_url,
        exists=exists,
        last_modified=last_modified,
        content_length=content_length,
    )


def _check_origin_exists(origin_url: str) -> None:
    """Ensure the origin exists, if not raise an explicit message."""
    check = origin_exists(origin_url)
    if not check["exists"]:
        raise BadInputExc(
            f"The provided origin url ({escape(origin_url)}) does not exist!"
        )


def _get_visit_info_for_save_request(
    save_request: SaveOriginRequest,
) -> Tuple[Optional[datetime], Optional[str]]:
    """Retrieve visit information out of a save request

    Args:
        save_request: Input save origin request to retrieve information for.

    Returns:
        Tuple of (visit date, optional visit status) for such save request origin

    """
    visit_date = None
    visit_status = None
    time_now = datetime.now(tz=timezone.utc)
    time_delta = time_now - save_request.request_date
    # stop trying to find a visit date one month after save request submission
    # as those requests to storage are expensive and associated loading task
    # surely ended up with errors
    if time_delta.days <= 30:
        try:
            origin_info = archive.lookup_origin(OriginInfo(url=save_request.origin_url))
            origin_visits = get_origin_visits(origin_info)
            visit_dates = [parse_iso8601_date_to_utc(v["date"]) for v in origin_visits]
            i = bisect_right(visit_dates, save_request.request_date)
            if i != len(visit_dates):
                visit_date = visit_dates[i]
                visit_status = origin_visits[i]["status"]
                if visit_status not in ("full", "partial", "not_found"):
                    visit_date = None
        except Exception as exc:
            sentry_sdk.capture_exception(exc)
    return visit_date, visit_status


def _check_visit_update_status(
    save_request: SaveOriginRequest, save_task_status: str
) -> Tuple[Optional[datetime], str]:
    """Given a save request and a save task status, determine whether a save request was
    successful or failed.

    Args:
        save_request: Input save origin request to retrieve information for.

    Returns:
        Tuple of (optional visit date, save task status) for such save request origin

    """
    visit_date, visit_status = _get_visit_info_for_save_request(save_request)
    save_request.visit_date = visit_date
    save_request.visit_status = visit_status
    if visit_date and visit_status in ("full", "partial"):
        # visit has been performed, mark the saving task as succeeded
        save_task_status = SAVE_TASK_SUCCEEDED
    elif visit_status in ("created", "ongoing"):
        # visit is currently running
        save_task_status = SAVE_TASK_RUNNING
    elif visit_status in ("not_found", "failed"):
        save_task_status = SAVE_TASK_FAILED
    else:
        time_now = datetime.now(tz=timezone.utc)
        time_delta = time_now - save_request.request_date
        # consider the task as failed if it is still in scheduled state
        # 30 days after its submission
        if time_delta.days > 30:
            save_task_status = SAVE_TASK_FAILED
    return visit_date, save_task_status


def _update_save_request_info(
    save_request: SaveOriginRequest,
    task: Optional[Dict[str, Any]] = None,
    task_run: Optional[Dict[str, Any]] = None,
) -> SaveOriginRequestInfo:
    """Update save request information out of task and task_run information.

    Args:
        save_request: Save request
        task: Associated scheduler task information about the save request
        task_run: Most recent run occurrence of the associated task

    Returns:
        Summary of the save request information updated.

    """
    must_save = False
    visit_date = save_request.visit_date

    # save task still in scheduler db
    if task:
        save_task_status = _save_task_status[task["status"]]
        if task_run:
            save_task_status = _save_task_run_status[task_run["status"]]

        # Consider request from which a visit date has already been found
        # as succeeded to avoid retrieving it again
        if save_task_status == SAVE_TASK_SCHEDULED and visit_date:
            save_task_status = SAVE_TASK_SUCCEEDED
        if (
            save_task_status in (SAVE_TASK_FAILED, SAVE_TASK_SUCCEEDED)
            and not visit_date
        ):
            visit_date, visit_status = _get_visit_info_for_save_request(save_request)
            save_request.visit_date = visit_date
            save_request.visit_status = visit_status
            if visit_status in ("failed", "not_found"):
                save_task_status = SAVE_TASK_FAILED
            must_save = True
        # Check tasks still marked as scheduled / not yet scheduled
        if save_task_status in (SAVE_TASK_SCHEDULED, SAVE_TASK_NOT_YET_SCHEDULED):
            visit_date, save_task_status = _check_visit_update_status(
                save_request, save_task_status
            )

    # save task may have been archived
    else:
        save_task_status = save_request.loading_task_status
        if save_task_status in (SAVE_TASK_SCHEDULED, SAVE_TASK_NOT_YET_SCHEDULED):
            visit_date, save_task_status = _check_visit_update_status(
                save_request, save_task_status
            )

        else:
            save_task_status = save_request.loading_task_status

    if (
        # avoid to override final loading task status when already found
        # as visit status is no longer checked once a visit date has been found
        save_request.loading_task_status not in (SAVE_TASK_FAILED, SAVE_TASK_SUCCEEDED)
        and save_request.loading_task_status != save_task_status
    ):
        save_request.loading_task_status = save_task_status
        must_save = True

    if must_save:
        save_request.save()

    return save_request.to_dict()


def create_save_origin_request(
    visit_type: str,
    origin_url: str,
    bypass_pending_review: bool = False,
    user_id: Optional[int] = None,
) -> SaveOriginRequestInfo:
    """
    Create a loading task to save a software origin into the archive.

    This function aims to create a software origin loading task
    trough the use of the swh-scheduler component.

    First, some checks are performed to see if the visit type and origin
    url are valid but also if the the save request can be accepted.
    If those checks passed, the loading task is then created.
    Otherwise, the save request is put in pending or rejected state.

    All the submitted save requests are logged into the swh-web
    database to keep track of them.

    Args:
        visit_type: the type of visit to perform (e.g git, hg, svn, ...)
        origin_url: the url of the origin to save

    Raises:
        BadInputExc: the visit type or origin url is invalid or inexistent
        ForbiddenExc: the provided origin url is blacklisted

    Returns:
        dict: A dict describing the save request with the following keys:

            * **visit_type**: the type of visit to perform
            * **origin_url**: the url of the origin
            * **save_request_date**: the date the request was submitted
            * **save_request_status**: the request status, either **accepted**,
              **rejected** or **pending**
            * **save_task_status**: the origin loading task status, either
              **not created**, **not yet scheduled**, **scheduled**,
              **succeed** or **failed**


    """
    _check_visit_type_savable(visit_type)
    _check_origin_url_valid(origin_url)
    # if all checks passed so far, we can try and save the origin
    save_request_status = can_save_origin(origin_url, bypass_pending_review)
    task = None

    # if the origin save request is accepted, create a scheduler
    # task to load it into the archive
    if save_request_status == SAVE_REQUEST_ACCEPTED:
        # create a task with high priority
        kwargs = {
            "priority": "high",
            "url": origin_url,
        }
        sor = None
        # get list of previously sumitted save requests
        current_sors = list(
            SaveOriginRequest.objects.filter(
                visit_type=visit_type, origin_url=origin_url
            )
        )

        can_create_task = False
        # if no save requests previously submitted, create the scheduler task
        if not current_sors:
            can_create_task = True
        else:
            # get the latest submitted save request
            sor = current_sors[0]
            # if it was in pending state, we need to create the scheduler task
            # and update the save request info in the database
            if sor.status == SAVE_REQUEST_PENDING:
                can_create_task = True
            # a task has already been created to load the origin
            elif sor.loading_task_id != -1:
                # get the scheduler task and its status
                tasks = scheduler.get_tasks([sor.loading_task_id])
                task = tasks[0] if tasks else None
                task_runs = scheduler.get_task_runs([sor.loading_task_id])
                task_run = task_runs[0] if task_runs else None
                save_request_info = _update_save_request_info(sor, task, task_run)
                task_status = save_request_info["save_task_status"]
                # create a new scheduler task only if the previous one has been
                # already executed
                if (
                    task_status == SAVE_TASK_FAILED
                    or task_status == SAVE_TASK_SUCCEEDED
                ):
                    can_create_task = True
                    sor = None
                else:
                    can_create_task = False

        if can_create_task:
            # effectively create the scheduler task
            task_dict = create_oneshot_task_dict(_visit_type_task[visit_type], **kwargs)
            task = scheduler.create_tasks([task_dict])[0]

            # pending save request has been accepted
            if sor:
                sor.status = SAVE_REQUEST_ACCEPTED
                sor.loading_task_id = task["id"]
                sor.save()
            else:
                sor = SaveOriginRequest.objects.create(
                    visit_type=visit_type,
                    origin_url=origin_url,
                    status=save_request_status,
                    loading_task_id=task["id"],
                    user_id=str(user_id) if user_id else None,
                )
    # save request must be manually reviewed for acceptation
    elif save_request_status == SAVE_REQUEST_PENDING:
        # check if there is already such a save request already submitted,
        # no need to add it to the database in that case
        try:
            sor = SaveOriginRequest.objects.get(
                visit_type=visit_type, origin_url=origin_url, status=save_request_status
            )
        # if not add it to the database
        except ObjectDoesNotExist:
            sor = SaveOriginRequest.objects.create(
                visit_type=visit_type,
                origin_url=origin_url,
                status=save_request_status,
                user_id=str(user_id) if user_id else None,
            )
    # origin can not be saved as its url is blacklisted,
    # log the request to the database anyway
    else:
        sor = SaveOriginRequest.objects.create(
            visit_type=visit_type,
            origin_url=origin_url,
            status=save_request_status,
            user_id=str(user_id) if user_id else None,
        )

    if save_request_status == SAVE_REQUEST_REJECTED:
        raise ForbiddenExc(
            (
                'The "save code now" request has been rejected '
                "because the provided origin url is blacklisted."
            )
        )

    assert sor is not None
    return _update_save_request_info(sor, task)


def update_save_origin_requests_from_queryset(
    requests_queryset: QuerySet,
) -> List[SaveOriginRequestInfo]:
    """Update all save requests from a SaveOriginRequest queryset, update their status in db
    and return the list of impacted save_requests.

    Args:
        requests_queryset: input SaveOriginRequest queryset

    Returns:
        list: A list of save origin request info dicts as described in
        :func:`swh.web.common.origin_save.create_save_origin_request`

    """
    task_ids = []
    for sor in requests_queryset:
        task_ids.append(sor.loading_task_id)
    save_requests = []
    if task_ids:
        tasks = scheduler.get_tasks(task_ids)
        tasks = {task["id"]: task for task in tasks}
        task_runs = scheduler.get_task_runs(tasks)
        task_runs = {task_run["task"]: task_run for task_run in task_runs}
        for sor in requests_queryset:
            sr_dict = _update_save_request_info(
                sor, tasks.get(sor.loading_task_id), task_runs.get(sor.loading_task_id),
            )
            save_requests.append(sr_dict)
    return save_requests


def refresh_save_origin_request_statuses() -> List[SaveOriginRequestInfo]:
    """Refresh non-terminal save origin requests (SOR) in the backend.

    Non-terminal SOR are requests whose status is **accepted** and their task status are
    either **created**, **not yet scheduled**, **scheduled** or **running**.

    This shall compute this list of SOR, checks their status in the scheduler and
    optionally elasticsearch for their current status. Then update those in db.

    Finally, this returns the refreshed information on those SOR.

    """
    non_terminal_statuses = (
        SAVE_TASK_NOT_CREATED,
        SAVE_TASK_NOT_YET_SCHEDULED,
        SAVE_TASK_RUNNING,
        SAVE_TASK_SCHEDULED,
    )
    save_requests = SaveOriginRequest.objects.filter(
        status=SAVE_REQUEST_ACCEPTED, loading_task_status__in=non_terminal_statuses
    )
    # update save request statuses
    return (
        update_save_origin_requests_from_queryset(save_requests)
        if save_requests.count() > 0
        else []
    )


def get_save_origin_requests(
    visit_type: str, origin_url: str
) -> List[SaveOriginRequestInfo]:
    """
    Get all save requests for a given software origin.

    Args:
        visit_type: the type of visit
        origin_url: the url of the origin

    Raises:
        BadInputExc: the visit type or origin url is invalid
        swh.web.common.exc.NotFoundExc: no save requests can be found for the
            given origin

    Returns:
        list: A list of save origin requests dict as described in
        :func:`swh.web.common.origin_save.create_save_origin_request`
    """
    _check_visit_type_savable(visit_type)
    _check_origin_url_valid(origin_url)
    sors = SaveOriginRequest.objects.filter(
        visit_type=visit_type, origin_url=origin_url
    )
    if sors.count() == 0:
        raise NotFoundExc(
            f"No save requests found for visit of type {visit_type} "
            f"on origin with url {origin_url}."
        )
    return update_save_origin_requests_from_queryset(sors)


def get_save_origin_task_info(
    save_request_id: int, full_info: bool = True
) -> Dict[str, Any]:
    """
    Get detailed information about an accepted save origin request
    and its associated loading task.

    If the associated loading task info is archived and removed
    from the scheduler database, returns an empty dictionary.

    Args:
        save_request_id: identifier of a save origin request
        full_info: whether to return detailed info for staff users

    Returns:
        A dictionary with the following keys:

            - **type**: loading task type
            - **arguments**: loading task arguments
            - **id**: loading task database identifier
            - **backend_id**: loading task celery identifier
            - **scheduled**: loading task scheduling date
            - **ended**: loading task termination date
            - **status**: loading task execution status
            - **visit_status**: Actual visit status

        Depending on the availability of the task logs in the elasticsearch
        cluster of Software Heritage, the returned dictionary may also
        contain the following keys:

            - **name**: associated celery task name
            - **message**: relevant log message from task execution
            - **duration**: task execution time (only if it succeeded)
            - **worker**: name of the worker that executed the task
    """
    try:
        save_request = SaveOriginRequest.objects.get(id=save_request_id)
    except ObjectDoesNotExist:
        return {}

    task = scheduler.get_tasks([save_request.loading_task_id])
    task = task[0] if task else None
    if task is None:
        return {}

    task_run = scheduler.get_task_runs([task["id"]])
    task_run = task_run[0] if task_run else None
    if task_run is None:
        return {}
    task_run["type"] = task["type"]
    task_run["arguments"] = task["arguments"]
    task_run["id"] = task_run["task"]
    del task_run["task"]
    del task_run["metadata"]
    # Enrich the task run with the loading visit status
    task_run["visit_status"] = save_request.visit_status

    es_workers_index_url = config.get_config()["es_workers_index_url"]
    if not es_workers_index_url:
        return task_run
    es_workers_index_url += "/_search"

    if save_request.visit_date:
        min_ts = save_request.visit_date
        max_ts = min_ts + timedelta(days=7)
    else:
        min_ts = save_request.request_date
        max_ts = min_ts + timedelta(days=30)
    min_ts_unix = int(min_ts.timestamp()) * 1000
    max_ts_unix = int(max_ts.timestamp()) * 1000

    save_task_status = _save_task_status[task["status"]]
    priority = "3" if save_task_status == SAVE_TASK_FAILED else "6"

    query = {
        "bool": {
            "must": [
                {"match_phrase": {"priority": {"query": priority}}},
                {"match_phrase": {"swh_task_id": {"query": task_run["backend_id"]}}},
                {
                    "range": {
                        "@timestamp": {
                            "gte": min_ts_unix,
                            "lte": max_ts_unix,
                            "format": "epoch_millis",
                        }
                    }
                },
            ]
        }
    }

    try:
        response = requests.post(
            es_workers_index_url,
            json={"query": query, "sort": ["@timestamp"]},
            timeout=30,
        )
        results = json.loads(response.text)
        if results["hits"]["total"]["value"] >= 1:
            task_run_info = results["hits"]["hits"][-1]["_source"]
            if "swh_logging_args_runtime" in task_run_info:
                duration = task_run_info["swh_logging_args_runtime"]
                task_run["duration"] = duration
            if "message" in task_run_info:
                task_run["message"] = task_run_info["message"]
            if "swh_logging_args_name" in task_run_info:
                task_run["name"] = task_run_info["swh_logging_args_name"]
            elif "swh_task_name" in task_run_info:
                task_run["name"] = task_run_info["swh_task_name"]
            if "hostname" in task_run_info:
                task_run["worker"] = task_run_info["hostname"]
            elif "host" in task_run_info:
                task_run["worker"] = task_run_info["host"]
    except Exception as exc:
        logger.warning("Request to Elasticsearch failed\n%s", exc)
        sentry_sdk.capture_exception(exc)

    if not full_info:
        for field in ("id", "backend_id", "worker"):
            # remove some staff only fields
            task_run.pop(field, None)
        if "message" in task_run and "Loading failure" in task_run["message"]:
            # hide traceback for non staff users, only display exception
            message_lines = task_run["message"].split("\n")
            message = ""
            for line in message_lines:
                if line.startswith("Traceback"):
                    break
                message += f"{line}\n"
            message += message_lines[-1]
            task_run["message"] = message

    return task_run


SUBMITTED_SAVE_REQUESTS_METRIC = "swh_web_submitted_save_requests"

_submitted_save_requests_gauge = Gauge(
    name=SUBMITTED_SAVE_REQUESTS_METRIC,
    documentation="Number of submitted origin save requests",
    labelnames=["status", "visit_type"],
    registry=SWH_WEB_METRICS_REGISTRY,
)


ACCEPTED_SAVE_REQUESTS_METRIC = "swh_web_accepted_save_requests"

_accepted_save_requests_gauge = Gauge(
    name=ACCEPTED_SAVE_REQUESTS_METRIC,
    documentation="Number of accepted origin save requests",
    labelnames=["load_task_status", "visit_type"],
    registry=SWH_WEB_METRICS_REGISTRY,
)


# Metric on the delay of save code now request per status and visit_type. This is the
# time difference between the save code now is requested and the time it got ingested.
ACCEPTED_SAVE_REQUESTS_DELAY_METRIC = "swh_web_save_requests_delay_seconds"

_accepted_save_requests_delay_gauge = Gauge(
    name=ACCEPTED_SAVE_REQUESTS_DELAY_METRIC,
    documentation="Save Requests Duration",
    labelnames=["load_task_status", "visit_type"],
    registry=SWH_WEB_METRICS_REGISTRY,
)


def compute_save_requests_metrics() -> None:
    """Compute Prometheus metrics related to origin save requests:

    - Number of submitted origin save requests
    - Number of accepted origin save requests
    - Save Code Now requests delay between request time and actual time of ingestion

    """

    request_statuses = (
        SAVE_REQUEST_ACCEPTED,
        SAVE_REQUEST_REJECTED,
        SAVE_REQUEST_PENDING,
    )

    load_task_statuses = (
        SAVE_TASK_NOT_CREATED,
        SAVE_TASK_NOT_YET_SCHEDULED,
        SAVE_TASK_SCHEDULED,
        SAVE_TASK_SUCCEEDED,
        SAVE_TASK_FAILED,
        SAVE_TASK_RUNNING,
    )

    visit_types = get_savable_visit_types()

    labels_set = product(request_statuses, visit_types)

    for labels in labels_set:
        _submitted_save_requests_gauge.labels(*labels).set(0)

    labels_set = product(load_task_statuses, visit_types)

    for labels in labels_set:
        _accepted_save_requests_gauge.labels(*labels).set(0)

    duration_load_task_statuses = (
        SAVE_TASK_FAILED,
        SAVE_TASK_SUCCEEDED,
    )

    for labels in product(duration_load_task_statuses, visit_types):
        _accepted_save_requests_delay_gauge.labels(*labels).set(0)

    for sor in SaveOriginRequest.objects.all():
        if sor.status == SAVE_REQUEST_ACCEPTED:
            _accepted_save_requests_gauge.labels(
                load_task_status=sor.loading_task_status, visit_type=sor.visit_type,
            ).inc()

        _submitted_save_requests_gauge.labels(
            status=sor.status, visit_type=sor.visit_type
        ).inc()

        if (
            sor.loading_task_status in (SAVE_TASK_SUCCEEDED, SAVE_TASK_FAILED)
            and sor.visit_date is not None
            and sor.request_date is not None
        ):
            delay = sor.visit_date.timestamp() - sor.request_date.timestamp()
            _accepted_save_requests_delay_gauge.labels(
                load_task_status=sor.loading_task_status, visit_type=sor.visit_type,
            ).inc(delay)
