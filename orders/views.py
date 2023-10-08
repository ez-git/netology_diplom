from django.db import IntegrityError
from django.db.models import Q, F, Sum
from django.contrib.auth import authenticate

from django.conf.global_settings import EMAIL_HOST_USER
from django.core.mail.message import EmailMultiAlternatives

from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

import yaml
from ujson import loads as load_json

from .models import (
    Shop,
    Category,
    Product,
    Parameter,
    ProductParameter,
    ProductInfo,
    Order,
    OrderItem,
    ConfirmToken,
    Contact
)
from .serializers import (
    UserSerializer,
    ShopSerializer,
    ProductInfoSerializer,
    CategorySerializer,
    OrderSerializer,
    OrderItemSerializer
)


def api_response(success, message, status):
    return Response(
        data={
            'status': success,
            'message': message
        },
        status=status
    )


def send_email(title: str, message: str, email: str, *args, **kwargs) -> str:
    email_list = [email]
    try:
        msg = EmailMultiAlternatives(subject=title, body=message,
                                     from_email=EMAIL_HOST_USER, to=email_list)
        msg.send()
        return f'Title: {msg.subject}, Message:{msg.body}'
    except Exception as exception:
        raise exception


def user_email_confirm(user_id):
    token, created = ConfirmToken.objects.get_or_create(user_id=user_id)
    message = token.key
    email = token.user.email
    send_email('Подтверждение регистрации', message, email)


def order_email_confirm(user_id, order_id):
    token, created = ConfirmToken.objects.get_or_create(user_id=user_id,
                                                        order_id=order_id)
    message = token.key
    email = token.user.email
    send_email('Подтверждение заказа', message, email)


class RegisterAccount(APIView):
    throttle_scope = 'anon'

    def post(self, request, *args, **kwargs):
        if {'email', 'password'}.issubset(request.data):

            user_serializer = UserSerializer(data=request.data)
            if not user_serializer.is_valid():
                return api_response(False,
                                    user_serializer.errors,
                                    status.HTTP_403_FORBIDDEN)
            user = user_serializer.save()
            user.set_password(request.data['password'])
            user.save()

            user_email_confirm(user.id)
            return api_response(True,
                                'Вы получите сообщение на эл. почту для подтвеждения регистрации',
                                status.HTTP_200_OK)
        else:
            return api_response(False,
                                'Переданные параметры указаны неверно',
                                status.HTTP_400_BAD_REQUEST)


class ConfirmAccount(APIView):
    throttle_scope = 'anon'

    def post(self, request, *args, **kwargs):
        # проверяем обязательные аргументы
        if {'email', 'token'}.issubset(request.data):

            token = ConfirmToken.objects.filter(
                user__email=request.data['email'],
                key=request.data['token']).first()
            if token:
                token.user.is_active = True
                token.user.save()
                token.delete()
                return api_response(True,
                                    'Аккаунт подтвержден',
                                    status.HTTP_200_OK)
            else:
                return api_response(False,
                                    'Неверно указаны E-mail или токен',
                                    status.HTTP_400_BAD_REQUEST)
        return api_response(False,
                            'Переданные параметры указаны неверно',
                            status.HTTP_400_BAD_REQUEST)


class LoginAccount(APIView):

    def post(self, request, *args, **kwargs):
        if {'email', 'password'}.issubset(request.data):
            user = authenticate(request,
                                email=request.data['email'],
                                password=request.data['password'])

            if user is not None:
                if user.is_active:
                    token, created = Token.objects.get_or_create(user=user)
                    return api_response(True,
                                        token.key,
                                        status.HTTP_200_OK)
            return api_response(False,
                                'Авторизация не выполнена. Проверьте правильность переданных данных или подтвердите адрес эл. почты.',
                                status.HTTP_403_FORBIDDEN)
        return api_response(False,
                            'Переданные параметры указаны неверно',
                            status.HTTP_400_BAD_REQUEST)


def import_goods(file, user_id):
    file = file['files'].read()
    data = yaml.safe_load(file)
    shop, created = Shop.objects.get_or_create(
        user_id=user_id,
        defaults={'name': data['shop']})

    load_cat = [
        Category(id=category['id'], name=category['name'])
        for category in data['categories']
    ]
    Category.objects.bulk_create(load_cat, ignore_conflicts=True)

    Product.objects.filter(product_infos__shop_id=shop.id).delete()

    load_p = []
    product_id = {}
    load_pi = []
    load_pp = []
    for item in data['goods']:
        product = Product(
            name=item['name'],
            category_id=item['category'])
        load_p.append(product)

        product_id[item['id']] = {}

        product_info = ProductInfo(
            product=product,
            shop_id=shop.id,
            name=item['model'],
            quantity=item['quantity'],
            price=item['price'],
            price_rrc=item['price_rrc'])
        load_pi.append(product_info)

        for name, value in item['parameters'].items():
            parameter, _ = Parameter.objects.get_or_create(name=name)
            product_id[item['id']].update({parameter.id: value})
            product_parameter = ProductParameter(
                product_info=product_info,
                parameter_id=parameter.id,
                value=value)
            load_pp.append(product_parameter)

    Product.objects.bulk_create(load_p)
    ProductInfo.objects.bulk_create(load_pi)
    ProductParameter.objects.bulk_create(load_pp)


