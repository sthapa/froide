# Generated by Django 3.0.8 on 2020-07-15 16:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("problem", "0004_auto_20200710_1148"),
    ]

    operations = [
        migrations.AddField(
            model_name="problemreport",
            name="escalated",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
