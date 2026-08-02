from decimal import Decimal

import factory
from django.contrib.auth import get_user_model
from factory.django import DjangoModelFactory

from store import models


class UserFactory(DjangoModelFactory):
    class Meta:
        model = get_user_model()
        django_get_or_create = ("username",)

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    is_staff = False
    is_superuser = False


class AdminUserFactory(UserFactory):
    username = factory.Sequence(lambda n: f"admin{n}")
    email = factory.Sequence(lambda n: f"admin{n}@example.com")
    is_staff = True
    is_superuser = True


class CategoryFactory(DjangoModelFactory):
    class Meta:
        model = models.Category

    title = factory.Sequence(lambda n: f"Category {n}")
    description = factory.Faker("sentence")


class ProductFactory(DjangoModelFactory):
    class Meta:
        model = models.Product

    category = factory.SubFactory(CategoryFactory)
    name = factory.Sequence(lambda n: f"Product {n}")
    slug = factory.Sequence(lambda n: f"product-{n}")
    description = factory.Faker("paragraph")
    unit_price = Decimal("10.00")
    inventory = 10


class CustomerFactory(DjangoModelFactory):
    class Meta:
        model = models.Customer
        django_get_or_create = ("user",)

    user = factory.SubFactory(UserFactory)
    phone_number = factory.Sequence(lambda n: f"555-010{n}")
    birth_date = "1990-01-01"


class CartFactory(DjangoModelFactory):
    class Meta:
        model = models.Cart


class CartItemFactory(DjangoModelFactory):
    class Meta:
        model = models.CartItem

    cart = factory.SubFactory(CartFactory)
    product = factory.SubFactory(ProductFactory)
    quantity = 2


class OrderFactory(DjangoModelFactory):
    class Meta:
        model = models.Order

    customer = factory.SubFactory(CustomerFactory)
    status = models.OrderStatus.UNPAID


class OrderItemFactory(DjangoModelFactory):
    class Meta:
        model = models.OrderItem

    order = factory.SubFactory(OrderFactory)
    product = factory.SubFactory(ProductFactory)
    quantity = 2
    unit_price = Decimal("10.00")


class CommentFactory(DjangoModelFactory):
    class Meta:
        model = models.Comment

    product = factory.SubFactory(ProductFactory)
    name = factory.Faker("name")
    body = factory.Faker("paragraph")
    status = models.CommentStatus.APPROVED
