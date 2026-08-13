import pytest
from django.urls import reverse
from rest_framework import status

from store.models import CartItem, Order, OrderStatus
from tests.factories import (
    AdminUserFactory,
    CartFactory,
    CartItemFactory,
    CategoryFactory,
    CustomerFactory,
    OrderFactory,
    OrderItemFactory,
    ProductFactory,
    UserFactory,
)

pytestmark = [pytest.mark.django_db, pytest.mark.api]


@pytest.fixture
def user():
    return UserFactory()


@pytest.fixture
def admin_user():
    return AdminUserFactory()


def test_get_product_list_is_public(api_client):
    product = ProductFactory(name="Public Product")

    response = api_client.get(reverse("store:product-list"))

    assert response.status_code == status.HTTP_200_OK
    results = response.data["results"] if "results" in response.data else response.data
    assert any(item["id"] == product.id for item in results)


def test_anonymous_user_cannot_create_product(api_client):
    category = CategoryFactory()

    response = api_client.post(
        reverse("store:product-list"),
        {
            "title": "Private Product",
            "price": "20.00",
            "category": category.id,
            "inventory": 7,
            "description": "Only admins can create products.",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_admin_can_create_product(admin_client):
    category = CategoryFactory()

    response = admin_client.post(
        reverse("store:product-list"),
        {
            "title": "Admin Product",
            "price": "20.00",
            "category": category.id,
            "inventory": 7,
            "description": "Created by admin.",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["title"] == "Admin Product"


def test_product_validation_error_is_returned_to_admin(admin_client):
    category = CategoryFactory()

    response = admin_client.post(
        reverse("store:product-list"),
        {
            "title": "Bad",
            "price": "20.00",
            "category": category.id,
            "inventory": 7,
            "description": "Invalid title.",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Product title length should be at least 5" in str(response.data)


def test_admin_can_patch_product(admin_client):
    product = ProductFactory(inventory=1)

    response = admin_client.patch(
        reverse("store:product-detail", args=[product.id]),
        {"inventory": 15},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    product.refresh_from_db()
    assert product.inventory == 15


def test_admin_can_delete_product_without_order_items(admin_client):
    product = ProductFactory()

    response = admin_client.delete(reverse("store:product-detail", args=[product.id]))

    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_product_with_order_items_cannot_be_deleted(admin_client):
    order_item = OrderItemFactory()

    response = admin_client.delete(
        reverse("store:product-detail", args=[order_item.product.id])
    )

    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_cart_item_post_patch_and_delete_flow(authenticated_client):
    cart = CartFactory()
    product = ProductFactory()
    list_url = reverse("store:cart-items-list", kwargs={"cart_pk": cart.id})

    post_response = authenticated_client.post(
        list_url,
        {"product": product.id, "quantity": 2},
        format="json",
    )

    assert post_response.status_code == status.HTTP_201_CREATED
    cart_item = CartItem.objects.get(cart=cart, product=product)
    detail_url = reverse(
        "store:cart-items-detail",
        kwargs={"cart_pk": cart.id, "pk": cart_item.id},
    )

    patch_response = authenticated_client.patch(detail_url, {"quantity": 5}, format="json")
    assert patch_response.status_code == status.HTTP_200_OK
    cart_item.refresh_from_db()
    assert cart_item.quantity == 5

    delete_response = authenticated_client.delete(detail_url)
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT
    assert not CartItem.objects.filter(id=cart_item.id).exists()


def test_authenticated_customer_can_create_order(authenticated_client, user):
    CustomerFactory(user=user)
    cart = CartFactory()
    CartItemFactory(cart=cart, quantity=2)

    response = authenticated_client.post(
        reverse("store:order-list"),
        {"cart_id": cart.id},
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert Order.objects.filter(customer__user=user).exists()


def test_anonymous_user_cannot_read_orders(api_client):
    response = api_client.get(reverse("store:order-list"))

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_customer_sees_only_own_orders(authenticated_client, user):
    customer = CustomerFactory(user=user)
    own_order = OrderFactory(customer=customer)
    OrderFactory()

    response = authenticated_client.get(reverse("store:order-list"))

    assert response.status_code == status.HTTP_200_OK
    returned_ids = {item["id"] for item in response.data["results"]}
    assert own_order.id in returned_ids
    assert len(returned_ids) == 1


def test_non_admin_cannot_patch_order(authenticated_client):
    order = OrderFactory()

    response = authenticated_client.patch(
        reverse("store:order-detail", args=[order.id]),
        {"status": OrderStatus.PAID},
        format="json",
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_admin_can_patch_order_status(admin_client):
    order = OrderFactory(status=OrderStatus.UNPAID)

    response = admin_client.patch(
        reverse("store:order-detail", args=[order.id]),
        {"status": OrderStatus.PAID},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    order.refresh_from_db()
    assert order.status == OrderStatus.PAID


def test_admin_can_delete_order_without_items(admin_client):
    order = OrderFactory()

    response = admin_client.delete(reverse("store:order-detail", args=[order.id]))

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Order.objects.filter(id=order.id).exists()
