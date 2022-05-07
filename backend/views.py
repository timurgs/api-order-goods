import random

from django.contrib.auth import authenticate
from django.db import IntegrityError
from requests import get
from rest_framework.authtoken.models import Token
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from yaml import load as load_yaml, Loader
from ujson import loads as load_json
import re
from django_rest_passwordreset.signals import reset_password_token_created

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.http import JsonResponse
from rest_framework.views import APIView
from django.db.models import Q, Sum, F

# Create your views here.
from backend.models import Shop, Category, ProductInfo, Product, Parameter, ProductParameter, Order, OrderItem, \
    ConfirmEmailToken, User, ResetPasswordToken, Contact
from backend.serializers import ProductInfoSerializer, OrderSerializer, OrderItemSerializer, UserSerializer, \
    ContactSerializer, CategorySerializer, ShopSerializer
from backend.signals import new_user_registered, new_order_user, new_order_admin


class RegisterView(APIView):

    def post(self, request, *args, **kwargs):
        if {'last_name', 'first_name', 'email', 'password', 'company', 'position'}.issubset(request.data):
            # проверка пароля на сложность
            pattern = r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$'
            result = re.findall(pattern, request.data['password'])
            if result:
                user_serializer = UserSerializer(data=request.data)
                if user_serializer.is_valid():
                    user = user_serializer.save()
                    user.set_password(request.data['password'])
                    user.save()
                    new_user_registered.send(sender=self.__class__, user_id=user.id)
                    return JsonResponse({'Status': True})
                else:
                    return JsonResponse({'Status': False, 'Errors': user_serializer.errors})
            else:
                return JsonResponse({'Status': False, 'Errors': {'password': 'easy password'}})
        else:
            return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class ConfirmView(APIView):

    def post(self, request, *args, **kwargs):
        # проверяем обязательные аргументы
        if {'email', 'token'}.issubset(request.data):
            token = ConfirmEmailToken.objects.filter(user__email=request.data['email'],
                                                     key=request.data['token']).first()
            if token:
                token.user.is_active = True
                token.user.save()
                token.delete()
                return JsonResponse({'Status': True})
            else:
                return JsonResponse({'Status': False, 'Errors': 'Неправильно указан токен или email'})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class LoginView(APIView):

    def post(self, request, *args, **kwargs):
        if {'email', 'password'}.issubset(request.data):
            user = authenticate(request, username=request.data['email'], password=request.data['password'])
            if user is not None:
                if user.is_active:
                    token, _ = Token.objects.get_or_create(user=user)
                    return JsonResponse({'Status': True, 'Token': token.key})
            else:
                return JsonResponse({'Status': False, 'Errors': 'Не удалось авторизировать'})
        else:
            return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class ResetPasswordRequestTokenView(APIView):

    def post(self, request, *args, **kwargs):
        if {'email'}.issubset(request.data):
            user = User.objects.filter(email=request.data['email']).first()
            if user:
                token, _ = ResetPasswordToken.objects.get_or_create(user_id=user.id)
                reset_password_token_created.send(sender=self.__class__, instance=self, reset_password_token=token)
                return JsonResponse({'Status': True})
            else:
                return JsonResponse({'Status': False, 'Errors': 'Данный email не найден'})
        else:
            return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class ResetPasswordView(APIView):

    def post(self, request, *args, **kwargs):
        if {'email', 'token', 'new_password'}.issubset(request.data):
            token = ResetPasswordToken.objects.filter(user__email=request.data['email'],
                                                      key=request.data['token']).first()
            if token:
                if isinstance(request.data['new_password'], str):
                    pattern = r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$'
                    result = re.findall(pattern, request.data['new_password'])
                    if result:
                        token.user.set_password(request.data['new_password'])
                        token.user.save()
                        token.delete()
                        return JsonResponse({'Status': True})
                    else:
                        return JsonResponse({'Status': False, 'Errors': {'password': 'easy password'}})
                else:
                    return JsonResponse({'Status': False, 'Errors': 'Пароль должен быть строкой'})
            else:
                return JsonResponse({'Status': False, 'Errors': 'Не правильно указан токен или email'})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class AccountData(APIView):
    """
    Класс для работы с данными пользователя
    """

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'})

        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'})

        user_serializer = UserSerializer(request.user, data=request.data, partial=True)
        # проверяем данные
        if user_serializer.is_valid():
            user = user_serializer.save()
        # проверяем данные не входящие в сериализатор
            if 'password' in request.data:
                pattern = r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$'
                result = re.findall(pattern, request.data['password'])
                if result:
                    user.set_password(request.data['password'])
                    user.save()
                    return JsonResponse({'Status': True})
                else:
                    return JsonResponse({'Status': False, 'Errors': 'easy password'})
            else:
                return JsonResponse({'Status': True})

        else:
            return JsonResponse({'Status': False, 'Errors': user_serializer.errors})


