# Generated by Django 2.2.24 on 2023-02-17 14:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('telegram_bot', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='request',
            name='php_link',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='php link'),
        ),
        migrations.AlterField(
            model_name='request',
            name='php_login',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='php login'),
        ),
        migrations.AlterField(
            model_name='request',
            name='php_password',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='php password'),
        ),
    ]
