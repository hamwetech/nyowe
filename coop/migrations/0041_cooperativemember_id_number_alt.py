# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2024-04-07 14:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coop', '0040_auto_20240407_0428'),
    ]

    operations = [
        migrations.AddField(
            model_name='cooperativemember',
            name='id_number_alt',
            field=models.CharField(blank=True, max_length=150, null=True, unique=True),
        ),
    ]
