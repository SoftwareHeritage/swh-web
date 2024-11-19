# Copyright (C) 2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from __future__ import annotations

import uuid

from django.db import models


class SaveBulkRequest(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4, unique=True, primary_key=True, editable=False
    )
    request_date = models.DateTimeField(auto_now_add=True)
    user_id = models.CharField(max_length=50, null=False)

    class Meta:
        app_label = "swh_web_save_bulk"
        db_table = "save_bulk_request"
        ordering = ["-id"]

    objects: models.Manager[SaveBulkRequest]


class SaveBulkOrigin(models.Model):
    id = models.BigAutoField(primary_key=True)
    origin_url = models.CharField(max_length=4096, null=False)
    visit_type = models.CharField(max_length=30, null=False)
    requests = models.ManyToManyField(SaveBulkRequest)

    class Meta:
        app_label = "swh_web_save_bulk"
        db_table = "save_bulk_origin"
        ordering = ["-id"]
        indexes = [models.Index(fields=["origin_url", "visit_type"])]
        constraints = [
            models.UniqueConstraint(
                fields=["origin_url", "visit_type"],
                name="unicity",
            ),
        ]

    objects: models.Manager[SaveBulkOrigin]
