# Generated by Django 3.1.8 on 2021-04-19 10:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("foirequest", "0049_auto_20210203_1237"),
    ]

    operations = [
        migrations.AddField(
            model_name="foimessage",
            name="content_rendered_anon",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="foimessage",
            name="content_rendered_auth",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="foimessage",
            name="kind",
            field=models.CharField(
                choices=[
                    ("email", "email"),
                    ("post", "postal mail"),
                    ("fax", "fax"),
                    ("upload", "upload"),
                    ("phone", "phone call"),
                    ("visit", "visit in person"),
                ],
                default="email",
                max_length=10,
            ),
        ),
    ]
