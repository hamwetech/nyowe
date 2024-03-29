# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2023-04-04 10:30
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('coop', '0029_auto_20230324_0412'),
    ]

    operations = [
        migrations.AddField(
            model_name='cooperative',
            name='fpo_type',
            field=models.CharField(blank=True, choices=[('Cooperative', 'CP'), ('Farmer Group', 'FG'), ('Aggregator', 'AG')], max_length=150, null=True),
        ),
        migrations.AlterField(
            model_name='cooperativemember',
            name='county',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='conf.County'),
        ),
        migrations.AlterField(
            model_name='cooperativemember',
            name='district',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='conf.District'),
        ),
        migrations.AlterField(
            model_name='cooperativemember',
            name='parish',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='conf.Parish'),
        ),
        migrations.AlterField(
            model_name='cooperativemember',
            name='sub_county',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='conf.SubCounty'),
        ),
    ]