class PartnerUpdate(APIView):

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return api_response(False,
                                'Авторизация не выполнена',
                                status.HTTP_403_FORBIDDEN)

        if request.user.type != 'shop':
            return api_response(False,
                                'Доступно только для пользователей магазина',
                                status.HTTP_403_FORBIDDEN)

        file = request.FILES
        if file:
            user_id = request.user.id
            import_goods(file, user_id)

            return api_response(True,
                                'Переданные данные загружены успешно',
                                status.HTTP_200_OK)
        return api_response(False,
                            'Переданные параметры указаны неверно',
                            status.HTTP_400_BAD_REQUEST)


class CategoryView(viewsets.ModelViewSet):
    """
    Класс для просмотра категорий
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    ordering = ('name',)


class ShopView(viewsets.ModelViewSet):
    """
    Класс для просмотра списка магазинов
    """

    queryset = Shop.objects.all()
    serializer_class = ShopSerializer
    ordering = ('name',)


class ProductInfoView(viewsets.ReadOnlyModelViewSet):
    """
    Класс для поиска товаров
    """
    throttle_scope = 'anon'
    serializer_class = ProductInfoSerializer
    ordering = ('product',)

    def get_queryset(self):

        query = Q()  # shop__state=True)
        shop_id = self.request.query_params.get('shop_id')
        category_id = self.request.query_params.get('category_id')

        if shop_id:
            query = query & Q(shop_id=shop_id)

        if category_id:
            query = query & Q(product__category_id=category_id)

        # фильтруем и отбрасываем дуликаты
        queryset = ProductInfo.objects.filter(
            query).select_related(
            'shop', 'product__category').prefetch_related(
            'product_parameters__parameter').distinct()

        return queryset


class BasketView(APIView):
    throttle_scope = 'user'

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return api_response(False,
                                'Авторизация не выполнена',
                                status.HTTP_403_FORBIDDEN)

        basket = Order.objects.filter(
            user_id=request.user.id, status='basket').prefetch_related(
            'ordered_items__product_info__product__category',
            'ordered_items__product_info__product_parameters__parameter').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F(
                'ordered_items__product_info__price'))).distinct()

        serializer = OrderSerializer(basket, many=True)
        return api_response(True,
                            serializer.data,
                            status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return api_response(False,
                                'Авторизация не выполнена',
                                status.HTTP_403_FORBIDDEN)

        items_sting = request.data.get('items')
        if items_sting:
            try:
                items_dict = load_json(items_sting)
            except ValueError:
                return api_response(False,
                                    'Переданные параметры указаны неверно',
                                    status.HTTP_400_BAD_REQUEST)
            else:
                basket, _ = Order.objects.get_or_create(
                    user_id=request.user.id, status='basket')
                objects_created = 0
                for order_item in items_dict:
                    order_item.update({'order': basket.id})
                    serializer = OrderItemSerializer(data=order_item)
                    if serializer.is_valid():
                        try:
                            serializer.save()
                        except IntegrityError as error:
                            return api_response(False,
                                                str(error),
                                                status.HTTP_400_BAD_REQUEST)
                        else:
                            objects_created += 1
                    else:
                        return api_response(False,
                                            serializer.errors,
                                            status.HTTP_400_BAD_REQUEST)
                return api_response(True,
                                    f'Создано объектов: {objects_created}',
                                    status.HTTP_200_OK)
        return api_response(False,
                            'Переданные параметры указаны неверно',
                            status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return api_response(False,
                                'Авторизация не выполнена',
                                status.HTTP_403_FORBIDDEN)

        items_sting = request.data.get('items')
        if items_sting:
            items_list = items_sting.split(',')
            basket, _ = Order.objects.get_or_create(user_id=request.user.id,
                                                    status='basket')
            query = Q()
            objects_deleted = False
            for order_item_id in items_list:
                if order_item_id.isdigit():
                    query = query | Q(order_id=basket.id, id=order_item_id)
                    objects_deleted = True

            if objects_deleted:
                deleted_count = OrderItem.objects.filter(query).delete()[0]
                return api_response(True,
                                    f'Удалено объектов: {deleted_count}',
                                    status.HTTP_200_OK)
        return api_response(False,
                            'Переданные параметры указаны неверно',
                            status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return api_response(False,
                                'Авторизация не выполнена',
                                status.HTTP_403_FORBIDDEN)

        items_sting = request.data.get('items')
        if items_sting:
            try:
                items_dict = load_json(items_sting)
            except ValueError:
                return api_response(False,
                                    'Переданные параметры указаны неверно',
                                    status.HTTP_400_BAD_REQUEST)
            else:
                basket, _ = Order.objects.get_or_create(
                    user_id=request.user.id, status='basket')
                objects_updated = 0
                for order_item in items_dict:
                    if type(order_item['id']) == int and type(
                            order_item['quantity']) == int:
                        objects_updated += OrderItem.objects.filter(
                            order_id=basket.id, id=order_item['id']).update(
                            quantity=order_item['quantity'])

                return api_response(True,
                                    f'Обновлено объектов: {objects_updated}',
                                    status.HTTP_200_OK)
        return api_response(False,
                            'Переданные параметры указаны неверно',
                            status.HTTP_400_BAD_REQUEST)


class OrderView(APIView):
    throttle_scope = 'user'

    def get_address(self, data: dict):
        city = data.get('city'),
        street = data.get('street'),
        house = data.get('house'),
        housing = data.get('housing'),
        building = data.get('building'),
        apartment = data.get('apartment')
        address = ''

        if city:
            if address:
                address = address + f'{city}'
            else:
                address = f'{city}'

        if street:
            if address:
                address = address + f', {street}'
            else:
                address = f'{street}'

        if house:
            if address:
                address = address + f', {house}'
            else:
                address = f'{house}'

        if housing:
            if address:
                address = address + f', {housing}'
            else:
                address = f'{housing}'

        if building:
            if address:
                address = address + f', {building}'
            else:
                address = f'{building}'

        if apartment:
            if address:
                address = address + f', {apartment}'
            else:
                address = f'{apartment}'

        return address

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return api_response(False,
                                'Авторизация не выполнена',
                                status.HTTP_403_FORBIDDEN)

        order_id = self.request.query_params.get('order_id')
        if order_id:
            order = Order.objects.filter(
                id=order_id).exclude(status='basket').select_related(
                'contact').prefetch_related(
                'ordered_items').annotate(
                total_quantity=Sum('ordered_items__quantity'),
                total_sum=Sum('ordered_items__total_amount')).distinct()
        else:
            order = Order.objects.filter(
                user_id=request.user.id).exclude(
                status='basket').select_related('contact').prefetch_related(
                'ordered_items').annotate(
                total_quantity=Sum('ordered_items__quantity'),
                total_sum=Sum('ordered_items__total_amount')).distinct()

        serializer = OrderSerializer(order, many=True)
        return api_response(True,
                            serializer.data,
                            status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):

        if not request.user.is_authenticated:
            return api_response(False,
                                'Авторизация не выполнена',
                                status.HTTP_403_FORBIDDEN)

        data = request.data
        basket_id = data.get('id')

        if basket_id:
            if basket_id.isdigit():
                contact_id = data.get('contact')
                if contact_id:
                    try:
                        order = Order.objects.filter(id=basket_id,
                                                     user_id=request.user.id)
                        order.update(contact_id=contact_id,
                                                     status='new')
                    except IntegrityError as error:
                        return api_response(False,
                                            'Переданные параметры указаны неверно',
                                            status.HTTP_400_BAD_REQUEST)
                else:
                    try:
                        order = Order.objects.filter(id=basket_id,
                                                     user_id=request.user.id)
                        address = self.get_address(data)
                        contact, created = Contact.objects.get_or_create(
                            user_id=request.user.id,
                            type='address',
                            value=address
                        )
                        order.update(contact_id=contact.id,
                                     status='new')
                    except IntegrityError as error:
                        return api_response(False,
                                            'Переданные параметры указаны неверно',
                                            status.HTTP_400_BAD_REQUEST)
                order_email_confirm(request.user.id, basket_id)
                return api_response(True,
                                    'Заказ сформирован и ожидает подтверждения. '
                                    'Подтверждение выслано на эл. почту.',
                                    status.HTTP_200_OK)
        return api_response(False,
                            'Переданные параметры указаны неверно',
                            status.HTTP_400_BAD_REQUEST)


class OrderConfirmView(APIView):

    def post(self, request, *args, **kwargs):

        if not request.user.is_authenticated:
            return api_response(False,
                                'Авторизация не выполнена',
                                status.HTTP_403_FORBIDDEN)

        if {'email', 'token'}.issubset(request.data):

            token = ConfirmToken.objects.filter(
                user__email=request.data['email'],
                key=request.data['token']).first()
            if token:
                order_id = token.order.id
                token.delete()

                order = Order.objects.filter(
                    id=order_id).exclude(status='basket').select_related(
                    'contact').prefetch_related(
                    'ordered_items').annotate(
                    total_quantity=Sum('ordered_items__quantity'),
                    total_sum=Sum('ordered_items__total_amount')).distinct()

                serializer = OrderSerializer(order, many=True)
                return api_response(True,
                             serializer.data,
                             status.HTTP_200_OK)
            else:
                return api_response(False,
                                    'Неверно указаны E-mail или токен',
                                    status.HTTP_400_BAD_REQUEST)
        return api_response(False,
                            'Переданные параметры указаны неверно',
                            status.HTTP_400_BAD_REQUEST)
