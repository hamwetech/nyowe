# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2023-09-28 01:53
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('product', '0002_item_unit'),
    ]

    operations = [
        migrations.CreateModel(
            name='OffTaker',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('address', models.CharField(blank=True, max_length=255, null=True)),
                ('create_date', models.DateTimeField(auto_now_add=True)),
                ('update_date', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'off_taker',
            },
        ),
        migrations.CreateModel(
            name='OffTakerSale',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=9)),
                ('quantity', models.DecimalField(decimal_places=2, max_digits=9)),
                ('total_price', models.DecimalField(decimal_places=2, max_digits=9)),
                ('create_date', models.DateTimeField(auto_now_add=True)),
                ('update_date', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('off_taker', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='product.OffTaker')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='product.ProductVariation')),
            ],
            options={
                'db_table': 'off_taker_sale',
            },
        ),
    ]
