# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2021-07-28 15:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coop', '0011_cooperativemember_app_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cooperativemember',
            name='phone_number',
            field=models.CharField(blank=True, max_length=16, null=True),
        ),
    ]
