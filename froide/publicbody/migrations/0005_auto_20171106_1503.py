# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-06 14:03
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.manager
import froide.publicbody.models


class Migration(migrations.Migration):

    dependencies = [
        ("publicbody", "0004_auto_20161130_0128"),
    ]

    operations = [
        migrations.AlterModelManagers(
            name="publicbody",
            managers=[
                ("non_filtered_objects", django.db.models.manager.Manager()),
                ("objects", froide.publicbody.models.PublicBodyManager()),
            ],
        ),
        migrations.AlterField(
            model_name="foilaw",
            name="max_response_time_unit",
            field=models.CharField(
                blank=True,
                choices=[
                    ("day", "Day(s)"),
                    ("working_day", "Working Day(s)"),
                    ("month_de", "Month(s) (DE)"),
                ],
                default="day",
                max_length=32,
                verbose_name="Unit of Response Time",
            ),
        ),
        migrations.AlterField(
            model_name="publicbody",
            name="other_names",
            field=models.TextField(blank=True, default="", verbose_name="Other names"),
        ),
    ]
