# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2019-03-19 12:12
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coop', '0004_cooperativemember_county'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cooperativemember',
            name='cotton_acreage',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='cooperativemember',
            name='soghum_acreage',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='cooperativemember',
            name='soya_beans_acreage',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=10, null=True),
        ),
    ]