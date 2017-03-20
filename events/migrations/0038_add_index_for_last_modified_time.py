# -*- coding: utf-8 -*-
# Generated by Django 1.9.11 on 2017-03-20 14:06
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0037_add_n_events_changed_to_keyword_and_place'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='last_modified_time',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name='keyword',
            name='last_modified_time',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name='keywordset',
            name='last_modified_time',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name='organization',
            name='last_modified_time',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name='place',
            name='last_modified_time',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
    ]
