from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import (
    CreateModelMixin,
    RetrieveModelMixin,
    DestroyModelMixin,
)
from decimal import Decimal
from django.db.models import DecimalField, F, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from django.db.models import Prefetch
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.db.models import Count
from django.db.models import F, Sum, DecimalField, ExpressionWrapper

from .signals import order_created
from .filters import ProductFilter
from .paginations import DefaultPagination
from .permissions import IsAdminOrReadOnly, SendPrivateEmailToCustomerPermission
from .models import (
    Product,
    Category,
    Comment,
    Customer,
    Cart,
    CartItem,
    Order,
    OrderItem,
    CommentStatus,
)
from .serializers import (
    ProductSerializer,
    CategorySerializer,
    CommentSerializer,
    CustomerSerializer,
    CartSerializer,
    CartItemSerializer,
    AddCartItemSerializer,
    UpdateCartItemSerializer,
    OrderSerializer,
    OrderForAdminSerializer,
    OrderCreateSerializer,
    OrderUpdateSerializer,
    OrderItemSerializer,
)


@method_decorator(cache_page(60 * 5), name="list")
@method_decorator(cache_page(60 * 5), name="retrieve")
class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    queryset = Product.objects.select_related("category").all()
    filter_backends = [SearchFilter, OrderingFilter]
    permission_classes = [IsAdminOrReadOnly]
    filterset_class = ProductFilter
    ordering_fields = ["name", "unit_price", "inventory"]
    search_fields = ["name", "category__title"]
    pagination_class = DefaultPagination
    ordering = ["id"]

    def destroy(self, request, *args, **kwargs):
        product = get_object_or_404(
            Product.objects.select_related("category"), pk=kwargs["pk"]
        )
        if product.order_items.count() > 0:
            return Response(
                {
                    "error": "There is some order items including this product."
                    "Please remove them first"
                },
                status=status.HTTP_405_METHOD_NOT_ALLOWED,
            )
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    queryset = Category.objects.annotate(number_of_product=Count("products"))
    permission_classes = [IsAdminOrReadOnly]

    def destroy(self, request, *args, **kwargs):
        category = get_object_or_404(
            Category.objects.prefetch_related("products"),
            pk=kwargs["pk"],
        )
        if category.products.count() > 0:
            return Response(
                {
                    "error": "There are a number of products that subset this category, Please remove them first."
                },
                status=status.HTTP_405_METHOD_NOT_ALLOWED,
            )
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer

    def get_queryset(self):
        product_pk = self.kwargs["product_pk"]
        return Comment.objects.filter(
            product_id=product_pk, status=CommentStatus.APPROVED
        ).all()

    def get_serializer_context(self):
        return {"product_pk": self.kwargs["product_pk"]}


class CartItemViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete"]

    def get_queryset(self):
        cart_pk = self.kwargs["cart_pk"]
        return (
            CartItem.objects.select_related("product")
            .filter(
                cart_id=cart_pk,
            )
            .all()
        )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AddCartItemSerializer
        elif self.request.method == "PATCH":
            return UpdateCartItemSerializer
        return CartItemSerializer

    def get_serializer_context(self):
        return {"cart_pk": self.kwargs["cart_pk"]}


class CartViewSet(
    CreateModelMixin, RetrieveModelMixin, DestroyModelMixin, GenericViewSet
):
    serializer_class = CartSerializer

    queryset = Cart.objects.annotate(
        total_price=Coalesce(
            Sum(
                F("items__quantity") * F("items__product__unit_price"),
                output_field=DecimalField(),
            ),
            Value(Decimal("0")),
        )
    )

    lookup_value_regex = (
        r"[0-9a-fA-F]{8}-?[0-9a-fA-F]{4}-?"
        r"[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?"
        r"[0-9a-fA-F]{12}"
    )


class CustomerViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerSerializer
    queryset = Customer.objects.all()
    permission_classes = [IsAdminUser]

    @action(detail=False, methods=["GET", "PUT"], permission_classes=[IsAuthenticated])
    def me(self, request):
        user_id = request.user.id
        customer = get_object_or_404(Customer, user_id=user_id)
        if request.method == "GET":
            serializer = CustomerSerializer(customer)
            return Response(serializer.data)
        elif request.method == "PUT":
            serializer = CustomerSerializer(customer, data=request.data,partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

    @action(detail=True, permission_classes=[SendPrivateEmailToCustomerPermission])
    def send_private_email(self, request, pk):
        return Response(f"Sending private email to customer {pk=}")


class OrderViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete", "options", "head"]
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method in ["PATCH", "DELETE"]:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user

        queryset = (
            Order.objects.select_related("customer__user")
            .prefetch_related(
                Prefetch(
                    "items",
                    queryset=OrderItem.objects.select_related("product"),
                )
            )
            .annotate(
                total_price=Coalesce(
                    Sum(
                        F("items__quantity") * F("items__product__unit_price"),
                        output_field=DecimalField(),
                    ),
                    Value(Decimal("0")),
                )
            )
        )

        if user.is_staff:
            return queryset

        return queryset.filter(customer__user_id=user.id)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return OrderCreateSerializer

        if self.request.method == "PATCH":
            return OrderUpdateSerializer

        user = self.request.user

        if user.is_staff:
            return OrderForAdminSerializer
        return OrderSerializer

    def get_serializer_context(self):
        return {"user_id": self.request.user.id}

    def create(self, request, *args, **kwargs):
        create_order_serializer = OrderCreateSerializer(
            data=request.data,
            context={"user_id": self.request.user.id},
        )
        create_order_serializer.is_valid(raise_exception=True)
        created_order = create_order_serializer.save()

        order_created.send(self.__class__, order=created_order)

        created_order = self.get_queryset().get(pk=created_order.pk)

        serializer = OrderSerializer(
            created_order,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        with transaction.atomic():
            order = get_object_or_404(
                Order.objects.select_for_update(),
                pk=kwargs["pk"],
            )

            OrderItem.objects.filter(order=order).delete()
            order.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class OrderItemViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "delete", "options", "head"]
    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        order_pk = self.kwargs["order_pk"]
        user = self.request.user

        queryset = (
            OrderItem.objects.select_related("order", "product")
            .filter(order_id=order_pk)
            .all()
        )

        if user.is_staff:
            return queryset

        return queryset.filter(order__customer__user_id=user.id)
