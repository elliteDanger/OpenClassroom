# Generated by Django 3.1.3 on 2020-11-12 11:21

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('classroom', '0003_auto_20201112_1032'),
    ]

    operations = [
        migrations.AddField(
            model_name='classroom',
            name='slug',
            field=models.SlugField(default=django.utils.timezone.now, max_length=20, unique_for_date='created_at'),
            preserve_default=False,
        ),
    ]
