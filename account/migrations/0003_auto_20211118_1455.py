# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2021-11-18 11:55
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0002_accounttransaction_phone_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='accounttransaction',
            name='response_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
