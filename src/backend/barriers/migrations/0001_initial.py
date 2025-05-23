# Generated by Django 4.2.20 on 2025-03-29 19:58

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import core.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Barrier",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "address",
                    models.CharField(
                        db_index=True,
                        help_text="Full address of the barrier, validated based on frontend suggestions.",
                        max_length=510,
                    ),
                ),
                (
                    "device_phone",
                    models.CharField(
                        db_index=True,
                        help_text="Enter a phone number in the format +7XXXXXXXXXX.",
                        max_length=20,
                        unique=True,
                        validators=[core.validators.PhoneNumberValidator()],
                    ),
                ),
                (
                    "device_model",
                    models.CharField(
                        choices=[
                            ("RTU5025", "RTU5025"),
                            ("RTU5035", "RTU5035"),
                            ("Telemetrica", "Telemetrica"),
                            ("Elfoc", "Elfoc"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "device_phones_amount",
                    models.PositiveIntegerField(
                        default=1, help_text="Number of registered device phones. Must be at least 1."
                    ),
                ),
                (
                    "device_password",
                    models.CharField(help_text="Device password for managing.", max_length=20, null=True),
                ),
                ("additional_info", models.TextField(blank=True, help_text="Additional details about the barrier.")),
                (
                    "is_public",
                    models.BooleanField(default=True, help_text="Whether the barrier is visible to all users."),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "owner",
                    models.ForeignKey(
                        help_text="User who owns the barrier. Must be an admin.",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="owned_barriers",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "barrier",
            },
        ),
        migrations.CreateModel(
            name="UserBarrier",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "barrier",
                    models.ForeignKey(
                        help_text="Barrier to which the user has access.",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="users_access",
                        to="barriers.barrier",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        help_text="User who has access to the barrier.",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="barriers_access",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "user_barrier",
                "unique_together": {("user", "barrier")},
            },
        ),
    ]
