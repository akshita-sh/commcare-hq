# -*- coding: utf-8 -*-
# Generated by Django 1.11.28 on 2020-03-25 17:11
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('icds_reports', '0184_auto_20200421_2017'),
    ]

    operations = [
        migrations.RunSQL('ALTER TABLE awc_location ADD COLUMN awc_deprecates TEXT'),
        migrations.RunSQL('ALTER TABLE awc_location ADD COLUMN awc_deprecated_at TEXT'),
        migrations.RunSQL('ALTER TABLE awc_location ADD COLUMN supervisor_deprecates TEXT'),
        migrations.RunSQL('ALTER TABLE awc_location ADD COLUMN supervisor_deprecated_at TEXT'),
        migrations.RunSQL('ALTER TABLE awc_location_local ADD COLUMN awc_deprecates TEXT'),
        migrations.RunSQL('ALTER TABLE awc_location_local ADD COLUMN awc_deprecated_at TEXT'),
        migrations.RunSQL('ALTER TABLE awc_location_local ADD COLUMN supervisor_deprecates TEXT'),
        migrations.RunSQL('ALTER TABLE awc_location_local ADD COLUMN supervisor_deprecated_at TEXT'),

    ]
