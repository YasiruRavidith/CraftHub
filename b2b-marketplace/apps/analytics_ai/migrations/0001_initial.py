# Generated by Django 5.2.1 on 2025-05-09 08:15

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ReportData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('report_type', models.CharField(choices=[('sales_summary', 'Sales Summary'), ('user_activity', 'User Activity'), ('trend_analysis', 'Trend Analysis')], max_length=50)),
                ('report_parameters', models.JSONField(blank=True, default=dict, help_text='Parameters used to generate the report')),
                ('data', models.JSONField(default=dict, help_text='The actual report data or AI output')),
                ('version', models.PositiveIntegerField(default=1)),
                ('generated_for_user', models.ForeignKey(blank=True, help_text='Report generated for a specific user (e.g., seller dashboard)', null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Report Data Entries',
                'ordering': ['-created_at'],
            },
        ),
    ]
