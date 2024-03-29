# Copyright (C) 2020-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.db import models


class OIDCUserOfflineTokens(models.Model):
    """
    Model storing encrypted bearer tokens generated by users.
    """

    user_id = models.CharField(max_length=50)
    creation_date = models.DateTimeField(auto_now_add=True)
    offline_token = models.BinaryField()

    class Meta:
        app_label = "swh_web_auth"
        db_table = "oidc_user_offline_tokens"
