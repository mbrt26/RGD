# Generated by Django 4.2.21 on 2025-06-19 17:12

import crm.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0025_remove_tareaventa_prioridad_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tareaventa',
            name='fecha_vencimiento',
            field=models.DateField(default=crm.models.fecha_actual, verbose_name='Fecha de Vencimiento'),
        ),
    ]
