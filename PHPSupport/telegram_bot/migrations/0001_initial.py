# Generated by Django 2.2.24 on 2023-02-17 14:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='name')),
                ('telegram_id', models.CharField(max_length=50, verbose_name='telegram id')),
                ('registration_date', models.DateTimeField(auto_now=True, verbose_name='date of registration')),
                ('subscription_end', models.DateTimeField(verbose_name='end of subscription date')),
            ],
        ),
        migrations.CreateModel(
            name='Subcontractor',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='name')),
                ('telegram_id', models.CharField(max_length=50, verbose_name='telegram id')),
                ('registration_date', models.DateTimeField(auto_now=True, verbose_name='date of registration')),
                ('salary', models.IntegerField(blank=True, null=True, verbose_name='salary')),
                ('is_active', models.BooleanField(blank=True, null=True, verbose_name='is active')),
            ],
        ),
        migrations.CreateModel(
            name='Request',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creation_date', models.DateTimeField(auto_now=True, verbose_name='request creation date')),
                ('title', models.CharField(max_length=50, verbose_name='title')),
                ('description', models.TextField(verbose_name='description')),
                ('price', models.IntegerField(blank=True, null=True, verbose_name='price')),
                ('estimate', models.DateTimeField(blank=True, null=True, verbose_name='estimate')),
                ('php_login', models.CharField(max_length=50, verbose_name='php login')),
                ('php_password', models.CharField(max_length=50, verbose_name='php password')),
                ('php_link', models.CharField(max_length=50, verbose_name='php link')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('open', 'Open'), ('working', 'In work'), ('complete', 'Complete'), ('cancelled', 'Cancelled')], default=('pending', 'Pending'), max_length=10)),
                ('difficulty', models.CharField(choices=[('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')], max_length=10)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='requests', to='telegram_bot.Client', verbose_name='client')),
                ('subcontractor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='requests', to='telegram_bot.Subcontractor', verbose_name='subcontractor')),
            ],
        ),
        migrations.CreateModel(
            name='Clarification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question', models.TextField(verbose_name='question')),
                ('answer', models.TextField(verbose_name='answer')),
                ('creation_date', models.DateTimeField(auto_now=True, verbose_name='request creation date')),
                ('request', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='clarifications', to='telegram_bot.Request', verbose_name='request')),
            ],
        ),
    ]
