from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),
    path('store/', include('store.urls', namespace='store')),
    path("__debug__/", include("debug_toolbar.urls")),
    path('auth/', include('djoser.urls'),),
    path('auth/', include('djoser.urls.jwt'),),
]
