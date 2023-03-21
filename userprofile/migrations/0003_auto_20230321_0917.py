# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2023-03-21 06:17
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('conf', '0002_systemsettings_mobile_money_payment'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('userprofile', '0002_auto_20200924_0537'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='district',
            field=models.ManyToManyField(blank=True, null=True, to='conf.District'),
        ),
        migrations.AddField(
            model_name='profile',
            name='supervisor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='supervisor', to=settings.AUTH_USER_MODEL),
        ),
    ]
