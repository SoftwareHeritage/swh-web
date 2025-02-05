# Copyright (C) 2021-2024 The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from typing import Dict, List, Tuple

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from swh.web.auth.utils import (
    ADD_FORGE_MODERATOR_PERMISSION,
    ADMIN_LIST_DEPOSIT_PERMISSION,
    ALTER_ADMIN_PERMISSION,
    MAILMAP_ADMIN_PERMISSION,
    SWH_AMBASSADOR_PERMISSION,
    get_or_create_django_permission,
)

User = get_user_model()

# username: (password, email, permissions, groups)
users: Dict[str, Tuple[str, str, List[str], List[str]]] = {
    "user": ("user", "user@example.org", [], []),
    "user2": ("user2", "user2@example.org", [], []),
    "ambassador": (
        "ambassador",
        "ambassador@example.org",
        [SWH_AMBASSADOR_PERMISSION],
        [],
    ),
    "deposit": ("deposit", "deposit@example.org", [ADMIN_LIST_DEPOSIT_PERMISSION], []),
    "add-forge-moderator": (
        "add-forge-moderator",
        "moderator@example.org",
        [ADD_FORGE_MODERATOR_PERMISSION],
        [],
    ),
    "mailmap-admin": (
        "mailmap-admin",
        "mailmap-admin@example.org",
        [MAILMAP_ADMIN_PERMISSION],
        [],
    ),
    "alter-support": (
        "alter-support",
        "alter-support@example.org",
        [ALTER_ADMIN_PERMISSION],
        ["support"],
    ),
    "alter-legal": (
        "alter-legal",
        "alter-legal@example.org",
        [ALTER_ADMIN_PERMISSION],
        ["legal"],
    ),
}


for username, (password, email, permissions, groups) in users.items():
    if not User.objects.filter(username=username).exists():
        user = User.objects.create_user(username, email, password)
        for perm_name in permissions:
            user.user_permissions.add(get_or_create_django_permission(perm_name))
        for group_name in groups:
            user.groups.add(Group.objects.get_or_create(name=group_name)[0])
        if permissions or groups:
            user.save()
