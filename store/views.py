from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Product, Category
from .serializers import ProductSerializer, CategorySerializer


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
