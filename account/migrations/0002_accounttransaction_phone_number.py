# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2021-11-18 11:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='accounttransaction',
            name='phone_number',
            field=models.CharField(default=b'', max_length=64),
            preserve_default=False,
        ),
    ]