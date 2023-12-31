# Generated by Django 4.1.6 on 2023-10-07 22:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0002_shop_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConfirmEmailToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'verbose_name': 'Токен подтверждения Email',
                'verbose_name_plural': 'Токены подтверждения Email',
            },
        ),
        migrations.AlterField(
            model_name='user',
            name='type',
            field=models.CharField(choices=[('shop', 'Магазин'), ('buyer', 'Покупатель')], default='shop', max_length=5, verbose_name='Тип пользователя'),
        ),
    ]
