# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-12-20 16:18
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("foirequest", "0012_auto_20171218_1407"),
    ]

    operations = [
        migrations.AddField(
            model_name="requestdraft",
            name="project",
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="foirequest.FoiProject",
            ),
        ),
        migrations.AddField(
            model_name="requestdraft",
            name="request",
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="foirequest.FoiRequest",
            ),
        ),
    ]
