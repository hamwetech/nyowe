# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2023-03-23 05:35
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coop', '0024_auto_20230323_0509'),
    ]

    operations = [
        migrations.AddField(
            model_name='savings',
            name='reference',
            field=models.CharField(blank=True, max_length=120, null=True),
        ),
    ]