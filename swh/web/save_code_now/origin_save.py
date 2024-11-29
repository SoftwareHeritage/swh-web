# Copyright (C) 2018-2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from datetime import datetime, timedelta, timezone
from functools import lru_cache
import logging
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import quote, urlparse

import requests

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import URLValidator
from django.db.models import Q, QuerySet
from django.utils.html import escape

from swh.model.hashutil import hash_to_bytes
from swh.model.swhids import CoreSWHID, ObjectType
from swh.scheduler.model import ListedOrigin, Task, TaskRun
from swh.scheduler.utils import create_oneshot_task
from swh.web.config import get_config, scheduler
from swh.web.save_code_now.models import (
    SAVE_REQUEST_ACCEPTED,
    SAVE_REQUEST_PENDING,
    SAVE_REQUEST_REJECTED,
    SAVE_TASK_FAILED,
    SAVE_TASK_PENDING,
    SAVE_TASK_RUNNING,
    SAVE_TASK_SCHEDULED,
    SAVE_TASK_SUCCEEDED,
    VISIT_STATUS_CREATED,
    VISIT_STATUS_FULL,
    VISIT_STATUS_ONGOING,
    VISIT_STATUS_PARTIAL,
    SaveAuthorizedOrigin,
    SaveOriginRequest,
    SaveUnauthorizedOrigin,
)
from swh.web.utils import archive, parse_iso8601_date_to_utc
from swh.web.utils.exc import BadInputExc, ForbiddenExc, NotFoundExc
from swh.web.utils.typing import OriginExistenceCheckInfo, SaveOriginRequestInfo

logger = logging.getLogger(__name__)

# Number of days in the past to lookup for information
MAX_THRESHOLD_DAYS = 30

# Non terminal visit statuses which needs updates
NON_TERMINAL_STATUSES = [
    VISIT_STATUS_CREATED,
    VISIT_STATUS_ONGOING,
]

# minimum interval in minutes between two webhook save requests for a same origin
WEBHOOK_REQUEST_COOLDOWN_INTERVAL = get_config().get(
    "webhook_request_cooldown_interval", 60
)


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
_visit_type_task = {
    "git": "load-git",
    "hg": "load-hg",
    "svn": "load-svn",
    "cvs": "load-cvs",
    "bzr": "load-bzr",
}


_visit_type_task_privileged = {
    "archives": "load-archive-files",
}


