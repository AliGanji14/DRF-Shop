from decimal import Decimal

import pytest

from store.models import Cart, OrderItem
from store.serializers import (
    CategorySerializer,
    OrderCreateSerializer,
    ProductSerializer,
)
from tests.factories import (
    CartFactory,
    CartItemFactory,
    CategoryFactory,
    CustomerFactory,
    UserFactory,
)

pytestmark = pytest.mark.django_db


def test_product_serializer_creates_slug_from_name():
    category = CategoryFactory()
    serializer = ProductSerializer(
        data={
            "title": "Premium Coffee",
            "price": "12.50",
            "category": category.id,
            "inventory": 5,
            "description": "Fresh beans",
        }
    )

    assert serializer.is_valid(), serializer.errors
    product = serializer.save()

    assert product.slug == "premium-coffee"
    assert product.unit_price == Decimal("12.50")


def test_product_serializer_rejects_short_title():
    category = CategoryFactory()
    serializer = ProductSerializer(
        data={
            "title": "Tea",
            "price": "4.00",
            "category": category.id,
            "inventory": 5,
            "description": "Short name",
        }
    )

    assert not serializer.is_valid()
    assert "Product title length should be at least 5" in str(serializer.errors)


def test_category_serializer_rejects_short_title():
    serializer = CategorySerializer(data={"title": "Toy", "description": "Kids"})

    assert not serializer.is_valid()
    assert "Category title length should be at least 5." in str(serializer.errors)


def test_order_create_serializer_moves_cart_items_to_order():
    user = UserFactory()
    CustomerFactory(user=user)
    cart = CartFactory()
    cart_item = CartItemFactory(cart=cart, quantity=3)
    serializer = OrderCreateSerializer(
        data={"cart_id": cart.id},
        context={"user_id": user.id},
    )

    assert serializer.is_valid(), serializer.errors
    order = serializer.save()

    assert order.customer.user == user
    assert OrderItem.objects.filter(
        order=order,
        product=cart_item.product,
        quantity=3,
        unit_price=cart_item.product.unit_price,
    ).exists()
    assert not Cart.objects.filter(id=cart.id).exists()


def test_order_create_serializer_rejects_empty_cart():
    user = UserFactory()
    CustomerFactory(user=user)
    cart = CartFactory()
    serializer = OrderCreateSerializer(
        data={"cart_id": cart.id},
        context={"user_id": user.id},
    )

    assert not serializer.is_valid()
    assert "Your cart is empty" in str(serializer.errors)
