# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-04-22 17:18
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import migrations

from corehq.sql_db.operations import HqRunSQL
from corehq.util.django_migrations import add_if_not_exists_raw


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0005_automatic_downgrade_adjustment_method'),
    ]

    operations = [
        HqRunSQL(
            add_if_not_exists_raw(
                """
                CREATE UNIQUE INDEX accounting_subscription_active_subscriber
                ON accounting_subscription(subscriber_id) WHERE (is_active = TRUE and is_hidden_to_ops = FALSE)
                """, name='accounting_subscription_active_subscriber'
            ),
            reverse_sql=
            """
            DROP INDEX IF EXISTS accounting_subscription_active_subscriber;
            """,
        )
    ]
