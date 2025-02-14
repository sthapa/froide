# -*- coding: utf-8 -*-
# Generated by Django 1.11.12 on 2018-05-08 11:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("georegion", "0002_auto_20180409_1007"),
    ]

    operations = [
        migrations.AlterField(
            model_name="georegion",
            name="kind",
            field=models.CharField(
                choices=[
                    ("country", "country"),
                    ("state", "state"),
                    ("admin_district", "administrative district"),
                    ("district", "district"),
                    ("admin_cooperation", "administrative cooperation"),
                    ("municipality", "municipality"),
                    ("borough", "borough"),
                    ("zipcode", "zipcode"),
                    ("admin_court_jurisdiction", "administrative court jurisdiction"),
                ],
                max_length=255,
                verbose_name="Kind of Region",
            ),
        ),
    ]