class PartnerUpdate(APIView):
    """
    Класс для обновления прайса от поставщика
    """

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=403)

        url = request.data.get('url')
        if url:
            validate_url = URLValidator()
            try:
                validate_url(url)
            except ValidationError as e:
                return JsonResponse({'Status': False, 'Error': str(e)})
            else:
                stream = get(url).content

                data = load_yaml(stream, Loader=Loader)

                shop, _ = Shop.objects.get_or_create(name=data['shop'], user_id=request.user.id)
                for category in data['categories']:
                    category_object, _ = Category.objects.get_or_create(id=category['id'], name=category['name'])
                    category_object.shops.add(shop.id)
                    category_object.save()
                ProductInfo.objects.filter(shop_id=shop.id).delete()
                for item in data['goods']:
                    product, _ = Product.objects.get_or_create(name=item['name'], category_id=item['category'])

                    product_info = ProductInfo.objects.create(product_id=product.id,
                                                              external_id=item['id'],
                                                              model=item['model'],
                                                              price=item['price'],
                                                              price_rrc=item['price_rrc'],
                                                              quantity=item['quantity'],
                                                              shop_id=shop.id)
                    for name, value in item['parameters'].items():
                        parameter_object, _ = Parameter.objects.get_or_create(name=name)
                        ProductParameter.objects.create(product_info_id=product_info.id,
                                                        parameter_id=parameter_object.id,
                                                        value=value)

                return JsonResponse({'Status': True})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class PartnerState(APIView):

    def put(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=403)

        if {'shop_id', 'state'}.issubset(request.data):
            if request.data['shop_id'].isdigit():
                if request.data['state'] in {True, False}:
                    shop = Shop.objects.filter(id=request.data['shop_id'], user_id=request.user.id)
                    if shop:
                        shop.update(state=request.data['state'])
                        return JsonResponse({'Status': True})
                    else:
                        return JsonResponse({'Status': False, 'Errors': 'Такого магазина не существует'})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class PartnerOrders(APIView):

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=403)

        orders = Order.objects.filter(
            ~Q(state='basket'), ordered_items__product_info__shop__user_id=request.user.id).prefetch_related(
            'ordered_items__product_info__product__category',
            'ordered_items__product_info__product_parameters__parameter').select_related('contact').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()

        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)


class ProductInfoView(APIView):
    """
    Класс для поиска товаров
    """

    def get(self, request, *args, **kwargs):
        query = Q(shop__state=True)
        shop_id = request.query_params.get('shop_id')
        category_id = request.query_params.get('category_id')

        if shop_id:
            query = query & Q(shop_id=shop_id)

        if category_id:
            query = query & Q(product__category_id=category_id)

        # фильтруем и отбрасываем дуликаты
        queryset = ProductInfo.objects.filter(
            query).select_related(
            'shop', 'product__category').prefetch_related(
            'product_parameters__parameter').distinct()

        serializer = ProductInfoSerializer(queryset, many=True)

        return Response(serializer.data)


