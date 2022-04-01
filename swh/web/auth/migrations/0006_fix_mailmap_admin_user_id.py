# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import datetime

from django.db import migrations


def _set_first_mailmaps_as_edited_by_admin(apps, schema_editor):
    """First mailmaps in production database have been created by a user
    with "swh.web.mailmap" permission because no "swh.web.admin.mailmap"
    permission existed at the time.

    So change user_id to None to indicate these mailmaps have been created
    by a mailmap administrator.
    """
    UserMailmap = apps.get_model("swh_web_auth", "UserMailmap")

    for mailmap in UserMailmap.objects.filter(
        last_update_date__lte=datetime.datetime(
            2022, 2, 12
        )  # first mailmaps added on 2022/2/11 in production
    ):
        if mailmap.user_id is not None:
            mailmap.user_id = None
            mailmap.save()


class Migration(migrations.Migration):

    dependencies = [
        ("swh_web_auth", "0005_usermailmapevent"),
    ]

    operations = [
        migrations.RunPython(
            _set_first_mailmaps_as_edited_by_admin, migrations.RunPython.noop
        ),
    ]
