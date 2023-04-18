# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2019-02-20 18:54
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('activity', '0003_remove_trainingsession_training_module'),
    ]

    operations = [
        migrations.AddField(
            model_name='trainingsession',
            name='thematic_area',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='activity.ThematicArea'),
        ),
    ]