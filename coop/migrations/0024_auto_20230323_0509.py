# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2023-03-23 02:09
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0002_item_unit'),
        ('conf', '0002_systemsettings_mobile_money_payment'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('coop', '0023_farmergroupadmin'),
    ]

    operations = [
        migrations.CreateModel(
            name='Savings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_date', models.DateField()),
                ('amount', models.DecimalField(decimal_places=2, default=0, max_digits=9)),
                ('balance_after', models.DecimalField(decimal_places=2, default=0, max_digits=9)),
                ('create_date', models.DateTimeField(auto_now_add=True)),
                ('update_date', models.DateTimeField(auto_now=True)),
                ('cooperative', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='coop.Cooperative')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'savings',
            },
        ),
        migrations.AddField(
            model_name='farmergroup',
            name='address',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='farmergroup',
            name='code',
            field=models.CharField(blank=True, max_length=150, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='farmergroup',
            name='contact_person_number',
            field=models.CharField(default=0, max_length=150),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='farmergroup',
            name='contribution_total',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=20),
        ),
        migrations.AddField(
            model_name='farmergroup',
            name='county',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='conf.County'),
        ),
        migrations.AddField(
            model_name='farmergroup',
            name='create_date',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='farmergroup',
            name='created_by',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='farmergroup',
            name='district',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='conf.District'),
        ),
        migrations.AddField(
            model_name='farmergroup',
            name='is_active',
            field=models.BooleanField(default=0),
        ),
        migrations.AddField(
            model_name='farmergroup',
            name='parish',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='conf.Parish'),
        ),
        migrations.AddField(
            model_name='farmergroup',
            name='product',
            field=models.ManyToManyField(blank=True, to='product.Product'),
        ),
        migrations.AddField(
            model_name='farmergroup',
            name='send_message',
            field=models.BooleanField(default=0, help_text="If not set, the cooperative member will not receive SMS's when sent."),
        ),
        migrations.AddField(
            model_name='farmergroup',
            name='sub_county',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='conf.SubCounty'),
        ),
        migrations.AddField(
            model_name='farmergroup',
            name='update_date',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='farmergroup',
            name='village',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='savings',
            name='farmer_group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='coop.FarmerGroup'),
        ),
        migrations.AddField(
            model_name='savings',
            name='member',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='coop.CooperativeMember'),
        ),
    ]