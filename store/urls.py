from django.urls import path
from rest_framework_nested import routers

from . import views

app_name = 'store'

router = routers.DefaultRouter()

router.register('products', views.ProductViewSet, basename='product')
router.register('categories', views.CategoryViewSet, basename='category')


urlpatterns = router.urls
