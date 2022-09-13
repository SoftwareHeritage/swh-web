# Copyright (C) 2021-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from typing import Dict, List, Tuple

from django.contrib.auth import get_user_model

from swh.web.auth.utils import (
    ADD_FORGE_MODERATOR_PERMISSION,
    ADMIN_LIST_DEPOSIT_PERMISSION,
    MAILMAP_ADMIN_PERMISSION,
    SWH_AMBASSADOR_PERMISSION,
)
from swh.web.tests.helpers import create_django_permission

User = get_user_model()


users: Dict[str, Tuple[str, str, List[str]]] = {
    "user": ("user", "user@example.org", []),
    "user2": ("user2", "user2@example.org", []),
    "ambassador": (
        "ambassador",
        "ambassador@example.org",
        [SWH_AMBASSADOR_PERMISSION],
    ),
    "deposit": ("deposit", "deposit@example.org", [ADMIN_LIST_DEPOSIT_PERMISSION]),
    "add-forge-moderator": (
        "add-forge-moderator",
        "moderator@example.org",
        [ADD_FORGE_MODERATOR_PERMISSION],
    ),
    "mailmap-admin": (
        "mailmap-admin",
        "mailmap-admin@example.org",
        [MAILMAP_ADMIN_PERMISSION],
    ),
}


for username, (password, email, permissions) in users.items():
    if not User.objects.filter(username=username).exists():
        user = User.objects.create_user(username, email, password)
        if permissions:
            for perm_name in permissions:
                permission = create_django_permission(perm_name)
                user.user_permissions.add(permission)

            user.save()
