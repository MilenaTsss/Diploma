# Generated by Django 4.2.20 on 2025-04-04 10:18

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("barriers", "0002_add_userbarrier_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="BarrierLimit",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "user_phone_limit",
                    models.PositiveIntegerField(
                        blank=True, help_text="Maximum number of phone numbers a user can register", null=True
                    ),
                ),
                (
                    "user_temp_phone_limit",
                    models.PositiveIntegerField(
                        blank=True, help_text="Maximum number of temporary phone numbers allowed per user", null=True
                    ),
                ),
                (
                    "global_temp_phone_limit",
                    models.PositiveIntegerField(
                        blank=True, help_text="Maximum number of temporary phone numbers allowed in total", null=True
                    ),
                ),
                (
                    "sms_weekly_limit",
                    models.PositiveIntegerField(
                        blank=True, help_text="Maximum number of SMS messages a user can send per week", null=True
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, help_text="Timestamp when limits were created")),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, help_text="Timestamp when limits were last updated"),
                ),
                (
                    "barrier",
                    models.OneToOneField(
                        help_text="Barrier associated with the limits.",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="limits",
                        to="barriers.barrier",
                    ),
                ),
            ],
            options={
                "db_table": "barrier_limit",
            },
        ),
    ]
