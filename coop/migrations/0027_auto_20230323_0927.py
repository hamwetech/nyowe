# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2023-03-23 06:27
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coop', '0026_auto_20230323_0916'),
    ]

    operations = [
        migrations.AddField(
            model_name='cooperativemember',
            name='saving_balance',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=32),
        ),
        migrations.AddField(
            model_name='farmergroup',
            name='is_vsla',
            field=models.BooleanField(default=0),
        ),
        migrations.AddField(
            model_name='farmergroup',
            name='saving_balance',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=32),
        ),
    ]
