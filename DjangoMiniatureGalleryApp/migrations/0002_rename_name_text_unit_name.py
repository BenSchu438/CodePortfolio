# Generated by Django 5.1.5 on 2025-01-22 23:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('MiniatureGallery', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='unit',
            old_name='name_text',
            new_name='name',
        ),
    ]
