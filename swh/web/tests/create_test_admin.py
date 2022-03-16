# Copyright (C) 2019-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


from django.contrib.auth import get_user_model

username = "admin"
password = "admin"
email = "admin@swh-web.org"

User = get_user_model()

try:
    user = User.objects.filter(username=username).get()
except User.DoesNotExist:
    user = User.objects.create_superuser(username, email, password)

assert user.is_staff is True
