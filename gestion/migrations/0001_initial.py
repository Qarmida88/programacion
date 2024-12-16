# Generated by Django 4.1 on 2024-12-01 19:48

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Producto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=255)),
                ('precio_unitario', models.DecimalField(decimal_places=2, max_digits=10)),
                ('fecha_vencimiento', models.DateField()),
                ('stock', models.PositiveIntegerField()),
                ('categoria', models.CharField(max_length=100)),
            ],
        ),
    ]
