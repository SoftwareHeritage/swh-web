# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from datetime import datetime
from typing import Optional

from django.contrib.auth.models import User


class OIDCUser(User):
    """
    Custom User proxy model for remote users storing OpenID Connect
    related data: profile containing authentication tokens.

    The model is also not saved to database as all users are already stored
    in the Keycloak one.
    """

    # OIDC subject identifier
    sub: str = ""

    # OIDC tokens and session related data, only relevant when a user
    # authenticates from a web browser
    access_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    id_token: Optional[str] = None
    refresh_token: Optional[str] = None
    refresh_expires_at: Optional[datetime] = None
    scope: Optional[str] = None
    session_state: Optional[str] = None

    class Meta:
        app_label = "swh.web.auth"
        proxy = True

    def save(self, **kwargs):
        """
        Override django.db.models.Model.save to avoid saving the remote
        users to web application database.
        """
        pass
