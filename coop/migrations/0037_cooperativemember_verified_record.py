# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2024-03-03 18:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coop', '0036_auto_20231119_0638'),
    ]

    operations = [
        migrations.AddField(
            model_name='cooperativemember',
            name='verified_record',
            field=models.BooleanField(default=False),
        ),
    ]
