# Generated by Django 4.2 on 2025-05-14 09:24

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0011_document_requirement'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='quantity_actual',
            field=models.DecimalField(decimal_places=1, default=1, max_digits=3, validators=[django.core.validators.MinValueValidator(0.1), django.core.validators.MaxValueValidator(5.0)], verbose_name='Amalda miqdor'),
        ),
    ]
