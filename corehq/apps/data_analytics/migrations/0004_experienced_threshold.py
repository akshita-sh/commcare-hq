# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data_analytics', '0003_auto_20160205_0927'),
    ]

    operations = [
        migrations.RenameField(
            model_name='maltrow',
            old_name='threshold',
            new_name='use_threshold',
        ),
        migrations.AddField(
            model_name='maltrow',
            name='experience_threshold',
            field=models.PositiveSmallIntegerField(default=3, null=True),
            preserve_default=True,
        ),
    ]
