# Generated by Django 2.2.28 on 2022-08-16 14:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("swh_web_add_forge_now", "0006_request_add_new_fields"),
    ]

    operations = [
        migrations.AlterField(
            model_name="request",
            name="status",
            field=models.TextField(
                choices=[
                    ("PENDING", "Pending"),
                    ("WAITING_FOR_FEEDBACK", "Waiting for feedback"),
                    ("FEEDBACK_TO_HANDLE", "Feedback to handle"),
                    ("ACCEPTED", "Accepted"),
                    ("SCHEDULED", "Scheduled"),
                    ("FIRST_LISTING_DONE", "First listing done"),
                    ("FIRST_ORIGIN_LOADED", "First origin loaded"),
                    ("REJECTED", "Rejected"),
                    ("SUSPENDED", "Suspended"),
                    ("UNSUCCESSFUL", "Unsuccessful"),
                ],
                default="PENDING",
            ),
        ),
        migrations.AlterField(
            model_name="requesthistory",
            name="new_status",
            field=models.TextField(
                choices=[
                    ("PENDING", "Pending"),
                    ("WAITING_FOR_FEEDBACK", "Waiting for feedback"),
                    ("FEEDBACK_TO_HANDLE", "Feedback to handle"),
                    ("ACCEPTED", "Accepted"),
                    ("SCHEDULED", "Scheduled"),
                    ("FIRST_LISTING_DONE", "First listing done"),
                    ("FIRST_ORIGIN_LOADED", "First origin loaded"),
                    ("REJECTED", "Rejected"),
                    ("SUSPENDED", "Suspended"),
                    ("UNSUCCESSFUL", "Unsuccessful"),
                ],
                null=True,
            ),
        ),
    ]
