# Generated by Django 4.1.6 on 2023-10-07 23:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0004_confirmemailtoken_created_at_confirmemailtoken_key_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='confirmemailtoken',
            name='key',
            field=models.CharField(db_index=True, max_length=64, unique=True, verbose_name='Ключ'),
        ),
    ]
