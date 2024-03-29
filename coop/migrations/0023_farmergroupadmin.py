# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2023-03-21 17:12
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('coop', '0022_cooperativemember_chia_trees'),
    ]

    operations = [
        migrations.CreateModel(
            name='FarmerGroupAdmin',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_date', models.DateTimeField(auto_now_add=True)),
                ('update_date', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('farmer_group', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='coop.FarmerGroup')),
                ('user', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, related_name='farmer_group_admin', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'farmer_group_admin',
            },
        ),
    ]
