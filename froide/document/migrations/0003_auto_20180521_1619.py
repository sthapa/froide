# -*- coding: utf-8 -*-
# Generated by Django 1.11.12 on 2018-05-21 14:19
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("document", "0002_auto_20180521_1613"),
    ]

    operations = [
        migrations.RenameField(
            model_name="page",
            old_name="image_thumbnail",
            new_name="image_small",
        ),
    ]
