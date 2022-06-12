from rest_framework import serializers

from backend.models import Product, ProductInfo, Contact, User, Category, Shop, ProductParameter, OrderItem, Order


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ('id', 'city', 'street', 'house', 'structure', 'building', 'apartment', 'user', 'phone')
        read_only_fields = ('id',)
        extra_fields = {
            'user': {'write_only': True}
        }


class UserSerializer(serializers.ModelSerializer):
    contacts = ContactSerializer(read_only=True, many=True)

    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'middle_name', 'email', 'company', 'position', 'contacts')
        read_only_field = ('id', 'middle_name')


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name',)
        read_only_fields = ('id',)


class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ('id', 'name', 'state',)
        read_only_fields = ('id',)


class ProductSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()

    class Meta:
        model = Product
        fields = ('name', 'category',)


class ProductParameterSerializer(serializers.ModelSerializer):
    parameter = serializers.StringRelatedField()

    class Meta:
        model = ProductParameter
        fields = ('parameter', 'value')


class ProductInfoSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_parameters = ProductParameterSerializer(read_only=True, many=True)

    class Meta:
        model = ProductInfo
        fields = ('id', 'model', 'product', 'shop', 'quantity', 'price', 'price_rrc', 'product_parameters',)
        read_only_fields = ('id',)


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ('id', 'product_info', 'quantity', 'order')
        read_only_fields = ('id',)
        extra_kwargs = {
            'order': {'write_only': True}
        }


class OrderItemCreateSerializer(OrderItemSerializer):
    product_info = ProductInfoSerializer(read_only=True)


class OrderSerializer(serializers.ModelSerializer):
    ordered_items = OrderItemCreateSerializer(read_only=True, many=True)

    total_sum = serializers.IntegerField()

    class Meta:
        model = Order
        fields = ('id', 'ordered_items', 'state', 'dt', 'total_sum', 'number')
        read_only_fields = ('id',)


# for schema

class RegisterRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'last_name', 'first_name', 'email', 'password', 'company', 'position')


class ConfirmRequestSerializer(serializers.ModelSerializer):
    token = serializers.CharField()

    class Meta:
        model = User
        fields = ('id', 'email', 'token')


class LoginRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'password')


class ResetPasswordTokenRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email')


class ResetPasswordRequestSerializer(serializers.ModelSerializer):
    token = serializers.CharField()
    new_password = serializers.CharField()

    class Meta:
        model = User
        fields = ('id', 'email', 'token', 'new_password')


class PartnerUpdateRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ('id', 'url')


class PartnerStateRequestSerializer(serializers.ModelSerializer):
    shop_id = serializers.CharField()

    class Meta:
        model = Shop
        fields = ('id', 'shop_id', 'state')


class BasketRequestSerializer(serializers.Serializer):
    items = serializers.CharField()


class OrderConfirmRequestSerializer(serializers.ModelSerializer):
    id = serializers.CharField()
    contact_id = serializers.CharField()

    class Meta:
        model = Order
        fields = ('id', 'contact_id')


class ContactsCreateRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ('id', 'city', 'street', 'phone')


class ContactsRemoveRequestSerializer(serializers.Serializer):
    items = serializers.CharField()
