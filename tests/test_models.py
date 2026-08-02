import pytest

from store.models import Comment, Order,CommentStatus,OrderStatus
from tests.factories import CommentFactory, OrderFactory, ProductFactory

pytestmark = pytest.mark.django_db


def test_model_string_representations_are_readable():
    product = ProductFactory(name="Test Product")
    category = product.category
    order = OrderFactory()

    assert str(category) == category.title
    assert str(product) == "Test Product"
    assert str(order) == f"order id: {order.id}"


def test_unpaid_order_manager_returns_only_unpaid_orders():
    unpaid_order = OrderFactory(status=OrderStatus.UNPAID)
    OrderFactory(status=OrderStatus.PAID)

    assert list(Order.unpaid_orders.all()) == [unpaid_order]


def test_approved_comment_managers_return_only_approved_comments():
    approved_comment = CommentFactory(status=CommentStatus.APPROVED)
    CommentFactory(status=CommentStatus.WAITING)

    assert list(Comment.approved.all()) == [approved_comment]
    assert list(Comment.objects.get_approved()) == [approved_comment]
