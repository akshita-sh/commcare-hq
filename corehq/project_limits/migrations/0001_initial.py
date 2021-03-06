# -*- coding: utf-8 -*-
# Generated by Django 1.11.26 on 2019-12-07 00:25
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DynamicRateDefinition',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(db_index=True, max_length=512, unique=True)),
                ('per_week', models.FloatField(blank=True, default=None, null=True)),
                ('per_day', models.FloatField(blank=True, default=None, null=True)),
                ('per_hour', models.FloatField(blank=True, default=None, null=True)),
                ('per_minute', models.FloatField(blank=True, default=None, null=True)),
                ('per_second', models.FloatField(blank=True, default=None, null=True)),
            ],
        ),
    ]
