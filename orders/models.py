from django.db import models
from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.core.files.storage import FileSystemStorage
from django_rest_passwordreset.tokens import get_token_generator

storage = FileSystemStorage(location=settings.STORAGE)

STATUS_CHOICES = (
    ('basket', 'Статус корзины'),
    ('new', 'Новый'),
    ('confirmed', 'Подтвержден'),
    ('assembled', 'Собран'),
    ('sent', 'Отправлен'),
    ('delivered', 'Доставлен'),
    ('canceled', 'Отменен'),
)

USER_TYPE_CHOICES = (
    ('shop', 'Магазин'),
    ('buyer', 'Покупатель'),

)

CONTACT_TYPE_CHOICES = (
    ('address', 'Адрес'),
    ('email', 'Почта'),
    ('phone', 'Телефон'),
    ('work_phone', 'Рабочий телефон'),
)


class UserManager(BaseUserManager):
    """
    Миксин для управления пользователями
    """
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Стандартная модель пользователей
    """
    objects = UserManager()
    email = models.EmailField(verbose_name='Email', max_length=40, unique=True)
    company = models.CharField(verbose_name='Компания', max_length=40,
                               blank=True, null=True)
    position = models.CharField(verbose_name='Должность', max_length=40,
                                blank=True, null=True)
    type = models.CharField(verbose_name='Тип пользователя',
                            choices=USER_TYPE_CHOICES, max_length=5,
                            default='shop')

    username = models.CharField(max_length=150, unique=False)
    is_active = models.BooleanField(verbose_name='Email подтвержден',
                                    default=False,
                                    help_text="Designates whether this user "
                                              "should be treated as active."
                                              "Unselect this instead of "
                                              "deleting accounts.")

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = "Список пользователей"
        ordering = ('email',)

class Contact(models.Model):
    user = models.ForeignKey(User,
                             verbose_name='Пользователь',
                             related_name='contacts',
                             blank=True,
                             on_delete=models.CASCADE)

    type = models.CharField(max_length=50,
                            verbose_name='Тип',
                            choices=CONTACT_TYPE_CHOICES)

    value = models.CharField(max_length=150,
                             verbose_name='Значение',
                             blank=True)

    class Meta:
        verbose_name = 'Контактная информация'
        verbose_name_plural = "Контактная информация"

    def __str__(self):
        return f'{self.user.username} (контактная информация)'


class Shop(models.Model):
    name = models.CharField(max_length=50, verbose_name='Название магазина')
    url = models.URLField(verbose_name='Сайт магазина', null=True, blank=True)
    file_name = models.FileField(verbose_name='', null=True, blank=True,
                                 storage=storage)
    user = models.OneToOneField(User, verbose_name='Пользователь', blank=True,
                                null=True,
                                on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Магазин'
        verbose_name_plural = 'Магазины'
        ordering = ('-name',)

    def __str__(self):
        return f'{self.name}'


class Category(models.Model):
    name = models.CharField(max_length=50, verbose_name='Название категории')
    shops = models.ManyToManyField(Shop, verbose_name='Магазины',
                                   related_name='categories', blank=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ('-name',)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название продукта')
    category = models.ForeignKey(Category, verbose_name='Категория',
                                 related_name='products', blank=True,
                                 on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = "Продукты"
        ordering = ('-name',)

    def __str__(self):
        return f'{self.category} - {self.name}'


class ProductInfo(models.Model):
    name = models.CharField(max_length=100, verbose_name='Модель')
    quantity = models.PositiveIntegerField(verbose_name='Количество')
    price = models.PositiveIntegerField(verbose_name='Цена')
    price_rrc = models.PositiveIntegerField(
        verbose_name='Рекомендуемая розничная цена')
    product = models.ForeignKey(Product, verbose_name='Продукт',
                                related_name='product_infos', blank=True,
                                on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, verbose_name='Магазин',
                             related_name='product_infos', blank=True,
                             on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Информация о продукте'
        verbose_name_plural = 'Информационный список о продуктах'
        constraints = [
            models.UniqueConstraint(fields=['product', 'shop'],
                                    name='unique_product_info'),
        ]

    def __str__(self):
        return f'{self.shop.name} - {self.product.name}'


class Parameter(models.Model):
    name = models.CharField(max_length=50, verbose_name='Название параметра')

    class Meta:
        verbose_name = 'Название параметра'
        verbose_name_plural = "Список названий параметров"
        ordering = ('-name',)

    def __str__(self):
        return self.name


class ProductParameter(models.Model):
    product_info = models.ForeignKey(ProductInfo,
                                     verbose_name='Информация о продукте',
                                     blank=True,
                                     related_name='product_parameters',
                                     on_delete=models.CASCADE)
    parameter = models.ForeignKey(Parameter, verbose_name='Параметр',
                                  related_name='product_parameters',
                                  blank=True,
                                  on_delete=models.CASCADE)
    value = models.CharField(max_length=100, verbose_name='Значение')

    class Meta:
        verbose_name = 'Параметр'
        verbose_name_plural = 'Список параметров'
        constraints = [
            models.UniqueConstraint(fields=['product_info', 'parameter'],
                                    name='unique_product_parameter'),
        ]

    def __str__(self):
        return f'{self.product_info.name} - {self.parameter.name}'


class Order(models.Model):
    user = models.ForeignKey(User, verbose_name='Пользователь',
                             related_name='orders', blank=True,
                             on_delete=models.CASCADE)
    contact = models.ForeignKey(Contact, verbose_name='Контакт',
                                related_name='Контакт', blank=True, null=True,
                                on_delete=models.CASCADE)
    dt = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=15, verbose_name='Статус',
                              choices=STATUS_CHOICES)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = "Список заказов"
        ordering = ('-dt',)

    def __str__(self):
        return f'{self.user} - {self.dt}'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, verbose_name='Заказ',
                              related_name='ordered_items', blank=True,
                              on_delete=models.CASCADE)

    product_info = models.ForeignKey(ProductInfo,
                                     verbose_name='Информация о продукте',
                                     related_name='ordered_items',
                                     blank=True, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1,
                                           verbose_name='Количество')
    price = models.PositiveIntegerField(default=0, verbose_name='Цена')
    total_amount = models.PositiveIntegerField(default=0,
                                               verbose_name='Общая стоимость')

    class Meta:
        verbose_name = 'Заказанная позиция'
        verbose_name_plural = "Список заказанных позиций"
        constraints = [
            models.UniqueConstraint(fields=['order_id', 'product_info'],
                                    name='unique_order_item'),
        ]

    def __str__(self):
        return (f'№ {self.order} - {self.product_info.name}. '
                f'Кол-во: {self.quantity}. Сумма {self.total_amount} ')

    def save(self, *args, **kwargs):
        self.price = self.product_info.price
        self.total_amount = self.price * self.quantity
        super(OrderItem, self).save(*args, **kwargs)


class ConfirmToken(models.Model):
    user = models.ForeignKey(
        User,
        related_name='confirm_email_tokens',
        on_delete=models.CASCADE,
        verbose_name="Пользователь"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Создано"
    )

    # Key field, though it is not the primary key of the model
    key = models.CharField(
        verbose_name="Ключ",
        max_length=64,
        db_index=True,
        unique=True
    )

    order = models.ForeignKey(Order, verbose_name='Заказ', blank=True, null=True, default=None, on_delete=models.CASCADE)

    @staticmethod
    def generate_key():
        return get_token_generator().generate_token()

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super(ConfirmToken, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.user}"

    class Meta:
        verbose_name = 'Токен подтверждения Email'
        verbose_name_plural = 'Токены подтверждения Email'
