# -*- coding: utf-8 -*-
# Generated by Django 1.11.28 on 2020-06-12 09:48
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sms', '0039_trumpia_gateway'),
    ]

    operations = [
        migrations.DeleteModel(
            name='KarixBackend',
        )
    ]
