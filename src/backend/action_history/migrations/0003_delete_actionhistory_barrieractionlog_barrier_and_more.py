# Generated by Django 4.2.20 on 2025-05-07 16:42

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("phones", "0002_barrierphone_access_state"),
        ("barriers", "0004_barrierlimit_global_schedule_phone_limit_and_more"),
        ("action_history", "0002_barrieractionlog_remove_actionhistory_barrier_and_more"),
        ("message_management", "0003_remove_smsmessage_action_smsmessage_log_and_more"),
    ]

    operations = [
        migrations.DeleteModel(
            name="ActionHistory",
        ),
        migrations.AddField(
            model_name="barrieractionlog",
            name="barrier",
            field=models.ForeignKey(
                help_text="Barrier associated with the action",
                on_delete=django.db.models.deletion.PROTECT,
                related_name="action_histories",
                to="barriers.barrier",
            ),
        ),
        migrations.AddField(
            model_name="barrieractionlog",
            name="phone",
            field=models.ForeignKey(
                blank=True,
                help_text="Phone involved in the action, if any",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="action_histories",
                to="phones.barrierphone",
            ),
        ),
        migrations.AddIndex(
            model_name="barrieractionlog",
            index=models.Index(fields=["created_at", "phone", "barrier"], name="barrier_act_created_9e1b2a_idx"),
        ),
    ]
