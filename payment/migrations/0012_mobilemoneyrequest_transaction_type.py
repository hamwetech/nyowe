    # -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2021-11-17 10:34
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payment', '0011_auto_20190308_2108'),
    ]

    operations = [
        migrations.AddField(
            model_name='mobilemoneyrequest',
            name='transaction_type',
            field=models.CharField(blank=True, choices=[('COLLECTION', 'COLLECTION'), ('PAYOUT', 'PAYOUT')], max_length=15),
        ),
    ]