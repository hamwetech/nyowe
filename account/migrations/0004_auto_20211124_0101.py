# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2021-11-23 22:01
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0003_auto_20211118_1455'),
    ]

    operations = [
        migrations.AlterField(
            model_name='accounttransaction',
            name='balance_after',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=32, null=True),
        ),
    ]
