# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2019-05-24 17:00
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coop', '0005_auto_20190319_1512'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cooperativemember',
            name='phone_number',
            field=models.CharField(blank=True, max_length=12, null=True),
        ),
    ]
