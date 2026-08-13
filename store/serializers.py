from rest_framework import serializers
from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from django.db.models import F
from django.utils.text import slugify
from django.db import transaction
from django.conf import settings
from .models import (
    Product,
    Category,
    Comment,
    Customer,
    Cart,
    CartItem,
    Order,
    OrderItem,
)


class CategorySerializer(serializers.ModelSerializer):
    number_of_product = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = ["id", "title", "description", "number_of_product"]

    def validate(self, data):
        title = data.get("title")

        if title is not None and len(title) < 5:
            raise serializers.ValidationError(
                {"title": "Category title length should be at least 5."}
            )

        return data


class ProductSerializer(serializers.ModelSerializer):
    title = serializers.CharField(max_length=255, source="name")
    price = serializers.DecimalField(
        max_digits=6, decimal_places=2, source="unit_price"
    )
    unit_price_after_tax = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "title",
            "price",
            "unit_price_after_tax",
            "category",
            "inventory",
            "description",
        ]

    def get_unit_price_after_tax(self, product):
        return (product.unit_price * (Decimal("1") + settings.TAX_RATE)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    def validate(self, data):
        name = data.get("name")

        if name is None and self.instance:
            name = self.instance.name

        if len(name) < 5:
            raise serializers.ValidationError(
                {"title": "Product title length should be at least 5."}
            )

        return data

    def create(self, validated_data):
        product = Product(**validated_data)
        product.slug = slugify(product.name)
        product.save()
        return product


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ["id", "name", "body"]

    def create(self, validated_data):
        product_pk = self.context["product_pk"]
        return Comment.objects.create(product_id=product_pk, **validated_data)


class CartProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "unit_price"]


class UpdateCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ["quantity"]


class AddCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ["id", "product", "quantity"]

    def create(self, validated_data):
        cart_pk = self.context["cart_pk"]
        product = validated_data.get("product")
        quantity = validated_data.get("quantity")

        try:
            cart_item = CartItem.objects.get(cart_id=cart_pk, product_id=product.id)
            cart_item.quantity += quantity
            cart_item.save()
        except CartItem.DoesNotExist:
            cart_item = CartItem.objects.create(cart_id=cart_pk, **validated_data)

        self.instance = cart_item
        return cart_item


class CartItemSerializer(serializers.ModelSerializer):
    product = CartProductSerializer(read_only=True)
    item_total = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ["id", "product", "quantity", "item_total"]

    def get_item_total(self, cart_item: CartItem):
        return cart_item.quantity * cart_item.product.unit_price


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = Cart
        fields = ["id", "items", "total_price"]
        read_only_fields = ["id"]


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "user", "phone_number", "birth_date"]
        read_only_fields = ["user"]


class OrderCustomerSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(max_length=255, source="user.first_name")
    last_name = serializers.CharField(max_length=255, source="user.last_name")
    email = serializers.EmailField(source="user.email")

    class Meta:
        model = Customer
        fields = ["id", "first_name", "last_name", "email"]


class OrderItemProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "unit_price"]


class OrderItemSerializer(serializers.ModelSerializer):
    product = OrderItemProductSerializer()

    class Meta:
        model = OrderItem
        fields = ["id", "product", "quantity", "unit_price"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    total_price = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = Order
        fields = ["id", "status", "datetime_created", "items", "total_price"]


class OrderForAdminSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    customer = OrderCustomerSerializer()
    total_price = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = Order
        fields = [
            "id",
            "customer",
            "status",
            "datetime_created",
            "items",
            "total_price",
        ]


class OrderUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["status"]


class OrderCreateSerializer(serializers.Serializer):
    cart_id = serializers.UUIDField()

    def validate_cart_id(self, cart_id):
        if not Cart.objects.filter(id=cart_id).exists():
            raise serializers.ValidationError("There is no cart with this cart id!")
        if CartItem.objects.filter(cart_id=cart_id).count() == 0:
            raise serializers.ValidationError(
                "Your cart is empty. Please add some product to it first!"
            )
        return cart_id

    def save(self, **kwargs):
        with transaction.atomic():
            cart_id = self.validated_data["cart_id"]
            user_id = self.context["user_id"]

            customer = Customer.objects.filter(user_id=user_id).first()

            if customer is None:
                raise serializers.ValidationError("Customer profile does not exist.")

            cart_items = list(
                CartItem.objects.select_related("product")
                .select_for_update()
                .filter(cart_id=cart_id)
            )

            if not cart_items:
                raise serializers.ValidationError("Cart is empty.")

            for cart_item in cart_items:
                product = Product.objects.select_for_update().get(
                    pk=cart_item.product_id
                )

                if product.inventory < cart_item.quantity:
                    raise serializers.ValidationError(
                        f"Not enough inventory for {product.name}"
                    )

            order = Order.objects.create(
                customer=customer,
            )

            order_items = [
                OrderItem(
                    order=order,
                    product=cart_item.product,
                    unit_price=cart_item.product.unit_price,
                    quantity=cart_item.quantity,
                )
                for cart_item in cart_items
            ]

            OrderItem.objects.bulk_create(order_items)

            for cart_item in cart_items:
                Product.objects.filter(pk=cart_item.product_id).update(
                    inventory=F("inventory") - cart_item.quantity
                )

            Cart.objects.filter(pk=cart_id).delete()

            return order


class OrderItemProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "unit_price"]
