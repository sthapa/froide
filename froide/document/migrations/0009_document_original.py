# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-08-07 13:20
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("document", "0008_auto_20180807_1452"),
        ("foirequest", "0018_requestdraft_law_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="document",
            name="original",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="original_document",
                to="foirequest.FoiAttachment",
            ),
        ),
    ]