class BasketView(APIView):
    """
    Класс для работы с корзиной пользователя
    """

    # получить корзину
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
        basket = Order.objects.filter(
            user_id=request.user.id, state='basket').prefetch_related(
            'ordered_items__product_info__product__category',
            'ordered_items__product_info__product_parameters__parameter').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()

        serializer = OrderSerializer(basket, many=True)

        return Response(serializer.data)

    # добавить позиции в корзину
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        items_list = request.data.get('items')
        if items_list:
            try:
                items_dict = load_json(items_list)
            except ValueError:
                JsonResponse({'Status': False, 'Errors': 'Неверный формат запроса'})
            else:
                basket, _ = Order.objects.get_or_create(user_id=request.user.id, state='basket')
                objects_created = 0
                for order_item in items_dict:
                    order_item.update({'order': basket.id})
                    serializer = OrderItemSerializer(data=order_item)
                    if serializer.is_valid():
                        try:
                            serializer.save()
                        except IntegrityError as error:
                            return JsonResponse({'Status': False, 'Errors': str(error)})
                        else:
                            objects_created += 1
                    else:
                        JsonResponse({'Status': False, 'Errors': serializer.errors})
                return JsonResponse({'Status': True, 'Создано объектов': objects_created})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})

    # удалить товары из корзины
    def delete(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        items_string = request.data.get('items')
        if items_string:
            items_list = items_string.split(',')
            basket, _ = Order.objects.get_or_create(user_id=request.user.id, state='basket')
            query = Q()
            objects_deleted = False
            for order_item_id in items_list:
                if order_item_id.isdigit():
                    query = query | Q(order_id=basket.id, id=order_item_id)
                    objects_deleted = True
            if objects_deleted:
                deleted_count = OrderItem.objects.filter(query).delete()[0]
                return JsonResponse({'Status': True, 'Удалено объектов': deleted_count})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})

    # редактировать корзину
    def put(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        items_list = request.data.get('items')
        if items_list:
            try:
                items_dict = load_json(items_list)
                print(items_dict)
            except ValueError:
                JsonResponse({'Status': False, 'Errors': 'Неверный формат запроса'})
            else:
                basket, _ = Order.objects.get_or_create(user_id=request.user.id, state='basket')
                objects_updated = 0
                for order_item in items_dict:
                    if type(order_item['id']) == int and type(order_item['quantity']) == int:
                        objects_updated += OrderItem.objects.filter(order_id=basket.id, id=order_item['id']).update(
                            quantity=order_item['quantity'])
                return JsonResponse({'Status': True, 'Обновлено объектов': objects_updated})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class OrderConfirmView(APIView):

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        # проверка данных подтверждения заказа
        if {'id', 'contact_id'}.issubset(request.data):
            if request.data['id'].isdigit():

                order = Order.objects.filter(id=request.data['id'], user_id=request.user.id)
                if order:
                    if order.first().state == 'basket':

                        # присваиваем заказу номер
                        random_num = random.randint(10000, 99999)
                        unique_order = Order.objects.filter(number=random_num)
                        while unique_order:
                            random_num = random.randint(10000, 99999)
                            if not Order.objects.filter(number=random_num):
                                break

                        # новый заказ
                        try:
                            order.update(contact_id=request.data['contact_id'], state='new', number=random_num)
                        except IntegrityError:
                            return JsonResponse({'Status': False, 'Errors': 'Не правильно указаны аргументы'})
                        else:
                            # отправка email
                            new_order_user.send(sender=self.__class__, user_id=request.user.id)
                            ordered_items = OrderItem.objects.filter(order_id=order.first().id)
                            for ordered_item in ordered_items:
                                new_order_admin.send(sender=self.__class__,
                                                     user_id=ordered_item.product_info.shop.user.id)

                            return JsonResponse({'Status': True, 'Номер вашего заказа': random_num})

                    else:
                        return JsonResponse({'Status': False, 'Errors': 'Ваш заказ уже подтвержден'})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class OrdersView(APIView):

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        orders = Order.objects.filter(
            ~Q(state='basket'), user_id=request.user.id).prefetch_related(
            'ordered_items__product_info__product__category',
            'ordered_items__product_info__product_parameters__parameter').select_related('contact').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()

        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)


class ContactsView(APIView):
    """
    Класс для работы с контактами пользователя
    """

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        contacts = Contact.objects.filter(user_id=request.user.id)
        serializer = ContactSerializer(contacts, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if {'city', 'street', 'phone'}.issubset(request.data):
            request.data.update({'user': request.user.id})
            serializer = ContactSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse({'Status': True})
            else:
                return JsonResponse({'Status': False, 'Errors': serializer.errors})
        else:
            return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})

    def delete(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        items_string = request.data.get('items')
        if items_string:
            items_list = items_string.split(',')
            query = Q()
            objects_deleted = False
            for contact_id in items_list:
                if contact_id.isdigit():
                    query = query | Q(id=contact_id)
                    objects_deleted = True

            if objects_deleted:
                deleted_count = Contact.objects.filter(query).delete()[0]
                return JsonResponse({'Status': True, 'Удалено объектов': deleted_count})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})

    def put(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'})

        if 'id' in request.data:
            if request.data['id'].isdigit():
                contact = Contact.objects.filter(id=request.data['id'], user_id=request.user.id).first()
                if contact:
                    serializer = ContactSerializer(contact, data=request.data, partial=True)
                    if serializer.is_valid():
                        serializer.save()
                        return JsonResponse({'Status': True})
                    else:
                        return JsonResponse({'Status': False, 'Errors': serializer.errors})
                else:
                    return JsonResponse({'Status': False, 'Errors': 'Таких контактов не существует'})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class CategoryView(ListAPIView):
    """
    Класс для просмотра категорий
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ShopView(ListAPIView):
    """
    Класс для просмотра списка магазинов
    """
    queryset = Shop.objects.filter(state=True)
    serializer_class = ShopSerializer
