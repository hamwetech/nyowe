# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2023-04-20 11:02
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userprofile', '0005_profile_nin'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='nin',
            field=models.CharField(blank=True, max_length=12, null=True),
        ),
    ]
