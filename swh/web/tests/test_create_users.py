# Copyright (C) 2021  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


def test_create_users_test_users_exist(db):
    from .create_test_users import User, users

    for username, (_, _, permissions) in users.items():

        user = User.objects.filter(username=username).get()
        assert user is not None

        for permission in permissions:
            assert user.has_perm(permission)
