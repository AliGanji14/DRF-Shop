from django.urls import path
from rest_framework_nested import routers

from . import views

app_name = 'store'

router = routers.DefaultRouter()

router.register('products', views.ProductViewSet, basename='product')
router.register('categories', views.CategoryViewSet, basename='category')


products_router = routers.NestedDefaultRouter(
    router,
    'products',
    lookup='product'
)
products_router.register(
    'comments',
    views.CommentViewSet,
    basename='product-comments'
)
urlpatterns = router.urls + products_router.urls
