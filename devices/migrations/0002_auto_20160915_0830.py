# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-09-15 08:30
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('devices', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='device',
            name='mac',
            field=models.CharField(default=1, max_length=17),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='device',
            name='state',
            field=models.BooleanField(default=False),
        ),
    ]