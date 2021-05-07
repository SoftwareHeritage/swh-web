# Copyright (C) 2021  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


from django.contrib.auth import get_user_model

User = get_user_model()

username = "user"
password = "user"
email = "user@swh-web.org"

if not User.objects.filter(username=username).exists():
    User.objects.create_user(username, email, password)
