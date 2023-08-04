# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2023-08-04 09:54
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('coop', '0035_collection_farmer_group'),
        ('payment', '0012_mobilemoneyrequest_transaction_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='memberpaymenttransaction',
            name='farmer_group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='coop.FarmerGroup'),
        ),
    ]