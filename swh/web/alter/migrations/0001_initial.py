# Copyright (C) 2025  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import uuid

from django.db import migrations, models
import django.db.models.deletion

import swh.web.alter.models


def _create_alter_permission(apps, schema_editor):
    from swh.web.auth.utils import (
        ALTER_ADMIN_PERMISSION,
        get_or_create_django_permission,
    )

    get_or_create_django_permission(ALTER_ADMIN_PERMISSION)


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Alteration",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="created"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="updated"),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            (None, "Filter by status"),
                            ("validating", "Validating"),
                            ("planning", "Planning"),
                            ("executing", "Executing"),
                            ("processed", "Processed"),
                            ("rejected", "Rejected"),
                            ("closed", "Closed"),
                            ("archived", "Archived"),
                        ],
                        default="validating",
                        max_length=20,
                        verbose_name="status",
                    ),
                ),
                (
                    "category",
                    models.CharField(
                        choices=[
                            (None, "Filter by category"),
                            ("copyright", "Copyright / License infringement"),
                            ("pii", "Personal Identifiable Information"),
                            ("legal", "Other legal matters"),
                        ],
                        max_length=20,
                        verbose_name="category",
                    ),
                ),
                ("reasons", models.TextField(verbose_name="reasons")),
                ("expected_outcome", models.TextField(verbose_name="expected outcome")),
                (
                    "email",
                    models.EmailField(max_length=254, verbose_name="requester's email"),
                ),
            ],
            options={
                "db_table": "alteration",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="BlockList",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="created"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="updated"),
                ),
                (
                    "email_or_domain",
                    swh.web.alter.models.LowerCharField(
                        max_length=254,
                        validators=[swh.web.alter.models.validate_email_or_domain],
                        verbose_name="email or domain",
                    ),
                ),
                ("reason", models.TextField(blank=True, verbose_name="reasons")),
            ],
            options={
                "db_table": "block_list",
                "indexes": [
                    models.Index(
                        fields=["email_or_domain"], name="block_list_email_o_123185_idx"
                    )
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("email_or_domain",), name="unique_email_or_domain"
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name="Event",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="created"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="updated"),
                ),
                (
                    "category",
                    models.CharField(
                        choices=[("log", "Event"), ("message", "Message")],
                        max_length=20,
                        verbose_name="category",
                    ),
                ),
                (
                    "author",
                    models.CharField(blank=True, max_length=200, verbose_name="author"),
                ),
                (
                    "recipient",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("requester", "Requester"),
                            ("support", "Support"),
                            ("manager", "Manager"),
                            ("legal", "Legal"),
                            ("technical", "Technical"),
                        ],
                        max_length=20,
                        verbose_name="recipient role",
                    ),
                ),
                ("content", models.TextField(blank=True, verbose_name="content")),
                (
                    "internal",
                    models.BooleanField(
                        default=True,
                        help_text=(
                            "Internal messages are not visible in the Requester "
                            "activity log to avoid unnecessary noise, they must not "
                            "be used for confidential exchanges between team members "
                            "and could be requested by the user."
                        ),
                        verbose_name="internal",
                    ),
                ),
                (
                    "alteration",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="events",
                        to="swh_web_alter.alteration",
                    ),
                ),
            ],
            options={
                "db_table": "event",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="Origin",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="created"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="updated"),
                ),
                ("url", models.URLField(verbose_name="URL")),
                (
                    "outcome",
                    models.CharField(
                        choices=[
                            ("validating", "Validating"),
                            ("rejected", "Rejected"),
                            ("mailmap", "Mailmap"),
                            ("mask", "Permanent mask"),
                            ("takedown", "Takedown"),
                            ("block", "Takedown and block"),
                        ],
                        default="validating",
                        max_length=20,
                        verbose_name="outcome",
                    ),
                ),
                (
                    "reason",
                    models.TextField(
                        blank=True, verbose_name="reason for this outcome"
                    ),
                ),
                (
                    "code_license",
                    models.TextField(blank=True, verbose_name="license found in code"),
                ),
                (
                    "available",
                    models.BooleanField(
                        help_text="Is this URL is still available online ?",
                        null=True,
                        verbose_name="available",
                    ),
                ),
                (
                    "ownership",
                    models.CharField(
                        choices=[
                            ("unknown", "?"),
                            ("owner", "Requester is the owner of the origin"),
                            ("fork", "Fork of an origin owned by the requester"),
                            ("other", "Origin has no direct link with the requester"),
                        ],
                        default="unknown",
                        help_text="Is Requester the owner of this origin or is it a fork ?",
                        max_length=20,
                        verbose_name="owner",
                    ),
                ),
                (
                    "alteration",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="origins",
                        to="swh_web_alter.alteration",
                    ),
                ),
            ],
            options={
                "db_table": "origin",
                "indexes": [models.Index(fields=["url"], name="origin_url_4c8f23_idx")],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("alteration_id", "url"), name="unique_url"
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name="Token",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="created"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="updated"),
                ),
                (
                    "email",
                    models.EmailField(max_length=254, null=True, verbose_name="email"),
                ),
                (
                    "value",
                    models.CharField(
                        default=swh.web.alter.models._default_token_value,
                        max_length=32,
                        verbose_name="value",
                    ),
                ),
                (
                    "expires_at",
                    models.DateTimeField(
                        default=swh.web.alter.models._default_token_expires_at,
                        verbose_name="expiration date",
                    ),
                ),
                (
                    "alteration",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="tokens",
                        to="swh_web_alter.alteration",
                    ),
                ),
            ],
            options={
                "db_table": "token",
                "indexes": [
                    models.Index(fields=["value"], name="token_value_feb983_idx"),
                    models.Index(fields=["email"], name="token_email_715e44_idx"),
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("value",), name="unique_token_value"
                    )
                ],
            },
        ),
        migrations.RunPython(_create_alter_permission, migrations.RunPython.noop),
    ]
