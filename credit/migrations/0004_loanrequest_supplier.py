# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2024-05-08 01:52
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('credit', '0003_auto_20240505_1703'),
    ]

    operations = [
        migrations.AddField(
            model_name='loanrequest',
            name='supplier',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