# map scheduler task status to origin save status
_save_task_status = {
    "next_run_not_scheduled": SAVE_TASK_PENDING,
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


@lru_cache()
def get_scheduler_load_task_types() -> List[str]:
    task_types = scheduler().get_task_types()
    return [t.type for t in task_types if t.type.startswith("load")]


def get_savable_visit_types_dict(privileged_user: bool = False) -> Dict:
    """Returned the supported task types the user has access to.

    Args:
        privileged_user: Flag to determine if all visit types should be returned or not.
          Default to False to only list unprivileged visit types.

    Returns:
        the dict of supported visit types for the user

    """
    if privileged_user:
        task_types = {**_visit_type_task, **_visit_type_task_privileged}
    else:
        task_types = _visit_type_task

    # filter visit types according to scheduler load task types if available
    try:
        load_task_types = get_scheduler_load_task_types()
        assert load_task_types, "Empty load task types from scheduler"
        return {k: v for k, v in task_types.items() if v in load_task_types}
    except Exception as exc:
        logger.warning(
            "Could not retrieve load task types from the scheduler. "
            "Fall back to the default hardcoded list. Error was: %s",
            exc,
        )
        return task_types


def get_savable_visit_types(privileged_user: bool = False) -> List[str]:
    """Return the list of visit types the user can perform save requests on.

    Args:
        privileged_user: Flag to determine if all visit types should be returned or not.
          Default to False to only list unprivileged visit types.

    Returns:
        the list of saveable visit types

    """

    return sorted(list(get_savable_visit_types_dict(privileged_user).keys()))


def _check_visit_type_savable(visit_type: str, privileged_user: bool = False) -> None:
    visit_type_tasks = get_savable_visit_types(privileged_user)
    if visit_type not in visit_type_tasks:
        allowed_visit_types = ", ".join(visit_type_tasks)
        raise BadInputExc(
            f"Visit of type {visit_type} cannot be saved! "
            f"Allowed types are the following: {allowed_visit_types}"
        )


_validate_url = URLValidator(
    schemes=["http", "https", "svn", "git", "rsync", "pserver", "ssh", "bzr", "ftp"]
)


def validate_origin_url(origin_url: str) -> None:
    """Check an origin URL is well formed and does not contain password.

    Args:
        origin_url: The URL to check

    Raises:
        BadInputExc: if one of the checks failed
    """
    try:
        _validate_url(quote(origin_url, safe=":/@%+"))
    except ValidationError:
        raise BadInputExc(
            f"The provided origin URL '{escape(origin_url)}' is not valid!"
        )

    parsed_url = urlparse(origin_url)
    if parsed_url.password not in (None, "", "anonymous", "guest", "password"):
        raise BadInputExc(
            "The provided origin URL contains a password and cannot be "
            "accepted for security reasons."
        )


def origin_exists(origin_url: str) -> OriginExistenceCheckInfo:
    """Check the origin url for existence. If it exists, extract some more useful
    information on the origin.

    """
    resp = requests.head(origin_url, allow_redirects=True)
    exists = resp.ok
    content_length: Optional[int] = None
    last_modified: Optional[str] = None
    if exists:
        # Also process X-Archive-Orig-* headers in case the URL targets the
        # Internet Archive.
        size_ = resp.headers.get(
            "Content-Length", resp.headers.get("X-Archive-Orig-Content-Length")
        )
        content_length = int(size_) if size_ else None
        try:
            date_str = resp.headers.get(
                "Last-Modified", resp.headers.get("X-Archive-Orig-Last-Modified", "")
            )
            date = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %Z")
            last_modified = date.isoformat()
        except ValueError:
            # if not provided or not parsable as per the expected format, keep it None
            pass

    return OriginExistenceCheckInfo(
        origin_url=origin_url,
        exists=exists,
        last_modified=last_modified,
        content_length=content_length,
    )


def _check_origin_exists(url: str) -> OriginExistenceCheckInfo:
    """Ensure an URL exists, if not raise an explicit message."""
    metadata = origin_exists(url)
    if not metadata["exists"]:
        raise BadInputExc(f"The provided url ({escape(url)}) does not exist!")

    return metadata


def _get_visit_info_for_save_request(
    save_request: SaveOriginRequest,
) -> Tuple[Optional[datetime], Optional[str], Optional[str]]:
    """Retrieve visit information out of a save request

    Args:
        save_request: Input save origin request to retrieve information for.

    Returns:
        Tuple of (visit date, optional visit status, optional snapshot id)
        for such save origin request
    """
    visit_date = None
    visit_status = None
    snapshot_id = None
    origin = save_request.origin_url
    ovs = archive.origin_visit_find_by_date(origin, save_request.request_date)
    if ovs:
        visit_date = parse_iso8601_date_to_utc(ovs["date"])
        visit_status = ovs["status"]
        snapshot_id = ovs["snapshot"]
    return visit_date, visit_status, snapshot_id


def _check_visit_update_status(
    save_request: SaveOriginRequest,
) -> Tuple[Optional[datetime], Optional[str], Optional[str]]:
    """Given a save request, determine whether a save request was successful or failed.

    Args:
        save_request: Input save origin request to retrieve information for.

    Returns:
        Tuple of (optional visit date, optional visit status, optional save task status)
        for such save request origin

    """
    visit_date, visit_status, _ = _get_visit_info_for_save_request(save_request)
    loading_task_status = None
    if visit_date and visit_status in ("full", "partial"):
        # visit has been performed, mark the saving task as succeeded
        loading_task_status = SAVE_TASK_SUCCEEDED
    elif visit_status in ("created", "ongoing"):
        # visit is currently running
        loading_task_status = SAVE_TASK_RUNNING
    elif visit_status in ("not_found", "failed"):
        loading_task_status = SAVE_TASK_FAILED
    else:
        time_now = datetime.now(tz=timezone.utc)
        time_delta = time_now - save_request.request_date
        # consider the task as failed if it is still in scheduled state
        # 30 days after its submission
        if time_delta.days > MAX_THRESHOLD_DAYS:
            loading_task_status = SAVE_TASK_FAILED
    return visit_date, visit_status, loading_task_status


def _compute_task_loading_status(
    task: Optional[Task] = None,
    task_run: Optional[TaskRun] = None,
) -> Optional[str]:
    loading_task_status: Optional[str] = None
    # First determine the loading task status out of task information
    if task:
        loading_task_status = _save_task_status[task.status]
        if task_run:
            loading_task_status = _save_task_run_status[task_run.status]

    return loading_task_status


def _update_save_request_info(
    save_request: SaveOriginRequest,
    task: Optional[Task] = None,
    task_run: Optional[TaskRun] = None,
) -> SaveOriginRequestInfo:
    """Update save request information out of the visit status and fallback to the task and
    task_run information if the visit status is missing.

    Args:
        save_request: Save request
        task: Associated scheduler task information about the save request
        task_run: Most recent run occurrence of the associated task

    Returns:
        Summary of the save request information updated.

    """
    must_save = False

    # To determine the save code now request's final status, the visit date must be set
    # and the visit status must be a final one. Once they do, the save code now is
    # definitely done.
    if (
        not save_request.visit_date
        or not save_request.visit_status
        or save_request.visit_status in NON_TERMINAL_STATUSES
    ):
        visit_date, visit_status, loading_task_status = _check_visit_update_status(
            save_request
        )

        if not loading_task_status:  # fallback when not provided
            loading_task_status = _compute_task_loading_status(task, task_run)

        if visit_date != save_request.visit_date:
            must_save = True
            save_request.visit_date = visit_date

        if visit_status != save_request.visit_status:
            must_save = True
            save_request.visit_status = visit_status

        if (
            loading_task_status is not None
            and loading_task_status != save_request.loading_task_status
        ):
            must_save = True
            save_request.loading_task_status = loading_task_status

    # Try to get snapshot identifier associated to the save request
    if (
        save_request.visit_status in (VISIT_STATUS_PARTIAL, VISIT_STATUS_FULL)
        and save_request.snapshot_swhid is None
    ):
        _, _, snapshot_id = _get_visit_info_for_save_request(save_request)

        save_request.snapshot_swhid = (
            str(
                CoreSWHID(
                    object_type=ObjectType.SNAPSHOT,
                    object_id=hash_to_bytes(snapshot_id),
                )
            )
            if snapshot_id
            # snapshot not found, set its id to empty in database to avoid querying it again
            else ""
        )
        must_save = True

    if must_save:
        save_request.save()

    sr_dict = save_request.to_dict()
    if task:
        sr_dict["next_run"] = task.next_run

    return sr_dict


def create_save_origin_request(
    visit_type: str,
    origin_url: str,
    privileged_user: bool = False,
    user_id: Optional[int] = None,
    from_webhook: bool = False,
    webhook_origin: Optional[str] = None,
    **kwargs,
) -> SaveOriginRequestInfo:
    """Create a loading task to save a software origin into the archive.

    This function aims to create a software origin loading task through the use of the
    swh-scheduler component.

    First, some checks are performed to see if the visit type and origin url are valid
    but also if the the save request can be accepted. For the 'archives' visit type,
    this also ensures the artifacts actually exists. If those checks passed, the loading
    task is then created. Otherwise, the save request is put in pending or rejected
    state.

    All the submitted save requests are logged into the swh-web database to keep track
    of them.

    Args:
        visit_type: the type of visit to perform (e.g. git, hg, svn, archives, ...)
        origin_url: the url of the origin to save
        privileged: Whether the user has some more privilege than other (bypass
          review, access to privileged other visit types)
        user_id: User identifier (provided when authenticated)
        from_webhook: Indicates if the save request is created from a webhook receiver
        webhook_origin: Indicates which forge type sent the webhook
        kwargs: Optional parameters (e.g. artifact_url, artifact_filename,
          artifact_version)

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
              **not created**, **pending**, **scheduled**, **running**,
              **succeeded** or **failed**

    """
    visit_type_tasks = get_savable_visit_types_dict(privileged_user)
    _check_visit_type_savable(visit_type, privileged_user)
    validate_origin_url(origin_url)

    # if all checks passed so far, we can try and save the origin
    save_request_status = can_save_origin(origin_url, privileged_user)
    task = None

    # if the origin save request is accepted, create a scheduler
    # task to load it into the archive
    if save_request_status == SAVE_REQUEST_ACCEPTED:
        # create a task with high priority
        task_kwargs: Dict[str, Any] = {
            "priority": "high",
            "url": origin_url,
        }
        if visit_type == "archives":
            # extra arguments for that type are required
            archives_data = kwargs.get("archives_data", [])
            if not archives_data:
                raise BadInputExc(
                    "Artifacts data are missing for the archives visit type."
                )
            artifacts = []
            for artifact in archives_data:
                artifact_url = artifact.get("artifact_url")
                artifact_version = artifact.get("artifact_version")
                if not artifact_url or not artifact_version:
                    raise BadInputExc("Missing url or version for an artifact to load.")
                metadata = _check_origin_exists(artifact_url)
                artifacts.append(
                    {
                        "url": artifact_url,
                        "version": artifact_version,
                        "time": metadata["last_modified"],
                        "length": metadata["content_length"],
                    }
                )
            task_kwargs = dict(**task_kwargs, artifacts=artifacts, snapshot_append=True)
        sor = None
        # get list of previously submitted save requests (most recent first)
        current_sors = list(
            SaveOriginRequest.objects.filter(
                visit_type=visit_type, origin_url=origin_url, from_webhook=from_webhook
            ).order_by("-request_date")
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
                tasks = scheduler().get_tasks([sor.loading_task_id])
                task = tasks[0] if tasks else None
                task_runs = scheduler().get_task_runs([sor.loading_task_id])
                task_run = task_runs[0] if task_runs else None
                save_request_info = _update_save_request_info(sor, task, task_run)
                task_status = save_request_info["save_task_status"]
                # create a new scheduler task only if the previous one has been
                # already or is currently executed
                if task_status in (
                    SAVE_TASK_FAILED,
                    SAVE_TASK_SUCCEEDED,
                    SAVE_TASK_RUNNING,
                ):
                    can_create_task = True
                else:
                    can_create_task = False

                if from_webhook and task:
                    # a scheduler task whose execution is in the future has already been
                    # created for that webhook save request, no need to recreate a new one
                    if task.next_run > datetime.now(tz=timezone.utc):
                        can_create_task = False

        if can_create_task:
            next_run = None
            if from_webhook and sor:
                date_diff = datetime.now(tz=timezone.utc) - sor.request_date
                date_diff_seconds = int(date_diff.total_seconds())
                if date_diff_seconds // 60 < WEBHOOK_REQUEST_COOLDOWN_INTERVAL:
                    # if previous webhook save request has been submitted recently,
                    # set execution of the new one in the future to avoid creating
                    # too many scheduler tasks
                    next_run = sor.request_date + timedelta(
                        minutes=WEBHOOK_REQUEST_COOLDOWN_INTERVAL
                    )

            # effectively create the scheduler task
            task = create_oneshot_task(
                visit_type_tasks[visit_type], next_run=next_run, **task_kwargs
            )

            task = scheduler().create_tasks([task])[0]
            assert task.id is not None

            # pending save request has been accepted
            if sor and sor.status != SAVE_REQUEST_ACCEPTED:
                sor.status = SAVE_REQUEST_ACCEPTED
                sor.loading_task_id = task.id
                sor.save()
            else:
                sor = SaveOriginRequest.objects.create(
                    visit_type=visit_type,
                    origin_url=origin_url,
                    status=save_request_status,
                    loading_task_id=task.id,
                    user_ids=f'"{user_id}"' if user_id else None,
                    from_webhook=from_webhook,
                    webhook_origin=webhook_origin,
                )

    # save request must be manually reviewed for acceptation
    elif save_request_status == SAVE_REQUEST_PENDING:
        # check if there is already such a save request already submitted,
        # no need to add it to the database in that case
        try:
            sor = SaveOriginRequest.objects.get(
                visit_type=visit_type, origin_url=origin_url, status=save_request_status
            )
            user_ids = sor.user_ids if sor.user_ids is not None else ""
            if user_id is not None and f'"{user_id}"' not in user_ids:
                # update user ids list
                sor.user_ids = f'{sor.user_ids},"{user_id}"'
                sor.save()

        # if not add it to the database
        except ObjectDoesNotExist:
            sor = SaveOriginRequest.objects.create(
                visit_type=visit_type,
                origin_url=origin_url,
                status=save_request_status,
                user_ids=f'"{user_id}"' if user_id else None,
                from_webhook=from_webhook,
                webhook_origin=webhook_origin,
            )
    # origin cannot be saved as its url is blacklisted,
    # log the request to the database anyway
    else:
        sor = SaveOriginRequest.objects.create(
            visit_type=visit_type,
            origin_url=origin_url,
            status=save_request_status,
            user_ids=f'"{user_id}"' if user_id else None,
            from_webhook=from_webhook,
            webhook_origin=webhook_origin,
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
        :func:`swh.web.save_code_now.origin_save.create_save_origin_request`

    """
    task_ids = []
    for sor in requests_queryset:
        task_ids.append(sor.loading_task_id)
    save_requests = []
    if task_ids:
        try:
            tasks_list = scheduler().get_tasks(task_ids)
            tasks = {task.id: task for task in tasks_list if task.id is not None}
            task_runs_list = scheduler().get_task_runs(list(tasks.keys()))
            task_runs = {
                task_run.task: task_run
                for task_run in task_runs_list
                if task_run.task is not None
            }
        except Exception:
            # allow to avoid mocking api GET responses for /origin/save endpoint when
            # running cypress tests as scheduler is not available
            tasks = {}
            task_runs = {}
        for sor in requests_queryset:
            sr_dict = _update_save_request_info(
                sor,
                tasks.get(sor.loading_task_id),
                task_runs.get(sor.loading_task_id),
            )
            save_requests.append(sr_dict)
    return save_requests


def get_save_origin_requests_to_update(origin_url: Optional[str] = None) -> QuerySet:
    """Get the set of recent save origin requests that have non terminal statuses
    and require update.

    Non-terminal requests are those whose status is **accepted** and their task status are
    either **created**, **pending**, **scheduled** or **running**.

    Args:
        origin_url: If provided, only return requests to update for the given origin URL

    Returns:
        Django queryset of requests to update
    """
    pivot_date = datetime.now(tz=timezone.utc) - timedelta(days=MAX_THRESHOLD_DAYS)
    save_requests = SaveOriginRequest.objects.filter(
        # Retrieve accepted request statuses (all statuses)
        Q(status=SAVE_REQUEST_ACCEPTED),
        # those without the required information we need to update
        Q(visit_date__isnull=True)
        | Q(visit_status__isnull=True)
        | Q(visit_status__in=NON_TERMINAL_STATUSES),
        # limit results to recent ones (that is roughly 30 days old at best)
        Q(request_date__gte=pivot_date),
    )
    if origin_url:
        save_requests = save_requests.filter(origin_url__exact=origin_url)
    return save_requests


def refresh_save_origin_request_statuses() -> List[SaveOriginRequestInfo]:
    """Refresh non-terminal save origin requests (SOR) in the backend.

    Non-terminal SOR are requests whose status is **accepted** and their task status are
    either **created**, **pending**, **scheduled** or **running**.

    This shall compute this list of save requests, checks their status in the scheduler,
    then update those in database.

    Finally, this returns the refreshed information on those save requests.
    """
    save_requests = get_save_origin_requests_to_update()

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
        swh.web.utils.exc.NotFoundExc: no save requests can be found for the
            given origin

    Returns:
        list: A list of save origin requests dict as described in
        :func:`swh.web.save_code_now.origin_save.create_save_origin_request`
    """
    _check_visit_type_savable(visit_type)
    validate_origin_url(origin_url)
    sors = SaveOriginRequest.objects.filter(
        visit_type=visit_type, origin_url=origin_url
    )
    if sors.count() == 0:
        raise NotFoundExc(
            f"No save requests found for visit of type {visit_type} "
            f"on origin with url {origin_url}."
        )
    return update_save_origin_requests_from_queryset(sors)


def get_save_origin_request(request_id: int) -> SaveOriginRequestInfo:
    """
    Get save request with given identifier.

    Args:
        request_id: the save request identifier

    Raises:
        swh.web.utils.exc.NotFoundExc: no save request can be found for the
            given identifier

    Returns:
        A save origin request dict as described in
        :func:`swh.web.save_code_now.origin_save.create_save_origin_request`
    """

    sors = SaveOriginRequest.objects.filter(id=request_id)
    if sors.count() == 0:
        raise NotFoundExc(f"No save request found for id {request_id}.")
    return update_save_origin_requests_from_queryset(sors)[0]


def get_save_origin_task_info(save_request_id: int) -> Dict[str, Any]:
    """
    Get detailed information about an accepted save origin request
    and its associated loading task.

    If the associated loading task info is archived and removed
    from the scheduler database, returns an empty dictionary.

    Args:
        save_request_id: identifier of a save origin request

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
            - **metadata**: any other metadata related to the loading task;
                            typically comes with the error for a failed task
    """
    try:
        save_request = SaveOriginRequest.objects.get(id=save_request_id)
    except ObjectDoesNotExist:
        return {}

    task_info: Dict[str, Any] = {}
    if save_request.note is not None:
        task_info["note"] = save_request.note

    try:
        tasks = scheduler().get_tasks([save_request.loading_task_id])
    except Exception:
        # to avoid mocking GET responses of /save/task/info/ endpoint when running
        # cypress tests as scheduler is not available in that case
        tasks = None

    task = tasks[0] if tasks else None
    if task is None or task.id is None:
        return task_info

    task_runs = scheduler().get_task_runs([task.id])
    task_run = task_runs[0] if task_runs else None
    if task_run is None:
        return task_info
    task_info.update(task_run.to_dict())
    task_info["type"] = task.type
    task_info["arguments"] = task.arguments.to_dict()
    task_info["id"] = task_run.task
    del task_info["task"]
    # Enrich the task info with the loading visit status
    task_info["visit_status"] = save_request.visit_status

    return task_info


def schedule_origins_recurrent_visits(
    save_requests: List[SaveOriginRequestInfo],
) -> int:
    """Schedule recurrent visits of origin URLs submitted to Save Code Now.

    Args:
        save_requests: List of save origin requests from which to schedule
            recurrent visits

    Returns:
        The number of origins that were scheduled for recurrent visits
    """
    lister = scheduler().get_or_create_lister(
        name="save-code-now", instance_name=get_config()["instance_name"]
    )

    assert lister.id

    origins: Set[Tuple[str, str]] = set()
    listed_origins = []
    for save_request in save_requests:
        visit_type = save_request["visit_type"]
        # only deal with git, svn, hg visit types
        if visit_type == "archives":
            continue
        # only keep satisfying visit statuses
        if save_request["visit_status"] not in (
            VISIT_STATUS_PARTIAL,
            VISIT_STATUS_FULL,
        ):
            continue
        origin = save_request["origin_url"]
        # drop duplicates within the same batch
        if (visit_type, origin) in origins:
            continue
        origins.add((visit_type, origin))
        listed_origins.append(
            ListedOrigin(lister_id=lister.id, visit_type=visit_type, url=origin)
        )

    if listed_origins:
        listed_origins = scheduler().record_listed_origins(listed_origins)

    return len(listed_origins)


def has_pending_save_code_now_requests() -> bool:
    """Return :const:`True` if at least one submitted save request requires
    manual validation by staff member."""
    return (
        SaveOriginRequest.objects.filter(status=SAVE_REQUEST_PENDING).first()
        is not None
    )
