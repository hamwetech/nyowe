# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2024-04-11 07:43
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('coop', '0046_registeredsimcards_user_id'),
    ]

    operations = [
        migrations.RenameField(
            model_name='registeredsimcards',
            old_name='date',
            new_name='registration_date',
        ),
    ]