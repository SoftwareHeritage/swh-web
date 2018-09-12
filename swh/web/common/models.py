# Copyright (C) 2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.db import models


class SaveAuthorizedOrigin(models.Model):
    """
    Model table holding origin urls authorized to be loaded into the archive.
    """
    url = models.CharField(max_length=200, null=False)

    class Meta:
        app_label = 'swh.web.common'
        db_table = 'save_authorized_origin'

    def __str__(self):
        return self.url


class SaveUnauthorizedOrigin(models.Model):
    """
    Model table holding origin urls not authorized to be loaded into the
    archive.
    """
    url = models.CharField(max_length=200, null=False)

    class Meta:
        app_label = 'swh.web.common'
        db_table = 'save_unauthorized_origin'

    def __str__(self):
        return self.url


SAVE_REQUEST_ACCEPTED = 'accepted'
SAVE_REQUEST_REJECTED = 'rejected'
SAVE_REQUEST_PENDING = 'pending'

SAVE_REQUEST_STATUS = [
    (SAVE_REQUEST_ACCEPTED, SAVE_REQUEST_ACCEPTED),
    (SAVE_REQUEST_REJECTED, SAVE_REQUEST_REJECTED),
    (SAVE_REQUEST_PENDING, SAVE_REQUEST_PENDING)
]


class SaveOriginRequest(models.Model):
    """
    Model table holding all the save origin requests issued by users.
    """
    id = models.BigAutoField(primary_key=True)
    request_date = models.DateTimeField(auto_now_add=True)
    origin_type = models.CharField(max_length=200, null=False)
    origin_url = models.CharField(max_length=200, null=False)
    status = models.TextField(choices=SAVE_REQUEST_STATUS,
                              default=SAVE_REQUEST_PENDING)
    loading_task_id = models.IntegerField(default=-1)
    visit_date = models.DateTimeField(null=True)

    class Meta:
        app_label = 'swh.web.common'
        db_table = 'save_origin_request'
        ordering = ['-id']

    def __str__(self):
        return str({'id': self.id,
                    'request_date': self.request_date,
                    'origin_type': self.origin_type,
                    'origin_url': self.origin_url,
                    'status': self.status,
                    'loading_task_id': self.loading_task_id,
                    'visit_date': self.visit_date})
