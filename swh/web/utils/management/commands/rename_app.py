# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

"""
A Django Management Command to rename existing Django Applications.

Adapted from https://github.com/odwyersoftware/django-rename-app
"""

import logging

from django.core.management.base import BaseCommand
from django.db import connection

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Renames a Django Application. Usage rename_app [old_app_name] [new_app_name]"
    )

    def add_arguments(self, parser):
        parser.add_argument("old_app_name", nargs=1, type=str)
        parser.add_argument("new_app_name", nargs=1, type=str)

    def handle(self, old_app_name, new_app_name, *args, **options):
        with connection.cursor() as cursor:
            old_app_name = old_app_name[0]
            new_app_name = new_app_name[0]

            try:
                cursor.execute(
                    "SELECT * FROM django_content_type "
                    f"where app_label='{new_app_name}'"
                )
                has_already_been_ran = cursor.fetchone()
                if has_already_been_ran:
                    logger.info(
                        "Renaming app %s to %s has already been done, exiting without "
                        "making any changes",
                        old_app_name,
                        new_app_name,
                    )
                    return None

                cursor.execute(
                    f"UPDATE django_content_type SET app_label='{new_app_name}' "
                    f"WHERE app_label='{old_app_name}'"
                )
                cursor.execute(
                    f"UPDATE django_migrations SET app='{new_app_name}' "
                    f"WHERE app='{old_app_name}'"
                )
            except Exception as e:
                logger.info(
                    "Error while trying to rename app %s to %s: %s",
                    old_app_name,
                    new_app_name,
                    str(e),
                )
                return None
