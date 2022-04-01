# Generated by Django 2.2.24 on 2022-03-21 15:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("swh_web_add_forge_now", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="request",
            name="forge_contact_comment",
            field=models.TextField(
                help_text="Where did you find this contact information (url, ...)",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="requesthistory",
            name="actor_role",
            field=models.TextField(
                choices=[
                    ("MODERATOR", "moderator"),
                    ("SUBMITTER", "submitter"),
                    ("FORGE_ADMIN", "forge admin"),
                ]
            ),
        ),
    ]
