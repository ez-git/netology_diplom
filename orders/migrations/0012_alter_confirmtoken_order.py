# Generated by Django 4.1.6 on 2023-10-08 16:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0011_confirmtoken_order'),
    ]

    operations = [
        migrations.AlterField(
            model_name='confirmtoken',
            name='order',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='orders.order', verbose_name='Заказ'),
        ),
    ]