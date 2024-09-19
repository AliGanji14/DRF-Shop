from django.urls import path
from rest_framework_nested import routers

from . import views

app_name = 'store'

router = routers.DefaultRouter()

router.register('products', views.ProductViewSet, basename='product')
router.register('categories', views.CategoryViewSet, basename='category')
router.register('carts', views.CartViewSet, basename='carts')
router.register('customer', views.CustomerViewSet, basename='customer')


products_router = routers.NestedDefaultRouter(router,'products',lookup='product')
products_router.register('comments', views.CommentViewSet, basename='product-comments')


cart_items_router = routers.NestedDefaultRouter(router,'carts',lookup='cart',)
cart_items_router.register('items', views.CartItemViewSet, basename='cart-item')

urlpatterns = router.urls + products_router.urls + cart_items_router.urls
