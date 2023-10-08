# Generated by Django 4.1.6 on 2023-10-08 16:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0010_alter_contact_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='confirmtoken',
            name='order',
            field=models.ForeignKey(blank=True, default=None, on_delete=django.db.models.deletion.CASCADE, to='orders.order', verbose_name='Заказ'),
            preserve_default=False,
        ),
    ]
