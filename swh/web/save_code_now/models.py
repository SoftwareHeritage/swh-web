# Copyright (C) 2018-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.db import models

from swh.web.utils.typing import SaveOriginRequestInfo


class SaveAuthorizedOrigin(models.Model):
    """
    Model table holding origin urls authorized to be loaded into the archive.
    """

    url = models.CharField(max_length=200, null=False)

    class Meta:
        app_label = "swh_web_save_code_now"
        db_table = "save_authorized_origin"
        indexes = [models.Index(fields=["url"])]

    def __str__(self):
        return self.url


class SaveUnauthorizedOrigin(models.Model):
    """
    Model table holding origin urls not authorized to be loaded into the
    archive.
    """

    url = models.CharField(max_length=200, null=False)

    class Meta:
        app_label = "swh_web_save_code_now"
        db_table = "save_unauthorized_origin"
        indexes = [models.Index(fields=["url"])]

    def __str__(self):
        return self.url


SAVE_REQUEST_ACCEPTED = "accepted"
SAVE_REQUEST_REJECTED = "rejected"
SAVE_REQUEST_PENDING = "pending"

SAVE_REQUEST_STATUS = [
    (SAVE_REQUEST_ACCEPTED, SAVE_REQUEST_ACCEPTED),
    (SAVE_REQUEST_REJECTED, SAVE_REQUEST_REJECTED),
    (SAVE_REQUEST_PENDING, SAVE_REQUEST_PENDING),
]

SAVE_TASK_NOT_CREATED = "not created"
SAVE_TASK_NOT_YET_SCHEDULED = "not yet scheduled"
SAVE_TASK_SCHEDULED = "scheduled"
SAVE_TASK_SUCCEEDED = "succeeded"
SAVE_TASK_FAILED = "failed"
SAVE_TASK_RUNNING = "running"

SAVE_TASK_STATUS = [
    (SAVE_TASK_NOT_CREATED, SAVE_TASK_NOT_CREATED),
    (SAVE_TASK_NOT_YET_SCHEDULED, SAVE_TASK_NOT_YET_SCHEDULED),
    (SAVE_TASK_SCHEDULED, SAVE_TASK_SCHEDULED),
    (SAVE_TASK_SUCCEEDED, SAVE_TASK_SUCCEEDED),
    (SAVE_TASK_FAILED, SAVE_TASK_FAILED),
    (SAVE_TASK_RUNNING, SAVE_TASK_RUNNING),
]

VISIT_STATUS_CREATED = "created"
VISIT_STATUS_ONGOING = "ongoing"
VISIT_STATUS_FULL = "full"
VISIT_STATUS_PARTIAL = "partial"
VISIT_STATUS_NOT_FOUND = "not_found"
VISIT_STATUS_FAILED = "failed"

VISIT_STATUSES = [
    (VISIT_STATUS_CREATED, VISIT_STATUS_CREATED),
    (VISIT_STATUS_ONGOING, VISIT_STATUS_ONGOING),
    (VISIT_STATUS_FULL, VISIT_STATUS_FULL),
    (VISIT_STATUS_PARTIAL, VISIT_STATUS_PARTIAL),
    (VISIT_STATUS_NOT_FOUND, VISIT_STATUS_NOT_FOUND),
    (VISIT_STATUS_FAILED, VISIT_STATUS_FAILED),
]


class SaveOriginRequest(models.Model):
    """
    Model table holding all the save origin requests issued by users.
    """

    id = models.BigAutoField(primary_key=True)
    request_date = models.DateTimeField(auto_now_add=True)
    visit_type = models.CharField(max_length=200, null=False)
    visit_status = models.TextField(choices=VISIT_STATUSES, null=True)
    origin_url = models.CharField(max_length=200, null=False)
    status = models.TextField(choices=SAVE_REQUEST_STATUS, default=SAVE_REQUEST_PENDING)
    loading_task_id = models.IntegerField(default=-1)
    visit_date = models.DateTimeField(null=True)
    loading_task_status = models.TextField(
        choices=SAVE_TASK_STATUS, default=SAVE_TASK_NOT_CREATED
    )
    # store ids of users that submitted the request as string list
    user_ids = models.TextField(null=True)
    note = models.TextField(null=True)
    from_webhook = models.BooleanField(default=False)
    webhook_origin = models.CharField(max_length=200, null=True)
    # if None, no try to retrieve the snapshot has been performed
    # if empty string, try to retrieve the snapshot has been performed but none was found
    snapshot_swhid = models.CharField(max_length=200, null=True)

    class Meta:
        app_label = "swh_web_save_code_now"
        db_table = "save_origin_request"
        ordering = ["-id"]
        indexes = [models.Index(fields=["origin_url", "status"])]

    def to_dict(self) -> SaveOriginRequestInfo:
        """Map the request save model object to a json serializable dict.

        Returns:
            The corresponding SaveOriginRequetsInfo json serializable dict.

        """
        visit_date = self.visit_date
        return SaveOriginRequestInfo(
            id=self.id,
            origin_url=self.origin_url,
            visit_type=self.visit_type,
            save_request_date=self.request_date.isoformat(),
            save_request_status=self.status,
            save_task_status=self.loading_task_status,
            visit_status=self.visit_status,
            visit_date=visit_date.isoformat() if visit_date else None,
            loading_task_id=self.loading_task_id,
            note=self.note,
            from_webhook=self.from_webhook,
            webhook_origin=self.webhook_origin,
            snapshot_swhid=self.snapshot_swhid or None,
        )

    def __str__(self) -> str:
        return str(self.to_dict())
