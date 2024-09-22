from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin, DestroyModelMixin
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from django.db.models import Prefetch

from .permissions import IsAdminOrReadOnly, SendPrivateEmailToCustomerPermission
from .models import Product, Category, Comment, Customer, Cart, CartItem, Order, OrderItem
from .serializers import (ProductSerializer,
                          CategorySerializer,
                          CommentSerializer, CustomerSerializer,
                          CartSerializer,
                          CartItemSerializer,
                          AddCartItemSerializer,
                          UpdateCartItemSerializer,
                          OrderSerializer,
                          OrderForAdminSerializer,
                          OrderCreateSerializer,
                          )


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    queryset = Product.objects.select_related('category').all()

    def destroy(self, request, pk):
        product = get_object_or_404(
            Product.objects.select_related('category'),
            pk=pk
        )
        if product.order_items.count() > 0:
            return Response({
                'error':
                    'There is some order items including this product.'
                    'Please remove them first'},
                status=status.HTTP_405_METHOD_NOT_ALLOWED)
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    queryset = Category.objects.prefetch_related('products').all()
    permission_classes = [IsAdminOrReadOnly]

    def destroy(self, request, pk):
        category = get_object_or_404(
            Category.objects.prefetch_related('products'),
            pk=pk,
        )
        if category.products.count() > 0:
            return Response({
                'error':
                'There are a number of products that subset this category, Please remove them first.'
            }, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer

    def get_queryset(self):
        product_pk = self.kwargs['product_pk']
        return Comment.objects.filter(
            product_id=product_pk,
            status=Comment.COMMENT_STATUS_APPROVED
        ).all()

    def get_serializer_context(self):
        return {'product_pk': self.kwargs['product_pk']}


class CartItemViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        cart_pk = self.kwargs['cart_pk']
        return CartItem.objects.select_related('product').filter(
            cart_id=cart_pk,
        ).all()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AddCartItemSerializer
        elif self.request.method == "PATCH":
            return UpdateCartItemSerializer
        return CartItemSerializer

    def get_serializer_context(self):
        return {'cart_pk': self.kwargs['cart_pk']}


class CartViewSet(CreateModelMixin, RetrieveModelMixin, DestroyModelMixin, GenericViewSet):
    serializer_class = CartSerializer
    queryset = Cart.objects.prefetch_related('items__product').all()
    lookup_value_regex = '[0-9a-fA-F]{8}\-?[0-9a-fA-F]{4}\-?[0-9a-fA-F]{4}\-?[0-9a-fA-F]{4}\-?[0-9a-fA-F]{12}'


class CustomerViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerSerializer
    queryset = Customer.objects.all()
    permission_classes = [IsAdminUser]

    @action(detail=False, methods=['GET', 'PUT'], permission_classes=[IsAuthenticated])
    def me(self, request):
        user_id = request.user.id
        customer = Customer.objects.get(user_id=user_id)
        if request.method == 'GET':
            serializer = CustomerSerializer(customer)
            return Response(serializer.data)
        elif request.method == "PUT":
            serializer = CustomerSerializer(customer, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

    @action(detail=True, permission_classes=[SendPrivateEmailToCustomerPermission])
    def send_private_email(self, request, pk):
        return Response(f'Sending private email to customer {pk=}')


class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Order.objects.select_related('customer__user').prefetch_related(
            Prefetch(
                'items',
                queryset=OrderItem.objects.select_related('product')
            )
        ).all()

        if user.is_staff:
            return queryset
        return queryset.filter(customer__user_id=user.id)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OrderCreateSerializer

        if self.request.user.is_staff:
            return OrderForAdminSerializer
        return OrderSerializer

    def get_serializer_context(self):
        return {'user_id': self.request.user.id}

    def create(self, request, *args, **kwargs):
        create_order_serializer = OrderCreateSerializer(
            data=request.data, context={'user_id': self.request.user.id},
        )
        create_order_serializer.is_valid(raise_exception=True)
        created_order = create_order_serializer.save()

        serializer = OrderSerializer(created_order)
        return Response(serializer.data)
