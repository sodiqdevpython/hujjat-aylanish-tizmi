# Generated by Django 4.2 on 2025-05-13 21:55

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_user_faculty'),
    ]

    operations = [
        migrations.CreateModel(
            name='WorkPlanSummary',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('total_planned', models.DecimalField(decimal_places=1, default=0, max_digits=5)),
                ('total_actual', models.DecimalField(decimal_places=1, default=0, max_digits=5)),
                ('main_plan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.mainworkplan')),
                ('sub_plan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.subworkplan')),
                ('teacher', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('teacher', 'main_plan', 'sub_plan')},
            },
        ),
    ]
