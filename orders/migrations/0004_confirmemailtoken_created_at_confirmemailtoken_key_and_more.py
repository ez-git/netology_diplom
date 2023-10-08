# Generated by Django 4.1.6 on 2023-10-07 23:03

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0003_confirmemailtoken_alter_user_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='confirmemailtoken',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='Создано'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='confirmemailtoken',
            name='key',
            field=models.CharField(db_index=True, default=0, max_length=64, unique=True, verbose_name='Key'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='confirmemailtoken',
            name='user',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, related_name='confirm_email_tokens', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь'),
            preserve_default=False,
        ),
    ]