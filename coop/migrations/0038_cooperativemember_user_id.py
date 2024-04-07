# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2024-04-04 06:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coop', '0037_cooperativemember_verified_record'),
    ]

    operations = [
        migrations.AddField(
            model_name='cooperativemember',
            name='user_id',
            field=models.CharField(blank=True, max_length=150, null=True, unique=True),
        ),
    ]